use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{LazyLock, Mutex, PoisonError};

use pyo3::exceptions::{PyAttributeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::pyclass::CompareOp;
use pyo3::sync::{MutexExt, PyOnceLock};
use pyo3::types::{PyString, PyTuple, PyType};

struct KindData {
    id: usize,
    name: String,
    object: PyOnceLock<Py<Kind>>,
    operators: [PyOnceLock<Py<PyAny>>; Operator::COUNT],
    family: Option<Py<KindFamily>>,
    params: Box<[KindRef]>,
    signature: Option<Signature>,
    literals: Box<[Py<PyType>]>,
}

struct Signature {
    inputs: Box<[KindRef]>,
    run: Option<usize>,
    output: KindRef,
}

impl Signature {
    fn fits(&self, given: usize) -> bool {
        match self.run {
            Some(_) => given + 1 >= self.inputs.len(),
            None => given == self.inputs.len(),
        }
    }

    fn positions(&self, slot: usize, given: usize) -> std::ops::Range<usize> {
        match self.run {
            Some(run) if slot >= run => {
                let taken = given + 1 - self.inputs.len();
                if slot == run {
                    run..run + taken
                } else {
                    slot + taken - 1..slot + taken
                }
            }
            _ => slot..slot + 1,
        }
    }
}

type KindRef = &'static KindData;

fn same_kind(a: KindRef, b: KindRef) -> bool {
    std::ptr::eq(a, b)
}

static KIND_COUNT: AtomicUsize = AtomicUsize::new(0);

/// Make the record for a new kind. It is never freed.
fn new_kind_data(
    name: String,
    family: Option<Py<KindFamily>>,
    params: Box<[KindRef]>,
    signature: Option<Signature>,
    literals: Box<[Py<PyType>]>,
) -> KindRef {
    Box::leak(Box::new(KindData {
        id: KIND_COUNT.fetch_add(1, Ordering::Relaxed),
        name,
        object: PyOnceLock::new(),
        operators: [const { PyOnceLock::new() }; Operator::COUNT],
        family,
        params,
        signature,
        literals,
    }))
}

impl KindData {
    fn accepts(&self, value: &Bound<'_, PyAny>) -> bool {
        let value_type = value.get_type();
        self.literals.iter().any(|t| value_type.is(t.bind(value.py())))
    }
}

fn literal<'py>(kind: KindRef, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, Expr>> {
    Bound::new(value.py(), Expr { kind, form: Form::Literal { value: value.clone().unbind() } })
}

fn kind_object(py: Python<'_>, data: KindRef) -> PyResult<Py<Kind>> {
    let object = data.object.get_or_try_init(py, || Py::new(py, Kind { data }))?;
    Ok(object.clone_ref(py))
}

fn kind_tuple<'py>(py: Python<'py>, kinds: &[KindRef]) -> PyResult<Bound<'py, PyTuple>> {
    let mut objects = Vec::with_capacity(kinds.len());
    for &kind in kinds {
        objects.push(kind_object(py, kind)?);
    }
    PyTuple::new(py, objects)
}

#[pyclass(frozen, module = "nary")]
struct Kind {
    data: KindRef,
}

#[pymethods]
impl Kind {
    #[pyo3(signature = (head, *extra))]
    fn __call__<'py>(
        &self,
        head: &Bound<'py, PyAny>,
        extra: &Bound<'py, PyTuple>,
    ) -> PyResult<Bound<'py, Expr>> {
        let py = head.py();
        if !extra.is_empty() {
            return Err(PyTypeError::new_err(format!(
                "{} takes 1 argument, the name of a leaf, got {}; \
                 a node is built by calling a function",
                self.data.name,
                extra.len() + 1
            )));
        }
        if let Ok(name) = head.cast::<PyString>() {
            return Bound::new(
                py,
                Expr { kind: self.data, form: Form::Symbol { name: name.clone().unbind() } },
            );
        }
        if self.data.accepts(head) {
            return literal(self.data, head);
        }
        let types = literal_type_names(py, &self.data.literals)?;
        let (expected, note) = if types.is_empty() {
            ("a name (a str)".to_string(), "; it accepts no literals")
        } else {
            (format!("a name (a str) or a literal of type {}", types.join(" or ")), "")
        };
        Err(PyTypeError::new_err(format!(
            "{} takes {}, got {}: {}{}",
            self.data.name,
            expected,
            head.get_type().name()?,
            describe(head),
            note
        )))
    }

    #[getter]
    fn name(&self) -> &str {
        &self.data.name
    }

    fn __repr__(&self) -> &str {
        &self.data.name
    }

    #[getter]
    fn family(&self, py: Python<'_>) -> Option<Py<KindFamily>> {
        self.data.family.as_ref().map(|family| family.clone_ref(py))
    }

    #[getter]
    fn params<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        kind_tuple(py, &self.data.params)
    }

    #[getter]
    fn inputs<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyTuple>>> {
        let Some(sig) = &self.data.signature else {
            return Ok(None);
        };
        let mut inputs = Vec::with_capacity(sig.inputs.len());
        for (slot, &kind) in sig.inputs.iter().enumerate() {
            let mut input = kind_object(py, kind)?.into_any();
            if sig.run == Some(slot) {
                input = Py::new(py, Many { of: input })?.into_any();
            }
            inputs.push(input);
        }
        PyTuple::new(py, inputs).map(Some)
    }

    #[getter]
    fn output(&self, py: Python<'_>) -> PyResult<Option<Py<Kind>>> {
        self.data.signature.as_ref().map(|sig| kind_object(py, sig.output)).transpose()
    }

    #[getter]
    fn literals<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        PyTuple::new(py, self.data.literals.iter().map(|t| t.clone_ref(py)))
    }
}

fn literal_type_names(py: Python<'_>, types: &[Py<PyType>]) -> PyResult<Vec<String>> {
    types.iter().map(|t| Ok(t.bind(py).name()?.to_string())).collect()
}

fn literal_types(name: &str, literals: Option<&Bound<'_, PyAny>>) -> PyResult<Box<[Py<PyType>]>> {
    let Some(literals) = literals.filter(|literals| !literals.is_none()) else {
        return Ok(Box::new([]));
    };
    let items: Vec<Bound<'_, PyAny>> = match literals.cast::<PyTuple>() {
        Ok(tuple) => tuple.iter().collect(),
        Err(_) => vec![literals.clone()],
    };
    let mut types = Vec::with_capacity(items.len());
    for item in items {
        let Ok(t) = item.cast::<PyType>() else {
            return Err(PyTypeError::new_err(format!(
                "{name}: literals must be a type or a tuple of types, got {}",
                describe(literals)
            )));
        };
        if t.is_subclass_of::<PyString>()? {
            return Err(PyValueError::new_err(format!(
                "{name}: str cannot be a literal type, since a str names a symbol"
            )));
        }
        types.push(t.clone().unbind());
    }
    Ok(types.into_boxed_slice())
}

#[pyfunction]
#[pyo3(signature = (name, literals=None))]
fn declare_kind(
    py: Python<'_>,
    name: String,
    literals: Option<&Bound<'_, PyAny>>,
) -> PyResult<Py<Kind>> {
    let literals = literal_types(&name, literals)?;
    kind_object(py, new_kind_data(name, None, Box::new([]), None, literals))
}

static FUNCTION_KINDS: LazyLock<Mutex<HashMap<Box<[usize]>, KindRef>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

fn function_kind_name(inputs: &[KindRef], run: Option<usize>, output: KindRef) -> String {
    let names: Vec<String> = inputs
        .iter()
        .enumerate()
        .map(|(slot, kind)| match run {
            Some(run) if run == slot => format!("Many({})", kind.name),
            _ => kind.name.clone(),
        })
        .collect();
    let inputs = match names.len() {
        1 => format!("({},)", names[0]),
        _ => format!("({})", names.join(", ")),
    };
    format!("FunctionKind({inputs}, {})", output.name)
}

fn function_kind(
    py: Python<'_>,
    inputs: &[KindRef],
    run: Option<usize>,
    output: KindRef,
) -> PyResult<KindRef> {
    let mut key = Vec::with_capacity(inputs.len() + 2);
    key.push(output.id);
    key.push(run.unwrap_or(usize::MAX));
    key.extend(inputs.iter().map(|kind| kind.id));
    let data = {
        // No Python code runs while the table is locked, so the lock cannot
        // be asked for again by this thread before it is released.
        let mut table = FUNCTION_KINDS
            .lock_py_attached(py)
            .unwrap_or_else(PoisonError::into_inner);
        match table.get(key.as_slice()) {
            Some(&data) => data,
            None => {
                let data = new_kind_data(
                    function_kind_name(inputs, run, output),
                    None,
                    Box::new([]),
                    Some(Signature { inputs: inputs.into(), run, output }),
                    Box::new([]),
                );
                table.insert(key.into_boxed_slice(), data);
                data
            }
        }
    };
    // Made outside the lock, since allocating a Python object can run
    // Python code.
    data.object.get_or_try_init(py, || Py::new(py, Kind { data }))?;
    Ok(data)
}

#[pyfunction(name = "FunctionKind")]
fn function_kind_py(
    py: Python<'_>,
    inputs: &Bound<'_, PyAny>,
    output: &Bound<'_, PyAny>,
) -> PyResult<Py<Kind>> {
    let Ok(inputs) = inputs.cast_exact::<PyTuple>() else {
        return Err(PyTypeError::new_err(format!(
            "FunctionKind: inputs must be a tuple of kinds, got {}",
            describe(inputs)
        )));
    };
    let mut kinds = Vec::with_capacity(inputs.len());
    let mut run = None;
    for (slot, input) in inputs.iter().enumerate() {
        match input.cast_exact::<Many>() {
            Ok(many) => {
                if run.replace(slot).is_some() {
                    return Err(PyTypeError::new_err(format!(
                        "FunctionKind: at most one input can be Many, got {}",
                        describe(inputs)
                    )));
                }
                kinds.push(expect_kind(many.get().of.bind(py))?);
            }
            Err(_) => kinds.push(expect_kind(&input)?),
        }
    }
    let output = expect_kind(output)?;
    kind_object(py, function_kind(py, &kinds, run, output)?)
}

#[pyclass(frozen, module = "nary")]
struct KindFamily {
    name: String,
    params: Option<usize>,
    instances: Mutex<HashMap<Box<[usize]>, KindRef>>,
}

fn count(n: usize, what: &str) -> String {
    if n == 1 {
        format!("1 {what}")
    } else {
        format!("{n} {what}s")
    }
}

#[pymethods]
impl KindFamily {
    #[pyo3(signature = (*params))]
    fn __call__(slf: &Bound<'_, Self>, params: &Bound<'_, PyTuple>) -> PyResult<Py<Kind>> {
        let py = slf.py();
        let family = slf.get();
        let given = params.len();
        let expected = match family.params {
            Some(n) if given != n => Some(count(n, "parameter")),
            None if given == 0 => Some(format!("at least {}", count(1, "parameter"))),
            _ => None,
        };
        if let Some(expected) = expected {
            return Err(PyTypeError::new_err(format!(
                "{} takes {}, got {}",
                family.name, expected, given
            )));
        }
        let mut kinds = Vec::with_capacity(given);
        for param in params.iter() {
            kinds.push(expect_kind(&param)?);
        }
        let key: Box<[usize]> = kinds.iter().map(|kind| kind.id).collect();
        let data = {
            // No Python code runs while the table is locked, so the lock
            // cannot be asked for again by this thread before it is released.
            let mut instances = family
                .instances
                .lock_py_attached(py)
                .unwrap_or_else(PoisonError::into_inner);
            *instances.entry(key).or_insert_with(|| {
                let names: Vec<&str> = kinds.iter().map(|kind| kind.name.as_str()).collect();
                new_kind_data(
                    format!("{}({})", family.name, names.join(", ")),
                    Some(slf.clone().unbind()),
                    kinds.into_boxed_slice(),
                    None,
                    Box::new([]),
                )
            })
        };
        kind_object(py, data)
    }

    #[getter]
    fn name(&self) -> &str {
        &self.name
    }

    #[getter]
    fn params(&self) -> Option<usize> {
        self.params
    }

    fn __repr__(&self) -> String {
        format!("<kind family {}>", self.name)
    }
}

#[pyfunction]
#[pyo3(signature = (name, params=None))]
fn declare_kind_family(name: String, params: Option<isize>) -> PyResult<KindFamily> {
    let params = match params {
        None => None,
        Some(n) if n >= 1 => Some(n as usize),
        Some(n) => {
            return Err(PyValueError::new_err(format!(
                "{name}: params must be at least 1, got {n}"
            )));
        }
    };
    Ok(KindFamily { name, params, instances: Mutex::new(HashMap::new()) })
}

fn describe(obj: &Bound<'_, PyAny>) -> String {
    match obj.repr() {
        Ok(text) => text.to_string(),
        Err(_) => "an object whose repr failed".to_string(),
    }
}

fn expect_kind(obj: &Bound<'_, PyAny>) -> PyResult<KindRef> {
    match obj.cast_exact::<Kind>() {
        Ok(kind) => Ok(kind.get().data),
        Err(_) => Err(PyTypeError::new_err(format!(
            "expected a kind, got {}",
            describe(obj)
        ))),
    }
}

fn is_symbol(obj: &Bound<'_, PyAny>) -> bool {
    obj.cast_exact::<Expr>().is_ok_and(|expr| expr.get().is_symbol())
}

#[pyclass(frozen, module = "nary")]
struct Many {
    #[pyo3(get)]
    of: Py<PyAny>,
}

#[pymethods]
impl Many {
    #[new]
    fn new(of: &Bound<'_, PyAny>) -> PyResult<Self> {
        let kind = of.cast_exact::<Kind>().is_ok();
        if kind || is_symbol(of) || of.cast_exact::<BoundVariable>().is_ok() {
            return Ok(Many { of: of.clone().unbind() });
        }
        Err(PyTypeError::new_err(format!(
            "Many takes a kind or a symbol, got {}",
            describe(of)
        )))
    }

    fn __eq__(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        match other.cast_exact::<Many>() {
            Ok(other) => self.of.bind(py).eq(other.get().of.bind(py)),
            Err(_) => Ok(false),
        }
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        self.of.bind(py).hash()
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!("Many({})", self.of.bind(py).repr()?))
    }
}

#[pyclass(frozen, module = "nary", name = "Bound")]
struct BoundVariable {
    #[pyo3(get)]
    of: Py<PyAny>,
}

#[pymethods]
impl BoundVariable {
    #[new]
    fn new(of: &Bound<'_, PyAny>) -> PyResult<Self> {
        if is_symbol(of) {
            return Ok(BoundVariable { of: of.clone().unbind() });
        }
        Err(PyTypeError::new_err(format!("Bound takes a symbol, got {}", describe(of))))
    }

    fn __eq__(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        match other.cast_exact::<BoundVariable>() {
            Ok(other) => self.of.bind(py).eq(other.get().of.bind(py)),
            Err(_) => Ok(false),
        }
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        self.of.bind(py).hash()
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!("Bound({})", self.of.bind(py).repr()?))
    }
}

#[pyclass(frozen, module = "nary")]
struct Expr {
    kind: KindRef,
    form: Form,
}

enum Form {
    Symbol { name: Py<PyString> },
    Literal { value: Py<PyAny> },
    Declared {
        name: Py<PyString>,
        names: Option<Py<PyTuple>>,
        bound: Option<Box<[bool]>>,
    },
    Apply { head: Py<Expr>, args: Py<PyTuple> },
}

impl Expr {
    fn plain_name(&self) -> Option<&Py<PyString>> {
        match &self.form {
            Form::Symbol { name } | Form::Declared { name, .. } => Some(name),
            _ => None,
        }
    }

    fn label(&self, py: Python<'_>) -> PyResult<String> {
        match self.plain_name() {
            Some(name) => Ok(name.bind(py).to_string()),
            None => self.__repr__(py),
        }
    }
}

fn structural_eq(py: Python<'_>, a: &Expr, b: &Expr) -> PyResult<bool> {
    if std::ptr::eq(a, b) {
        return Ok(true);
    }
    if !same_kind(a.kind, b.kind) {
        return Ok(false);
    }
    Ok(match (&a.form, &b.form) {
        (Form::Symbol { name: x }, Form::Symbol { name: y }) => {
            x.bind(py).as_any().eq(y.bind(py))?
        }
        (Form::Literal { value: x }, Form::Literal { value: y }) => {
            let (x, y) = (x.bind(py), y.bind(py));
            x.get_type().is(&y.get_type()) && x.eq(y)?
        }
        (Form::Apply { head: h1, args: a1 }, Form::Apply { head: h2, args: a2 }) => {
            structural_eq(py, h1.get(), h2.get())? && a1.bind(py).as_any().eq(a2.bind(py))?
        }
        _ => false,
    })
}

fn compare(slf: &Expr, other: &Bound<'_, PyAny>, op: CompareOp) -> PyResult<Py<PyAny>> {
    let py = other.py();
    let equal = match other.cast_exact::<Expr>() {
        Ok(other) => structural_eq(py, slf, other.get())?,
        Err(_) => return Ok(py.NotImplemented()),
    };
    Ok(match op {
        CompareOp::Eq => equal.into_pyobject(py)?.to_owned().into_any().unbind(),
        CompareOp::Ne => (!equal).into_pyobject(py)?.to_owned().into_any().unbind(),
        _ => py.NotImplemented(),
    })
}

fn combine_hashes(parts: [usize; 3]) -> isize {
    const MULTIPLIER: u64 = 0x9E37_79B9_7F4A_7C15;
    let mut hash = MULTIPLIER;
    for part in parts {
        hash = (hash ^ part as u64).wrapping_mul(MULTIPLIER);
        hash ^= hash >> 32;
    }
    hash as isize
}

fn expr_hash(py: Python<'_>, e: &Expr) -> PyResult<isize> {
    let parts = match &e.form {
        Form::Symbol { name } => [0, e.kind.id, name.bind(py).hash()? as usize],
        Form::Declared { .. } => [1, e.kind.id, e as *const Expr as usize],
        Form::Apply { head, args } => {
            [2, expr_hash(py, head.get())? as usize, args.bind(py).hash()? as usize]
        }
        Form::Literal { value } => [3, e.kind.id, value.bind(py).hash()? as usize],
    };
    Ok(combine_hashes(parts))
}

fn wrong_kind(py: Python<'_>, head: &Expr, expected: KindRef, arg: &Bound<'_, PyAny>) -> PyErr {
    let text = (|| -> PyResult<String> {
        let got = match arg.cast_exact::<Expr>() {
            Ok(expr) => expr.get().kind.name.clone(),
            Err(_) => arg.get_type().name()?.to_string(),
        };
        Ok(format!(
            "{} expects {}, got {}: {}",
            head.label(py)?,
            expected.name,
            got,
            arg.repr()?
        ))
    })();
    match text {
        Ok(text) => PyTypeError::new_err(text),
        Err(error) => error,
    }
}

fn not_a_symbol(py: Python<'_>, head: &Expr, expected: KindRef, arg: &Bound<'_, PyAny>) -> PyErr {
    let text = (|| -> PyResult<String> {
        Ok(format!("{} expects a {} symbol, got {}", head.label(py)?, expected.name, arg.repr()?))
    })();
    match text {
        Ok(text) => PyTypeError::new_err(text),
        Err(error) => error,
    }
}

fn apply<'py>(head: &Bound<'py, Expr>, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, Expr>> {
    let py = args.py();
    let expr = head.get();
    let Some(sig) = &expr.kind.signature else {
        return Err(PyTypeError::new_err(format!(
            "{} is of kind {}, which is not a function kind, so it cannot be called",
            expr.label(py)?,
            expr.kind.name
        )));
    };
    let given = args.len();
    if !sig.fits(given) {
        let expected = match sig.run {
            Some(_) => format!("at least {}", sig.inputs.len() - 1),
            None => sig.inputs.len().to_string(),
        };
        return Err(PyTypeError::new_err(format!(
            "{} takes {} arguments, got {}",
            expr.label(py)?,
            expected,
            given
        )));
    }
    let bound = match &expr.form {
        Form::Declared { bound: Some(bound), .. } => Some(bound),
        _ => None,
    };
    let mut converted: Option<Vec<Bound<'py, PyAny>>> = None;
    let mut items = args.iter_borrowed();
    for (slot, &expected) in sig.inputs.iter().enumerate() {
        let only_symbol = bound.is_some_and(|bound| bound[slot]);
        for (position, arg) in sig.positions(slot, given).zip(&mut items) {
            match arg.cast_exact::<Expr>() {
                Ok(expr_arg) if same_kind(expr_arg.get().kind, expected) => {
                    if only_symbol && !expr_arg.get().is_symbol() {
                        return Err(not_a_symbol(py, expr, expected, &arg));
                    }
                    if let Some(converted) = converted.as_mut() {
                        converted.push(arg.to_owned());
                    }
                }
                Err(_) if expected.accepts(&arg) => {
                    if only_symbol {
                        return Err(not_a_symbol(py, expr, expected, &arg));
                    }
                    let node = literal(expected, &arg)?.into_any();
                    converted
                        .get_or_insert_with(|| args.iter().take(position).collect())
                        .push(node);
                }
                _ => return Err(wrong_kind(py, expr, expected, &arg)),
            }
        }
    }
    let args = match converted {
        Some(converted) => PyTuple::new(py, converted)?,
        None => args.clone(),
    };
    Bound::new(
        py,
        Expr {
            kind: sig.output,
            form: Form::Apply { head: head.clone().unbind(), args: args.unbind() },
        },
    )
}

#[derive(Clone, Copy)]
enum Operator {
    Add,
    Sub,
    Mul,
    Div,
    Pow,
    Neg,
    Lt,
    Gt,
    Le,
    Ge,
}

impl Operator {
    const COUNT: usize = 10;
    const ALL: [Operator; Operator::COUNT] = [
        Operator::Add,
        Operator::Sub,
        Operator::Mul,
        Operator::Div,
        Operator::Pow,
        Operator::Neg,
        Operator::Lt,
        Operator::Gt,
        Operator::Le,
        Operator::Ge,
    ];

    fn symbol(self) -> &'static str {
        match self {
            Operator::Add => "+",
            Operator::Sub => "-",
            Operator::Mul => "*",
            Operator::Div => "/",
            Operator::Pow => "**",
            Operator::Neg => "neg",
            Operator::Lt => "<",
            Operator::Gt => ">",
            Operator::Le => "<=",
            Operator::Ge => ">=",
        }
    }
}

fn operate<'py>(
    py: Python<'py>,
    function: &Py<PyAny>,
    kind: KindRef,
    operator: Operator,
    operands: &[&Bound<'py, PyAny>],
) -> PyResult<Bound<'py, PyAny>> {
    let result = function.bind(py).call1(PyTuple::new(py, operands)?)?;
    if result.cast_exact::<Expr>().is_err() {
        return Err(PyTypeError::new_err(format!(
            "the {} operator for {} must return an expression, got {}: {}",
            operator.symbol(),
            kind.name,
            result.get_type().name()?,
            describe(&result)
        )));
    }
    Ok(result)
}

fn binary<'py>(
    left: &Bound<'py, Expr>,
    right: &Bound<'py, PyAny>,
    operator: Operator,
) -> PyResult<Bound<'py, PyAny>> {
    let py = left.py();
    let kind = left.get().kind;
    match kind.operators[operator as usize].get(py) {
        Some(function) => operate(py, function, kind, operator, &[left.as_any(), right]),
        None => Ok(py.NotImplemented().into_bound(py)),
    }
}

fn reflected<'py>(
    right: &Bound<'py, Expr>,
    left: &Bound<'py, PyAny>,
    operator: Operator,
) -> PyResult<Bound<'py, PyAny>> {
    let kind = right.get().kind;
    if left.cast_exact::<Expr>().is_err() && kind.accepts(left) {
        binary(&literal(kind, left)?, right.as_any(), operator)
    } else {
        Ok(right.py().NotImplemented().into_bound(right.py()))
    }
}

fn check_no_modulus(modulo: &Bound<'_, PyAny>) -> PyResult<()> {
    if modulo.is_none() {
        Ok(())
    } else {
        Err(PyTypeError::new_err("pow() with a modulus is not supported"))
    }
}

#[pymethods]
impl Expr {
    #[pyo3(signature = (*args))]
    fn __call__<'py>(slf: &Bound<'py, Self>, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, Expr>> {
        apply(slf, args)
    }

    #[getter]
    fn kind(&self, py: Python<'_>) -> Option<Py<Kind>> {
        self.kind.object.get(py).map(|kind| kind.clone_ref(py))
    }

    #[getter]
    fn head(&self, py: Python<'_>) -> Option<Py<Expr>> {
        match &self.form {
            Form::Apply { head, .. } => Some(head.clone_ref(py)),
            _ => None,
        }
    }

    #[getter]
    fn args<'py>(&self, py: Python<'py>) -> Bound<'py, PyTuple> {
        match &self.form {
            Form::Apply { args, .. } => args.bind(py).clone(),
            _ => PyTuple::empty(py),
        }
    }

    #[getter]
    fn name(&self, py: Python<'_>) -> Option<Py<PyString>> {
        self.plain_name().map(|name| name.clone_ref(py))
    }

    #[getter]
    fn params<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyTuple>>> {
        let (Form::Declared { names: Some(names), bound, .. }, Some(sig)) =
            (&self.form, &self.kind.signature)
        else {
            return Ok(None);
        };
        let mut params = Vec::with_capacity(sig.inputs.len());
        for (slot, (&kind, name)) in sig.inputs.iter().zip(names.bind(py).iter()).enumerate() {
            let name = name.cast_into::<PyString>()?.unbind();
            let mut param = Py::new(py, Expr { kind, form: Form::Symbol { name } })?.into_any();
            if bound.as_ref().is_some_and(|bound| bound[slot]) {
                param = Py::new(py, BoundVariable { of: param })?.into_any();
            }
            if sig.run == Some(slot) {
                param = Py::new(py, Many { of: param })?.into_any();
            }
            params.push(param);
        }
        PyTuple::new(py, params).map(Some)
    }

    #[getter]
    fn is_symbol(&self) -> bool {
        matches!(self.form, Form::Symbol { .. })
    }

    #[getter]
    fn is_literal(&self) -> bool {
        matches!(self.form, Form::Literal { .. })
    }

    #[getter]
    fn is_constant(&self) -> bool {
        matches!(self.form, Form::Declared { .. })
    }

    #[getter]
    fn value(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        match &self.form {
            Form::Literal { value } => Some(value.clone_ref(py)),
            _ => None,
        }
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        match &self.form {
            Form::Symbol { name } | Form::Declared { name, .. } => Ok(name.bind(py).to_string()),
            Form::Literal { value } => Ok(value.bind(py).repr()?.to_string()),
            Form::Apply { head, args } => {
                let head = head.get();
                let args = args.bind(py);
                let head = match head.plain_name() {
                    Some(name) if args.is_empty() => return Ok(name.bind(py).to_string()),
                    Some(name) => name.bind(py).to_string(),
                    None => head.__repr__(py)?,
                };
                let mut parts = Vec::with_capacity(args.len());
                for arg in args.iter() {
                    parts.push(arg.repr()?.to_string());
                }
                Ok(format!("{}({})", head, parts.join(", ")))
            }
        }
    }

    fn __add__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Add)
    }

    fn __radd__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        reflected(slf, other, Operator::Add)
    }

    fn __sub__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Sub)
    }

    fn __rsub__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        reflected(slf, other, Operator::Sub)
    }

    fn __mul__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Mul)
    }

    fn __rmul__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        reflected(slf, other, Operator::Mul)
    }

    fn __truediv__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Div)
    }

    fn __rtruediv__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        reflected(slf, other, Operator::Div)
    }

    fn __pow__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        modulo: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        check_no_modulus(modulo)?;
        binary(slf, other, Operator::Pow)
    }

    fn __rpow__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        modulo: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        check_no_modulus(modulo)?;
        reflected(slf, other, Operator::Pow)
    }

    fn __neg__<'py>(slf: &Bound<'py, Self>) -> PyResult<Bound<'py, PyAny>> {
        let py = slf.py();
        let kind = slf.get().kind;
        match kind.operators[Operator::Neg as usize].get(py) {
            Some(function) => operate(py, function, kind, Operator::Neg, &[slf.as_any()]),
            None => Err(PyTypeError::new_err(format!(
                "bad operand type for unary -: an expression of kind {}",
                kind.name
            ))),
        }
    }

    fn __richcmp__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        op: CompareOp,
    ) -> PyResult<Py<PyAny>> {
        let operator = match op {
            CompareOp::Lt => Operator::Lt,
            CompareOp::Gt => Operator::Gt,
            CompareOp::Le => Operator::Le,
            CompareOp::Ge => Operator::Ge,
            CompareOp::Eq | CompareOp::Ne => return compare(slf.get(), other, op),
        };
        Ok(binary(slf, other, operator)?.unbind())
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        expr_hash(py, self)
    }

    fn __getattr__(&self, py: Python<'_>, name: &Bound<'_, PyString>) -> PyResult<Py<PyAny>> {
        if let Form::Apply { head, args } = &self.form {
            let head = head.get();
            if let (Form::Declared { names: Some(names), .. }, Some(sig)) =
                (&head.form, &head.kind.signature)
            {
                for (slot, declared) in names.bind(py).iter().enumerate() {
                    if declared.eq(name)? {
                        let args = args.bind(py);
                        let positions = sig.positions(slot, args.len());
                        return Ok(if sig.run == Some(slot) {
                            args.get_slice(positions.start, positions.end).into_any().unbind()
                        } else {
                            args.get_item(positions.start)?.unbind()
                        });
                    }
                }
            }
        }
        Err(PyAttributeError::new_err(format!(
            "'Expr' object has no attribute '{name}'"
        )))
    }
}

struct Parameter<'py> {
    kind: KindRef,
    name: Bound<'py, PyString>,
    run: bool,
    bound: bool,
}

fn parameter<'py>(function: &str, param: &Bound<'py, PyAny>) -> PyResult<Parameter<'py>> {
    let py = param.py();
    let (inner, run) = match param.cast_exact::<Many>() {
        Ok(many) => (many.get().of.bind(py).clone(), true),
        Err(_) => (param.clone(), false),
    };
    let (inner, bound) = match inner.cast_exact::<BoundVariable>() {
        Ok(marker) => (marker.get().of.bind(py).clone(), true),
        Err(_) => (inner, false),
    };
    if let Ok(symbol) = inner.cast_exact::<Expr>() {
        if let Form::Symbol { name } = &symbol.get().form {
            let name = name.bind(py).clone();
            return Ok(Parameter { kind: symbol.get().kind, name, run, bound });
        }
    }
    Err(PyTypeError::new_err(format!(
        "{function}: a parameter must be a symbol, such as NumberKind(\"x\"), got {}",
        describe(param)
    )))
}

#[pyfunction]
#[pyo3(signature = (name, *params, returns))]
fn declare_function<'py>(
    py: Python<'py>,
    name: Py<PyString>,
    params: &Bound<'py, PyTuple>,
    returns: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, Expr>> {
    let function = name.bind(py).to_string();
    let returns = match returns.cast_exact::<Kind>() {
        Ok(kind) => kind.get().data,
        Err(_) => {
            return Err(PyValueError::new_err(format!(
                "returns must be a kind, got {}",
                describe(returns)
            )));
        }
    };
    let mut kinds = Vec::with_capacity(params.len());
    let mut names: Vec<Bound<'py, PyString>> = Vec::with_capacity(params.len());
    let mut bound = Vec::with_capacity(params.len());
    let mut run = None;
    for (slot, param) in params.iter().enumerate() {
        let param = parameter(&function, &param)?;
        let param_name = param.name;
        if py.get_type::<Expr>().hasattr(&param_name)? {
            return Err(PyValueError::new_err(format!(
                "{function}: the parameter name {param_name} clashes with the attribute \
                 Expr.{param_name}"
            )));
        }
        if names.iter().any(|earlier| earlier.as_any().eq(&param_name).is_ok_and(|same| same)) {
            return Err(PyValueError::new_err(format!(
                "{function} has two parameters named {param_name}"
            )));
        }
        if param.run && run.replace(slot).is_some() {
            return Err(PyTypeError::new_err(format!(
                "{function}: at most one parameter can be Many, got {}",
                describe(params)
            )));
        }
        kinds.push(param.kind);
        names.push(param_name);
        bound.push(param.bound);
    }
    let bound = bound.contains(&true).then(|| bound.into_boxed_slice());
    let names = Some(PyTuple::new(py, names)?.unbind());
    let kind = function_kind(py, &kinds, run, returns)?;
    Bound::new(py, Expr { kind, form: Form::Declared { name, names, bound } })
}

#[pyfunction]
fn declare_constant<'py>(
    py: Python<'py>,
    name: Py<PyString>,
    kind: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, Expr>> {
    let kind = expect_kind(kind)?;
    Bound::new(py, Expr { kind, form: Form::Declared { name, names: None, bound: None } })
}

#[pyfunction]
fn set_operator(
    py: Python<'_>,
    kind: &Bound<'_, PyAny>,
    symbol: &str,
    function: &Bound<'_, PyAny>,
) -> PyResult<()> {
    let kind = expect_kind(kind)?;
    let Some(operator) = Operator::ALL.into_iter().find(|op| op.symbol() == symbol) else {
        return Err(PyValueError::new_err(format!("unknown operator {symbol:?}")));
    };
    if function.cast_exact::<Expr>().is_ok_and(|expr| expr.get().kind.signature.is_none()) {
        return Err(PyTypeError::new_err(format!(
            "set_operator expects an expression of a function kind, got {}",
            describe(function)
        )));
    }
    if !function.is_callable() {
        return Err(PyTypeError::new_err(format!(
            "set_operator expects a callable, got {}",
            describe(function)
        )));
    }
    kind.operators[operator as usize].set(py, function.clone().unbind()).map_err(|_| {
        PyValueError::new_err(format!(
            "the {symbol} operator is already set for {}",
            kind.name
        ))
    })
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Expr>()?;
    m.add_class::<Kind>()?;
    m.add_class::<KindFamily>()?;
    m.add_class::<Many>()?;
    m.add_class::<BoundVariable>()?;
    m.add_function(wrap_pyfunction!(declare_kind, m)?)?;
    m.add_function(wrap_pyfunction!(declare_kind_family, m)?)?;
    m.add_function(wrap_pyfunction!(function_kind_py, m)?)?;
    m.add_function(wrap_pyfunction!(declare_function, m)?)?;
    m.add_function(wrap_pyfunction!(declare_constant, m)?)?;
    m.add_function(wrap_pyfunction!(set_operator, m)?)?;
    Ok(())
}

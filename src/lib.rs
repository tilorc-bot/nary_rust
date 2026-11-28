use std::cell::{Cell, RefCell};
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{LazyLock, Mutex, PoisonError};

use pyo3::exceptions::{PyAttributeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::pyclass::CompareOp;
use pyo3::sync::{MutexExt, PyOnceLock};
use pyo3::types::{PyDict, PyString, PyTuple, PyType};

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
    run_element: Option<KindRef>,
    output: KindRef,
}

impl Signature {
    fn fixed(&self) -> usize {
        self.inputs.len() - usize::from(self.run_element.is_some())
    }
}

static MANY: PyOnceLock<Py<KindFamily>> = PyOnceLock::new();
static PROPERTIES: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

fn run_element(py: Python<'_>, kind: KindRef) -> Option<KindRef> {
    let many = MANY.get(py)?;
    match &kind.family {
        Some(family) if family.is(many) => Some(kind.params[0]),
        _ => None,
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

static FRACTION: PyOnceLock<Py<PyType>> = PyOnceLock::new();

fn integer_if_denominator_is_one<'py>(
    kind: KindRef,
    value: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let fraction = FRACTION.import(value.py(), "fractions", "Fraction")?;
    if value.get_type().is(fraction) && value.getattr("denominator")?.eq(1)? {
        let numerator = value.getattr("numerator")?;
        if kind.accepts(&numerator) {
            return Ok(numerator);
        }
    }
    Ok(value.clone())
}

fn literal<'py>(kind: KindRef, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, Expr>> {
    let value = integer_if_denominator_is_one(kind, value)?;
    new_expr(value.py(), kind, Form::Literal { value: value.unbind() })
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
            return new_expr(py, self.data, Form::Symbol { name: name.clone().unbind() });
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
        self.data.signature.as_ref().map(|sig| kind_tuple(py, &sig.inputs)).transpose()
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

fn function_kind_name(inputs: &[KindRef], output: KindRef) -> String {
    let names: Vec<&str> = inputs.iter().map(|kind| kind.name.as_str()).collect();
    let inputs = match names.len() {
        1 => format!("({},)", names[0]),
        _ => format!("({})", names.join(", ")),
    };
    format!("FunctionKind({inputs}, {})", output.name)
}

fn function_kind(py: Python<'_>, inputs: &[KindRef], output: KindRef) -> PyResult<KindRef> {
    if run_element(py, output).is_some() {
        return Err(PyTypeError::new_err(format!(
            "a function cannot return a run, got {}",
            output.name
        )));
    }
    let mut run = None;
    for (position, &input) in inputs.iter().enumerate() {
        let Some(element) = run_element(py, input) else { continue };
        if position + 1 != inputs.len() {
            return Err(PyTypeError::new_err(format!(
                "a run can only be the last input, got {} at position {}",
                input.name, position
            )));
        }
        if run_element(py, element).is_some() {
            return Err(PyTypeError::new_err(format!(
                "{} is a run of runs, which is not supported",
                input.name
            )));
        }
        run = Some(element);
    }
    let mut key = Vec::with_capacity(inputs.len() + 1);
    key.push(output.id);
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
                    function_kind_name(inputs, output),
                    None,
                    Box::new([]),
                    Some(Signature { inputs: inputs.into(), run_element: run, output }),
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
    for input in inputs.iter() {
        kinds.push(expect_kind(&input)?);
    }
    let output = expect_kind(output)?;
    kind_object(py, function_kind(py, &kinds, output)?)
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

#[pyclass(frozen, module = "nary", name = "Symbol")]
struct SymbolMarker {
    kind: KindRef,
}

#[pymethods]
impl SymbolMarker {
    #[new]
    fn new(kind: &Bound<'_, PyAny>) -> PyResult<Self> {
        Ok(SymbolMarker { kind: expect_kind(kind)? })
    }

    #[getter]
    fn kind(&self, py: Python<'_>) -> PyResult<Py<Kind>> {
        kind_object(py, self.kind)
    }

    fn __repr__(&self) -> String {
        format!("Symbol({})", self.kind.name)
    }
}

#[pyclass(frozen, module = "nary")]
struct Expr {
    kind: KindRef,
    hash: Option<isize>,
    form: Form,
}

enum Form {
    Symbol { name: Py<PyString> },
    Literal { value: Py<PyAny> },
    Declared {
        name: Py<PyString>,
        names: Option<Py<PyTuple>>,
        symbols: Option<Box<[bool]>>,
    },
    Apply { head: Py<Expr>, args: Py<PyTuple> },
}

thread_local! {
    static DROPPING: Cell<bool> = const { Cell::new(false) };
    static DEFERRED: RefCell<Vec<Form>> = const { RefCell::new(Vec::new()) };
}

impl Drop for Expr {
    fn drop(&mut self) {
        if !matches!(self.form, Form::Apply { .. }) {
            return;
        }
        let form = Python::attach(|py| {
            std::mem::replace(&mut self.form, Form::Literal { value: py.None() })
        });
        if DROPPING.get() {
            DEFERRED.with_borrow_mut(|deferred| deferred.push(form));
            return;
        }
        DROPPING.set(true);
        drop(form);
        while let Some(form) = DEFERRED.with_borrow_mut(Vec::pop) {
            drop(form);
        }
        DROPPING.set(false);
    }
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
            None => expr_repr(py, self),
        }
    }
}

fn structural_eq<'py>(a: &Bound<'py, Expr>, b: &Bound<'py, Expr>) -> PyResult<bool> {
    let py = a.py();
    let mut pending = vec![(a.clone(), b.clone())];
    while let Some((a, b)) = pending.pop() {
        if a.is(&b) {
            continue;
        }
        let (a, b) = (a.get(), b.get());
        if !same_kind(a.kind, b.kind) || matches!((a.hash, b.hash), (Some(x), Some(y)) if x != y) {
            return Ok(false);
        }
        let equal = match (&a.form, &b.form) {
            (Form::Symbol { name: x }, Form::Symbol { name: y }) => {
                x.bind(py).as_any().eq(y.bind(py))?
            }
            (Form::Literal { value: x }, Form::Literal { value: y }) => {
                let (x, y) = (x.bind(py), y.bind(py));
                x.get_type().is(&y.get_type()) && x.eq(y)?
            }
            (Form::Apply { head: h1, args: a1 }, Form::Apply { head: h2, args: a2 }) => {
                let (a1, a2) = (a1.bind(py), a2.bind(py));
                if a1.len() != a2.len() {
                    return Ok(false);
                }
                for (x, y) in a1.iter().zip(a2.iter()).rev() {
                    pending.push((x.cast_into()?, y.cast_into()?));
                }
                pending.push((h1.bind(py).clone(), h2.bind(py).clone()));
                true
            }
            _ => false,
        };
        if !equal {
            return Ok(false);
        }
    }
    Ok(true)
}

fn compare(slf: &Bound<'_, Expr>, other: &Bound<'_, PyAny>, op: CompareOp) -> PyResult<Py<PyAny>> {
    let py = other.py();
    let equal = match other.cast_exact::<Expr>() {
        Ok(other) => structural_eq(slf, other)?,
        Err(_) => return Ok(py.NotImplemented()),
    };
    Ok(match op {
        CompareOp::Eq => equal.into_pyobject(py)?.to_owned().into_any().unbind(),
        CompareOp::Ne => (!equal).into_pyobject(py)?.to_owned().into_any().unbind(),
        _ => py.NotImplemented(),
    })
}

fn mix(hash: u64, part: usize) -> u64 {
    const MULTIPLIER: u64 = 0x9E37_79B9_7F4A_7C15;
    let hash = (hash ^ part as u64).wrapping_mul(MULTIPLIER);
    hash ^ (hash >> 32)
}

static DECLARED_COUNT: AtomicUsize = AtomicUsize::new(0);

fn form_hash(py: Python<'_>, kind: KindRef, form: &Form) -> Option<isize> {
    let parts = match form {
        Form::Symbol { name } => [0, kind.id, name.bind(py).hash().ok()? as usize],
        Form::Declared { .. } => [1, kind.id, DECLARED_COUNT.fetch_add(1, Ordering::Relaxed)],
        Form::Literal { value } => [3, kind.id, value.bind(py).hash().ok()? as usize],
        Form::Apply { .. } => unreachable!("apply computes the hash of an application"),
    };
    Some(parts.into_iter().fold(0, mix) as isize)
}

fn new_expr(py: Python<'_>, kind: KindRef, form: Form) -> PyResult<Bound<'_, Expr>> {
    let hash = form_hash(py, kind, &form);
    Bound::new(py, Expr { kind, hash, form })
}

enum Piece<'py> {
    Text(&'static str),
    Expr(Bound<'py, Expr>),
}

fn literal_repr(value: &Bound<'_, PyAny>) -> PyResult<String> {
    let fraction = FRACTION.import(value.py(), "fractions", "Fraction")?;
    if value.get_type().is(fraction) {
        let (numerator, denominator) = (value.getattr("numerator")?, value.getattr("denominator")?);
        return Ok(format!("Rational({numerator}, {denominator})"));
    }
    Ok(value.repr()?.to_cow()?.into_owned())
}

fn expr_repr(py: Python<'_>, root: &Expr) -> PyResult<String> {
    let mut text = String::new();
    let mut pending = Vec::new();
    let mut next = Some(root);
    let mut held;
    loop {
        if let Some(e) = next.take() {
            match &e.form {
                Form::Symbol { name } | Form::Declared { name, .. } => {
                    text.push_str(&name.bind(py).to_cow()?)
                }
                Form::Literal { value } => text.push_str(&literal_repr(value.bind(py))?),
                Form::Apply { head, args } => {
                    let args = args.bind(py);
                    if !(args.is_empty() && head.get().plain_name().is_some()) {
                        pending.push(Piece::Text(")"));
                        for (position, arg) in args.iter().enumerate().rev() {
                            pending.push(Piece::Expr(arg.cast_into()?));
                            if position > 0 {
                                pending.push(Piece::Text(", "));
                            }
                        }
                        pending.push(Piece::Text("("));
                    }
                    pending.push(Piece::Expr(head.bind(py).clone()));
                }
            }
        }
        match pending.pop() {
            Some(Piece::Text(piece)) => text.push_str(piece),
            Some(Piece::Expr(e)) => {
                held = e;
                next = Some(held.get());
            }
            None => return Ok(text),
        }
    }
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

fn check_symbols(
    py: Python<'_>,
    head: &Expr,
    inputs: &[KindRef],
    symbols: &[bool],
    args: &Bound<'_, PyTuple>,
) -> PyResult<()> {
    for (position, &only_symbol) in symbols.iter().enumerate() {
        if !only_symbol {
            continue;
        }
        let arg = args.get_borrowed_item(position)?;
        if !arg.cast_exact::<Expr>().is_ok_and(|arg| arg.get().is_symbol()) {
            let kind = &inputs[position].name;
            return Err(PyTypeError::new_err(format!(
                "{} expects a {} symbol, got {}: {}",
                head.label(py)?,
                kind,
                kind,
                arg.repr()?
            )));
        }
    }
    Ok(())
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
    let fixed = sig.fixed();
    let given = args.len();
    if given < fixed || (sig.run_element.is_none() && given > fixed) {
        let expected = if sig.run_element.is_some() {
            format!("at least {}", fixed)
        } else {
            fixed.to_string()
        };
        return Err(PyTypeError::new_err(format!(
            "{} takes {} arguments, got {}",
            expr.label(py)?,
            expected,
            given
        )));
    }
    let mut converted: Option<Vec<Bound<'py, PyAny>>> = None;
    let mut hash = expr.hash.map(|head_hash| mix(mix(0, 2), head_hash as usize));
    for (position, arg) in args.iter_borrowed().enumerate() {
        let expected = match sig.run_element {
            Some(element) if position >= fixed => element,
            _ => sig.inputs[position],
        };
        match arg.cast_exact::<Expr>() {
            Ok(expr_arg) if same_kind(expr_arg.get().kind, expected) => {
                hash = hash.zip(expr_arg.get().hash).map(|(h, a)| mix(h, a as usize));
                if let Some(converted) = converted.as_mut() {
                    converted.push(arg.to_owned());
                }
            }
            Err(_) if expected.accepts(&arg) => {
                let node = literal(expected, &arg)?;
                hash = hash.zip(node.get().hash).map(|(h, a)| mix(h, a as usize));
                converted
                    .get_or_insert_with(|| args.iter().take(position).collect())
                    .push(node.into_any());
            }
            _ => return Err(wrong_kind(py, expr, expected, &arg)),
        }
    }
    let args = match converted {
        Some(converted) => PyTuple::new(py, converted)?,
        None => args.clone(),
    };
    if let Form::Declared { symbols: Some(symbols), .. } = &expr.form {
        check_symbols(py, expr, &sig.inputs, symbols, &args)?;
    }
    Bound::new(
        py,
        Expr {
            kind: sig.output,
            hash: hash.map(|h| h as isize),
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
    fn names<'py>(&self, py: Python<'py>) -> Bound<'py, PyTuple> {
        match &self.form {
            Form::Declared { names: Some(names), .. } => names.bind(py).clone(),
            _ => PyTuple::empty(py),
        }
    }

    #[getter]
    fn params<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyTuple>>> {
        let (Form::Declared { symbols, .. }, Some(sig)) = (&self.form, &self.kind.signature) else {
            return Ok(None);
        };
        let mut params = Vec::with_capacity(sig.inputs.len());
        for (position, &kind) in sig.inputs.iter().enumerate() {
            let only_symbol = symbols.as_ref().is_some_and(|symbols| symbols[position]);
            params.push(if only_symbol {
                Bound::new(py, SymbolMarker { kind })?.into_any()
            } else {
                kind_object(py, kind)?.into_bound(py).into_any()
            });
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
    fn is_atom(&self) -> bool {
        !matches!(self.form, Form::Apply { .. })
    }

    #[getter]
    fn value(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        match &self.form {
            Form::Literal { value } => Some(value.clone_ref(py)),
            _ => None,
        }
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        expr_repr(py, self)
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
            CompareOp::Eq | CompareOp::Ne => return compare(slf, other, op),
        };
        Ok(binary(slf, other, operator)?.unbind())
    }

    fn __hash__(&self) -> PyResult<isize> {
        self.hash.ok_or_else(|| PyTypeError::new_err("unhashable literal in expression"))
    }

    fn __getattr__(slf: &Bound<'_, Self>, name: &Bound<'_, PyString>) -> PyResult<Py<PyAny>> {
        let py = slf.py();
        let this = slf.get();
        if let Form::Apply { head, args } = &this.form {
            let head = head.get();
            if let (Form::Declared { names: Some(names), .. }, Some(sig)) =
                (&head.form, &head.kind.signature)
            {
                let args = args.bind(py);
                for (index, declared) in names.bind(py).iter().enumerate() {
                    if !declared.eq(name)? {
                        continue;
                    }
                    if sig.run_element.is_some() && index == sig.fixed() {
                        return Ok(args.get_slice(index, args.len()).into_any().unbind());
                    }
                    return Ok(args.get_item(index)?.unbind());
                }
            }
        }
        if let (Some(_), Some(properties)) = (&this.kind.signature, PROPERTIES.get(py)) {
            let properties = properties.bind(py).call1((slf,))?.cast_into::<PyDict>()?;
            if let Some(value) = properties.get_item(name)? {
                return Ok(value.unbind());
            }
        }
        Err(PyAttributeError::new_err(format!(
            "'Expr' object has no attribute '{name}'"
        )))
    }
}

#[pyfunction]
#[pyo3(signature = (name, *arg_kinds, returns, names=None))]
fn declare_function<'py>(
    py: Python<'py>,
    name: Py<PyString>,
    arg_kinds: &Bound<'py, PyTuple>,
    returns: &Bound<'py, PyAny>,
    names: Option<Py<PyTuple>>,
) -> PyResult<Bound<'py, Expr>> {
    let returns = match returns.cast_exact::<Kind>() {
        Ok(kind) => kind.get().data,
        Err(_) => {
            return Err(PyValueError::new_err(format!(
                "returns must be a kind, got {}",
                describe(returns)
            )));
        }
    };
    let mut kinds = Vec::with_capacity(arg_kinds.len());
    let mut symbols = Vec::with_capacity(arg_kinds.len());
    for param in arg_kinds.iter() {
        match param.cast_exact::<SymbolMarker>() {
            Ok(marker) => {
                let kind = marker.get().kind;
                if run_element(py, kind).is_some() {
                    return Err(PyTypeError::new_err(format!(
                        "{}: a run cannot be marked {}",
                        name.bind(py),
                        describe(marker.as_any())
                    )));
                }
                kinds.push(kind);
                symbols.push(true);
            }
            Err(_) => {
                kinds.push(expect_kind(&param)?);
                symbols.push(false);
            }
        }
    }
    let symbols = symbols.contains(&true).then(|| symbols.into_boxed_slice());
    let names = match names {
        Some(names) if names.bind(py).len() > kinds.len() => {
            return Err(PyValueError::new_err(format!(
                "{}: more names than declared arguments",
                name.bind(py)
            )));
        }
        Some(names) if names.bind(py).is_empty() => None,
        other => other,
    };
    let kind = function_kind(py, &kinds, returns)?;
    new_expr(py, kind, Form::Declared { name, names, symbols })
}

#[pyfunction]
fn declare_constant<'py>(
    py: Python<'py>,
    name: Py<PyString>,
    kind: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, Expr>> {
    let kind = expect_kind(kind)?;
    new_expr(py, kind, Form::Declared { name, names: None, symbols: None })
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

#[pyfunction(name = "_set_properties")]
fn set_properties(py: Python<'_>, properties: Py<PyAny>) -> PyResult<()> {
    PROPERTIES
        .set(py, properties)
        .map_err(|_| PyValueError::new_err("the properties are already set"))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Expr>()?;
    m.add_class::<Kind>()?;
    m.add_class::<KindFamily>()?;
    m.add_class::<SymbolMarker>()?;
    let many = MANY.get_or_try_init(m.py(), || {
        Py::new(
            m.py(),
            KindFamily { name: "Many".into(), params: Some(1), instances: Mutex::new(HashMap::new()) },
        )
    })?;
    m.add("Many", many.clone_ref(m.py()))?;
    m.add_function(wrap_pyfunction!(declare_kind, m)?)?;
    m.add_function(wrap_pyfunction!(declare_kind_family, m)?)?;
    m.add_function(wrap_pyfunction!(function_kind_py, m)?)?;
    m.add_function(wrap_pyfunction!(declare_function, m)?)?;
    m.add_function(wrap_pyfunction!(declare_constant, m)?)?;
    m.add_function(wrap_pyfunction!(set_operator, m)?)?;
    m.add_function(wrap_pyfunction!(set_properties, m)?)?;
    Ok(())
}

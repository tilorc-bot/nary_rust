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
    spread: Option<usize>,
    signature: Option<Signature>,
    literals: Box<[Py<PyType>]>,
    variable: bool,
    generic: bool,
}

struct Signature {
    inputs: Box<[KindRef]>,
    run: Option<usize>,
    spread: Option<usize>,
    output: KindRef,
}

impl Signature {
    fn open(&self) -> Option<usize> {
        self.run.or(self.spread)
    }

    fn fits(&self, given: usize) -> bool {
        match self.open() {
            Some(_) => given + 1 >= self.inputs.len(),
            None => given == self.inputs.len(),
        }
    }

    fn positions(&self, slot: usize, given: usize) -> std::ops::Range<usize> {
        slot_positions(self.inputs.len(), self.open(), slot, given)
    }
}

fn slot_positions(
    slots: usize,
    open: Option<usize>,
    slot: usize,
    given: usize,
) -> std::ops::Range<usize> {
    match open {
        Some(run) if slot >= run => {
            let taken = given + 1 - slots;
            if slot == run {
                run..run + taken
            } else {
                slot + taken - 1..slot + taken
            }
        }
        _ => slot..slot + 1,
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
    spread: Option<usize>,
    signature: Option<Signature>,
    literals: Box<[Py<PyType>]>,
    variable: bool,
) -> KindRef {
    let generic = variable
        || params.iter().any(|kind| kind.generic)
        || signature.as_ref().is_some_and(|sig| {
            sig.output.generic || sig.inputs.iter().any(|kind| kind.generic)
        });
    Box::leak(Box::new(KindData {
        id: KIND_COUNT.fetch_add(1, Ordering::Relaxed),
        name,
        object: PyOnceLock::new(),
        operators: [const { PyOnceLock::new() }; Operator::COUNT],
        family,
        params,
        spread,
        signature,
        literals,
        variable,
        generic,
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
        let mut params = Vec::with_capacity(self.data.params.len());
        for (slot, &kind) in self.data.params.iter().enumerate() {
            let mut param = kind_object(py, kind)?.into_any();
            if self.data.spread == Some(slot) {
                param = Py::new(py, ManyMixed { of: param })?.into_any();
            }
            params.push(param);
        }
        PyTuple::new(py, params)
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
            } else if sig.spread == Some(slot) {
                input = Py::new(py, ManyMixed { of: input })?.into_any();
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
    kind_object(py, new_kind_data(name, None, Box::new([]), None, None, literals, false))
}

#[pyfunction(name = "KindVariable")]
fn kind_variable(py: Python<'_>, name: String) -> PyResult<Py<Kind>> {
    kind_object(py, new_kind_data(name, None, Box::new([]), None, None, Box::new([]), true))
}

static FUNCTION_KINDS: LazyLock<Mutex<HashMap<Box<[usize]>, KindRef>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

fn function_kind_name(
    inputs: &[KindRef],
    run: Option<usize>,
    spread: Option<usize>,
    output: KindRef,
) -> String {
    let names: Vec<String> = inputs
        .iter()
        .enumerate()
        .map(|(slot, kind)| {
            if run == Some(slot) {
                format!("Many({})", kind.name)
            } else if spread == Some(slot) {
                format!("ManyMixed({})", kind.name)
            } else {
                kind.name.clone()
            }
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
    spread: Option<usize>,
    output: KindRef,
) -> PyResult<KindRef> {
    let mut key = Vec::with_capacity(inputs.len() + 3);
    key.push(output.id);
    key.push(run.unwrap_or(usize::MAX));
    key.push(spread.unwrap_or(usize::MAX));
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
                    function_kind_name(inputs, run, spread, output),
                    None,
                    Box::new([]),
                    None,
                    Some(Signature { inputs: inputs.into(), run, spread, output }),
                    Box::new([]),
                    false,
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
    let mut open = None;
    for input in inputs.iter() {
        let (inner, shape) = unwrap_shape(&input);
        let kind = expect_kind(&inner)?;
        if shape != Shape::One && open.replace((kinds.len(), shape)).is_some() {
            return Err(PyTypeError::new_err(format!(
                "FunctionKind: at most one input can be Many or ManyMixed, got {}",
                describe(inputs)
            )));
        }
        kinds.push(kind);
    }
    let (run, spread) = open_slots(open);
    let output = expect_kind(output)?;
    kind_object(py, function_kind(py, &kinds, run, spread, output)?)
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
        let mut spread = None;
        for param in params.iter() {
            let (inner, shape) = unwrap_shape(&param);
            if shape == Shape::Many {
                return Err(PyTypeError::new_err(format!(
                    "{}: a parameter of a kind family cannot be {}",
                    family.name,
                    describe(&param)
                )));
            }
            if let (Shape::ManyMixed, Some(n)) = (shape, family.params) {
                return Err(PyTypeError::new_err(format!(
                    "{} takes {}, so a parameter cannot be {}",
                    family.name,
                    count(n, "parameter"),
                    describe(&param)
                )));
            }
            if shape == Shape::ManyMixed && spread.replace(kinds.len()).is_some() {
                return Err(PyTypeError::new_err(format!(
                    "{}: at most one parameter can be ManyMixed, got {}",
                    family.name,
                    describe(params)
                )));
            }
            kinds.push(expect_kind(&inner)?);
        }
        kind_object(py, family_instance(slf, kinds, spread)?)
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

fn family_instance(
    family: &Bound<'_, KindFamily>,
    kinds: Vec<KindRef>,
    spread: Option<usize>,
) -> PyResult<KindRef> {
    let mut key = Vec::with_capacity(kinds.len() + 1);
    key.push(spread.unwrap_or(usize::MAX));
    key.extend(kinds.iter().map(|kind| kind.id));
    // No Python code runs while the table is locked, so the lock
    // cannot be asked for again by this thread before it is released.
    let mut instances = family
        .get()
        .instances
        .lock_py_attached(family.py())
        .unwrap_or_else(PoisonError::into_inner);
    let data = *instances.entry(key.into_boxed_slice()).or_insert_with(|| {
        let names: Vec<String> = kinds
            .iter()
            .enumerate()
            .map(|(slot, kind)| match spread == Some(slot) {
                true => format!("ManyMixed({})", kind.name),
                false => kind.name.clone(),
            })
            .collect();
        new_kind_data(
            format!("{}({})", family.get().name, names.join(", ")),
            Some(family.clone().unbind()),
            kinds.into_boxed_slice(),
            spread,
            None,
            Box::new([]),
            false,
        )
    });
    drop(instances);
    kind_object(family.py(), data)?;
    Ok(data)
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

#[derive(Clone, Copy, PartialEq)]
enum Shape {
    One,
    Many,
    ManyMixed,
}

fn unwrap_shape<'py>(obj: &Bound<'py, PyAny>) -> (Bound<'py, PyAny>, Shape) {
    let py = obj.py();
    if let Ok(many) = obj.cast_exact::<Many>() {
        (many.get().of.bind(py).clone(), Shape::Many)
    } else if let Ok(spread) = obj.cast_exact::<ManyMixed>() {
        (spread.get().of.bind(py).clone(), Shape::ManyMixed)
    } else {
        (obj.clone(), Shape::One)
    }
}

fn open_slots(open: Option<(usize, Shape)>) -> (Option<usize>, Option<usize>) {
    match open {
        Some((slot, Shape::Many)) => (Some(slot), None),
        Some((slot, _)) => (None, Some(slot)),
        None => (None, None),
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
struct ManyMixed {
    #[pyo3(get)]
    of: Py<PyAny>,
}

#[pymethods]
impl ManyMixed {
    #[new]
    fn new(of: &Bound<'_, PyAny>) -> PyResult<Self> {
        let py = of.py();
        let symbol = match of.cast_exact::<BoundVariable>() {
            Ok(marker) => marker.get().of.bind(py).clone(),
            Err(_) => of.clone(),
        };
        let kind = match (symbol.cast_exact::<Kind>(), symbol.cast_exact::<Expr>()) {
            (Ok(kind), _) => Some(kind.get().data),
            (_, Ok(expr)) if expr.get().is_symbol() => Some(expr.get().kind),
            _ => None,
        };
        match kind {
            Some(kind) if kind.variable => Ok(ManyMixed { of: of.clone().unbind() }),
            Some(kind) => Err(PyTypeError::new_err(format!(
                "ManyMixed takes a kind variable or a symbol of one, got {}; \
                 for any number of arguments of kind {} use Many",
                describe(of),
                kind.name
            ))),
            None => Err(PyTypeError::new_err(format!(
                "ManyMixed takes a kind variable or a symbol of one, got {}",
                describe(of)
            ))),
        }
    }

    fn __eq__(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        match other.cast_exact::<ManyMixed>() {
            Ok(other) => self.of.bind(py).eq(other.get().of.bind(py)),
            Err(_) => Ok(false),
        }
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        self.of.bind(py).hash()
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!("ManyMixed({})", self.of.bind(py).repr()?))
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
        params: Option<Box<[Param]>>,
        bound: Option<Box<[bool]>>,
        origin: Option<Box<Origin>>,
    },
    Apply { head: Py<Expr>, args: Py<PyTuple> },
}

struct Param {
    name: Py<PyString>,
    kind: KindRef,
    shape: Shape,
    bound: bool,
}

fn param_positions(params: &[Param], index: usize, given: usize) -> std::ops::Range<usize> {
    let open = params.iter().position(|param| param.shape != Shape::One);
    slot_positions(params.len(), open, index, given)
}

enum Origin {
    Generic { variables: Box<[Variable]>, instances: Mutex<HashMap<Box<[usize]>, Py<Expr>>> },
    Concrete { generic: Py<Expr> },
}

#[derive(Clone, Copy)]
struct Variable {
    kind: KindRef,
    mixed: bool,
}

fn generic_variables(expr: &Expr) -> Option<&[Variable]> {
    match &expr.form {
        Form::Declared { origin: Some(origin), .. } => match &**origin {
            Origin::Generic { variables, .. } => Some(variables),
            Origin::Concrete { .. } => None,
        },
        _ => None,
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
    if expr.kind.generic {
        if let Some(variables) = generic_variables(expr) {
            return apply_generic(head, variables, sig, args);
        }
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
    let head = match &expr.form {
        Form::Declared { origin: Some(origin), .. } => match &**origin {
            Origin::Concrete { generic } => generic.clone_ref(py),
            Origin::Generic { .. } => head.clone().unbind(),
        },
        _ => head.clone().unbind(),
    };
    Bound::new(py, Expr { kind: sig.output, form: Form::Apply { head, args: args.unbind() } })
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
        let Form::Declared { params: Some(params), .. } = &self.form else {
            return Ok(None);
        };
        let mut objects = Vec::with_capacity(params.len());
        for param in params.iter() {
            let name = param.name.clone_ref(py);
            let mut object = Py::new(py, Expr { kind: param.kind, form: Form::Symbol { name } })?.into_any();
            if param.bound {
                object = Py::new(py, BoundVariable { of: object })?.into_any();
            }
            object = match param.shape {
                Shape::One => object,
                Shape::Many => Py::new(py, Many { of: object })?.into_any(),
                Shape::ManyMixed => Py::new(py, ManyMixed { of: object })?.into_any(),
            };
            objects.push(object);
        }
        PyTuple::new(py, objects).map(Some)
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
            if let Form::Declared { params: Some(params), .. } = &head.get().form {
                for (index, param) in params.iter().enumerate() {
                    if param.name.bind(py).as_any().eq(name)? {
                        let args = args.bind(py);
                        let positions = param_positions(params, index, args.len());
                        return Ok(match param.shape {
                            Shape::One => args.get_item(positions.start)?.unbind(),
                            _ => args.get_slice(positions.start, positions.end).into_any().unbind(),
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

fn parameter(function: &str, param: &Bound<'_, PyAny>) -> PyResult<Param> {
    let py = param.py();
    let (inner, shape) = unwrap_shape(param);
    let (inner, bound) = match inner.cast_exact::<BoundVariable>() {
        Ok(marker) => (marker.get().of.bind(py).clone(), true),
        Err(_) => (inner, false),
    };
    if let Ok(symbol) = inner.cast_exact::<Expr>() {
        if let Form::Symbol { name } = &symbol.get().form {
            let name = name.clone_ref(py);
            return Ok(Param { name, kind: symbol.get().kind, shape, bound });
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
    let mut declared: Vec<Param> = Vec::with_capacity(params.len());
    let mut open = false;
    for param in params.iter() {
        let param = parameter(&function, &param)?;
        let param_name = param.name.bind(py);
        if py.get_type::<Expr>().hasattr(param_name)? {
            return Err(PyValueError::new_err(format!(
                "{function}: the parameter name {param_name} clashes with the attribute \
                 Expr.{param_name}"
            )));
        }
        if declared.iter().any(|earlier| earlier.name.bind(py).as_any().eq(param_name).is_ok_and(|same| same)) {
            return Err(PyValueError::new_err(format!(
                "{function} has two parameters named {param_name}"
            )));
        }
        if param.shape != Shape::One && std::mem::replace(&mut open, true) {
            return Err(PyTypeError::new_err(format!(
                "{function}: at most one parameter can be Many or ManyMixed, got {}",
                describe(params)
            )));
        }
        declared.push(param);
    }
    Bound::new(py, declare(py, name, declared.into_boxed_slice(), returns)?)
}

fn declare(
    py: Python<'_>,
    name: Py<PyString>,
    params: Box<[Param]>,
    returns: KindRef,
) -> PyResult<Expr> {
    let mut inputs = Vec::with_capacity(params.len());
    let mut bound = Vec::with_capacity(params.len());
    let (mut run, mut spread) = (None, None);
    let mut variables = Vec::new();
    let mut clash = Ok(());
    for param in params.iter() {
        match param.shape {
            Shape::Many => run = Some(inputs.len()),
            Shape::ManyMixed => spread = Some(inputs.len()),
            Shape::One => {}
        }
        clash = clash.and(collect_variables(param.kind, param.shape == Shape::ManyMixed, &mut variables));
        inputs.push(param.kind);
        bound.push(param.bound);
    }
    clash = clash.and(collect_variables(returns, false, &mut variables));
    if let Err(variable) = clash {
        return Err(PyTypeError::new_err(format!(
            "{}: {k} is used both as ManyMixed({k}) and on its own; ManyMixed({k}) gives each \
             argument its own {k}, so use a second kind variable for the other",
            name.bind(py),
            k = variable.name
        )));
    }
    let kind = function_kind(py, &inputs, run, spread, returns)?;
    let origin = (!variables.is_empty()).then(|| {
        Box::new(Origin::Generic {
            variables: variables.into_boxed_slice(),
            instances: Mutex::new(HashMap::new()),
        })
    });
    let bound = bound.contains(&true).then(|| bound.into_boxed_slice());
    Ok(Expr { kind, form: Form::Declared { name, params: Some(params), bound, origin } })
}

fn collect_variables(kind: KindRef, mixed: bool, variables: &mut Vec<Variable>) -> Result<(), KindRef> {
    if !kind.generic {
        return Ok(());
    }
    if kind.variable {
        return match variables.iter().find(|known| same_kind(known.kind, kind)) {
            Some(known) if known.mixed != mixed => Err(kind),
            Some(_) => Ok(()),
            None => {
                variables.push(Variable { kind, mixed });
                Ok(())
            }
        };
    }
    for (slot, &param) in kind.params.iter().enumerate() {
        collect_variables(param, kind.spread == Some(slot), variables)?;
    }
    if let Some(sig) = &kind.signature {
        for (slot, &input) in sig.inputs.iter().enumerate() {
            collect_variables(input, sig.spread == Some(slot), variables)?;
        }
        collect_variables(sig.output, false, variables)?;
    }
    Ok(())
}

enum Binding {
    One(KindRef),
    Mixed(Box<[KindRef]>),
}

impl Binding {
    fn same(&self, other: &Binding) -> bool {
        match (self, other) {
            (Binding::One(a), Binding::One(b)) => same_kind(a, b),
            (Binding::Mixed(a), Binding::Mixed(b)) => {
                a.len() == b.len() && a.iter().zip(b.iter()).all(|(&a, &b)| same_kind(a, b))
            }
            _ => false,
        }
    }

    fn name(&self) -> String {
        match self {
            Binding::One(kind) => kind.name.clone(),
            Binding::Mixed(kinds) => {
                let names: Vec<&str> = kinds.iter().map(|kind| kind.name.as_str()).collect();
                match names.len() {
                    1 => format!("({},)", names[0]),
                    _ => format!("({})", names.join(", ")),
                }
            }
        }
    }

    fn generic(&self) -> bool {
        match self {
            Binding::One(kind) => kind.generic,
            Binding::Mixed(kinds) => kinds.iter().any(|kind| kind.generic),
        }
    }
}

type Filling = Vec<(KindRef, Binding)>;

fn lookup(filling: &Filling, variable: KindRef) -> Option<&Binding> {
    filling.iter().find(|(known, _)| same_kind(known, variable)).map(|(_, binding)| binding)
}

enum Mismatch {
    Shape,
    Conflict(KindRef, String, String),
    Error(PyErr),
}

impl From<PyErr> for Mismatch {
    fn from(error: PyErr) -> Self {
        Mismatch::Error(error)
    }
}

fn bind(filling: &mut Filling, variable: KindRef, binding: Binding) -> Result<(), Mismatch> {
    match lookup(filling, variable) {
        Some(known) if known.same(&binding) => Ok(()),
        Some(known) => Err(Mismatch::Conflict(variable, known.name(), binding.name())),
        None => {
            filling.push((variable, binding));
            Ok(())
        }
    }
}

fn unify(param: KindRef, arg: KindRef, filling: &mut Filling) -> Result<(), Mismatch> {
    if param.variable {
        return bind(filling, param, Binding::One(arg));
    }
    if !param.generic {
        return if same_kind(param, arg) { Ok(()) } else { Err(Mismatch::Shape) };
    }
    if let (Some(family), Some(arg_family)) = (&param.family, &arg.family) {
        if family.is(arg_family) && arg.spread.is_none() {
            return unify_list(&param.params, param.spread, &arg.params, filling);
        }
    }
    if let (Some(sig), Some(arg_sig)) = (&param.signature, &arg.signature) {
        let same_shape = match sig.spread {
            Some(_) => arg_sig.open().is_none(),
            None => sig.run == arg_sig.run && arg_sig.spread.is_none(),
        };
        if !same_shape {
            return Err(Mismatch::Shape);
        }
        unify(sig.output, arg_sig.output, filling)?;
        return unify_list(&sig.inputs, sig.spread, &arg_sig.inputs, filling);
    }
    Err(Mismatch::Shape)
}

fn unify_list(
    params: &[KindRef],
    spread: Option<usize>,
    args: &[KindRef],
    filling: &mut Filling,
) -> Result<(), Mismatch> {
    let Some(spread) = spread else {
        if params.len() != args.len() {
            return Err(Mismatch::Shape);
        }
        for (&p, &a) in params.iter().zip(args.iter()) {
            unify(p, a, filling)?;
        }
        return Ok(());
    };
    let given = args.len();
    if given + 1 < params.len() {
        return Err(Mismatch::Shape);
    }
    for (slot, &kind) in params.iter().enumerate() {
        let positions = slot_positions(params.len(), Some(spread), slot, given);
        if slot == spread {
            bind(filling, kind, Binding::Mixed(args[positions].into()))?;
        } else {
            unify(kind, args[positions.start], filling)?;
        }
    }
    Ok(())
}

fn fill(py: Python<'_>, kind: KindRef, filling: &Filling) -> PyResult<KindRef> {
    if !kind.generic {
        return Ok(kind);
    }
    if kind.variable {
        return match lookup(filling, kind) {
            Some(Binding::One(filled)) => Ok(filled),
            _ => Err(PyTypeError::new_err(format!("{} is not filled", kind.name))),
        };
    }
    if let Some(family) = &kind.family {
        let params = fill_list(py, &kind.params, kind.spread, filling)?;
        return family_instance(family.bind(py), params, None);
    }
    let Some(sig) = &kind.signature else {
        return Ok(kind);
    };
    let inputs = fill_list(py, &sig.inputs, sig.spread, filling)?;
    function_kind(py, &inputs, sig.run, None, fill(py, sig.output, filling)?)
}

fn fill_list(
    py: Python<'_>,
    kinds: &[KindRef],
    spread: Option<usize>,
    filling: &Filling,
) -> PyResult<Vec<KindRef>> {
    let mut filled = Vec::with_capacity(kinds.len());
    for (slot, &kind) in kinds.iter().enumerate() {
        if spread != Some(slot) {
            filled.push(fill(py, kind, filling)?);
            continue;
        }
        let Some(Binding::Mixed(parts)) = lookup(filling, kind) else {
            return Err(PyTypeError::new_err(format!("ManyMixed({}) is not filled", kind.name)));
        };
        filled.extend_from_slice(parts);
    }
    Ok(filled)
}

fn concrete<'py>(generic: &Bound<'py, Expr>, filling: &Filling) -> PyResult<Bound<'py, Expr>> {
    let py = generic.py();
    let expr = generic.get();
    let (Form::Declared { name, bound, origin: Some(origin), .. }, Some(sig)) =
        (&expr.form, &expr.kind.signature)
    else {
        unreachable!("only a generic declared function is made concrete");
    };
    let Origin::Generic { variables, instances } = &**origin else {
        unreachable!("only a generic declared function is made concrete");
    };
    let mut key = Vec::with_capacity(variables.len());
    for variable in variables.iter() {
        match lookup(filling, variable.kind) {
            Some(Binding::One(kind)) => key.push(kind.id),
            Some(Binding::Mixed(kinds)) => {
                key.push(kinds.len());
                key.extend(kinds.iter().map(|kind| kind.id));
            }
            None => key.push(usize::MAX),
        }
    }
    let key = key.into_boxed_slice();
    let found = instances.lock_py_attached(py).unwrap_or_else(PoisonError::into_inner).get(&key).map(|e| e.clone_ref(py));
    if let Some(found) = found {
        return Ok(found.into_bound(py));
    }
    let kind = fill(py, expr.kind, filling)?;
    let bound = match bound {
        Some(bound) => {
            let mut filled = Vec::with_capacity(bound.len());
            for (slot, &only_symbol) in bound.iter().enumerate() {
                let width = match (sig.spread == Some(slot), lookup(filling, sig.inputs[slot])) {
                    (true, Some(Binding::Mixed(parts))) => parts.len(),
                    _ => 1,
                };
                filled.extend(std::iter::repeat_n(only_symbol, width));
            }
            Some(filled.into_boxed_slice())
        }
        None => None,
    };
    let origin = Some(Box::new(Origin::Concrete { generic: generic.clone().unbind() }));
    let made = Expr { kind, form: Form::Declared { name: name.clone_ref(py), params: None, bound, origin } };
    let made = Py::new(py, made)?;
    let mut table = instances.lock_py_attached(py).unwrap_or_else(PoisonError::into_inner);
    Ok(table.entry(key).or_insert(made).clone_ref(py).into_bound(py))
}

fn apply_generic<'py>(
    head: &Bound<'py, Expr>,
    variables: &[Variable],
    sig: &Signature,
    args: &Bound<'py, PyTuple>,
) -> PyResult<Bound<'py, Expr>> {
    let py = args.py();
    let expr = head.get();
    let given = args.len();
    let mut filling = Filling::new();
    for (slot, &expected) in sig.inputs.iter().enumerate() {
        if sig.spread == Some(slot) {
            let positions = sig.positions(slot, given);
            let mut parts = Vec::with_capacity(positions.len());
            for position in positions.clone() {
                let arg = args.get_item(position)?;
                parts.push(arg.cast_exact::<Expr>().ok().map(|arg| arg.get().kind));
            }
            let known = match lookup(&filling, expected) {
                Some(Binding::Mixed(known)) if known.len() != parts.len() => {
                    return Err(PyTypeError::new_err(format!(
                        "{}: {k} is {}, so ManyMixed({k}) takes {}, got {}",
                        expr.label(py)?,
                        Binding::Mixed(known.clone()).name(),
                        count(known.len(), "argument"),
                        parts.len(),
                        k = expected.name
                    )));
                }
                Some(Binding::Mixed(known)) => Some(known),
                _ => None,
            };
            let mut kinds = Vec::with_capacity(parts.len());
            for (position, part) in positions.zip(parts) {
                match (part, known) {
                    (Some(kind), _) => kinds.push(kind),
                    (None, Some(known)) => kinds.push(known[kinds.len()]),
                    (None, None) => {
                        return Err(PyTypeError::new_err(format!(
                            "{} cannot tell the kind of {}: a literal takes the kind of its \
                             position, and in ManyMixed({}) each position has its own kind",
                            expr.label(py)?,
                            args.get_item(position)?.repr()?,
                            expected.name
                        )));
                    }
                }
            }
            bind(&mut filling, expected, Binding::Mixed(kinds.into_boxed_slice()))
                .map_err(|m| mismatch(py, expr, expected, args, m))?;
            continue;
        }
        for position in sig.positions(slot, given) {
            let arg = args.get_item(position)?;
            if let Ok(arg_expr) = arg.cast_exact::<Expr>() {
                unify(expected, arg_expr.get().kind, &mut filling)
                    .map_err(|m| mismatch(py, expr, expected, &arg, m))?;
            }
        }
    }
    if let Some(missing) = variables.iter().find(|v| lookup(&filling, v.kind).is_none()) {
        return Err(PyTypeError::new_err(format!(
            "{label}: no argument fills {k}, since a literal has no kind of its own; \
             use concretize({label}, {{{k}: ...}})",
            label = expr.label(py)?,
            k = missing.kind.name
        )));
    }
    apply(&concrete(head, &filling)?, args)
}

fn mismatch(py: Python<'_>, head: &Expr, expected: KindRef, arg: &Bound<'_, PyAny>, m: Mismatch) -> PyErr {
    match m {
        Mismatch::Shape => wrong_kind(py, head, expected, arg),
        Mismatch::Conflict(variable, known, kind) => match head.label(py) {
            Ok(label) => PyTypeError::new_err(format!(
                "{label}: {} is {known} and {kind}",
                variable.name
            )),
            Err(error) => error,
        },
        Mismatch::Error(error) => error,
    }
}

#[pyfunction]
fn concretize<'py>(f: &Bound<'py, PyAny>, filling: &Bound<'py, PyDict>) -> PyResult<Bound<'py, Expr>> {
    let generic = f.cast_exact::<Expr>().ok().filter(|f| generic_variables(f.get()).is_some());
    let Some(generic) = generic else {
        return Err(PyTypeError::new_err(format!(
            "concretize expects a declared function with kind variables, got {}",
            describe(f)
        )));
    };
    let label = generic.get().label(f.py())?;
    let variables = generic_variables(generic.get()).unwrap_or_default();
    let mut given = Filling::new();
    for (key, value) in filling.iter() {
        let variable = expect_kind(&key)?;
        let Some(found) = variables.iter().find(|v| same_kind(v.kind, variable)) else {
            return Err(PyValueError::new_err(format!(
                "concretize: {} is not a kind variable of {label}",
                variable.name
            )));
        };
        let binding = match (found.mixed, value.cast_exact::<PyTuple>()) {
            (true, Ok(kinds)) => Binding::Mixed(kinds.iter().map(|kind| expect_kind(&kind)).collect::<PyResult<_>>()?),
            (false, Err(_)) => Binding::One(expect_kind(&value)?),
            (true, Err(_)) => {
                return Err(PyTypeError::new_err(format!(
                    "concretize: {label} has ManyMixed({k}), so {k} takes a tuple with a kind \
                     for each argument, got {}",
                    describe(&value),
                    k = variable.name
                )));
            }
            (false, Ok(_)) => {
                return Err(PyTypeError::new_err(format!(
                    "concretize: {k} stands for one kind in {label}, got {}; \
                     a tuple of kinds fills only a variable used as ManyMixed({k})",
                    describe(&value),
                    k = variable.name
                )));
            }
        };
        if binding.generic() {
            return Err(PyValueError::new_err(format!(
                "concretize: {} must be filled with kinds without kind variables, got {}",
                variable.name,
                binding.name()
            )));
        }
        given.push((variable, binding));
    }
    if let Some(missing) = variables.iter().find(|v| lookup(&given, v.kind).is_none()) {
        return Err(PyValueError::new_err(format!(
            "concretize: {label} needs a kind for {}",
            missing.kind.name
        )));
    }
    concrete(generic, &given)
}

#[pyfunction]
fn generic_of(py: Python<'_>, f: &Bound<'_, PyAny>) -> Option<Py<Expr>> {
    let f = f.cast_exact::<Expr>().ok()?;
    match &f.get().form {
        Form::Declared { origin: Some(origin), .. } => match &**origin {
            Origin::Concrete { generic } => Some(generic.clone_ref(py)),
            Origin::Generic { .. } => None,
        },
        _ => None,
    }
}

#[pyfunction]
fn declare_constant<'py>(
    py: Python<'py>,
    name: Py<PyString>,
    kind: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, Expr>> {
    let kind = expect_kind(kind)?;
    let form = Form::Declared { name, params: None, bound: None, origin: None };
    Bound::new(py, Expr { kind, form })
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
    m.add_class::<ManyMixed>()?;
    m.add_function(wrap_pyfunction!(kind_variable, m)?)?;
    m.add_function(wrap_pyfunction!(concretize, m)?)?;
    m.add_function(wrap_pyfunction!(generic_of, m)?)?;
    m.add_function(wrap_pyfunction!(declare_kind, m)?)?;
    m.add_function(wrap_pyfunction!(declare_kind_family, m)?)?;
    m.add_function(wrap_pyfunction!(function_kind_py, m)?)?;
    m.add_function(wrap_pyfunction!(declare_function, m)?)?;
    m.add_function(wrap_pyfunction!(declare_constant, m)?)?;
    m.add_function(wrap_pyfunction!(set_operator, m)?)?;
    Ok(())
}

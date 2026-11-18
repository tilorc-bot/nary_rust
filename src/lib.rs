//! Typed, inert expression trees for Python, written in Rust.
//!
//! `Expr` is the only class of expression, and every expression is one of
//! three forms: a symbol, a declared function, or an application of a head
//! expression to arguments. Each expression has a kind. A kind is an object
//! declared from Python with `declare_kind(name)`, or made by instantiating
//! a kind family declared with `declare_kind_family(name)`:
//! `TupleKind(NumberKind, BoolKind)`.
//!
//! The one kind defined here is the function kind,
//! `FunctionKind(inputs, output, rest=None)`, because application is checked
//! against it: calling an expression of a function kind checks the arguments
//! against the inputs and builds an application whose kind is the output. A
//! declared function is a named constant of a function kind, and a leading
//! position of it can be declared `Symbol(kind)` to accept only a symbol. The
//! checking and node construction happen here.
//!
//! No other kind and no particular function is defined in this file. The
//! kinds (NumberKind, BoolKind), the functions (Add, Mul, Eq and the rest)
//! and Lambda are declared in Python, in the package `nary`, and each kind is
//! told what an operator builds with `set_operator`.

use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{LazyLock, Mutex, PoisonError};

use pyo3::exceptions::{PyAttributeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::pyclass::CompareOp;
use pyo3::sync::{MutexExt, PyOnceLock};
use pyo3::types::{PyString, PyTuple};

/// What is known about a kind.
///
/// One of these is made for each `declare_kind(name)` call, for each
/// different list of parameters a kind family is instantiated with, and for
/// each different function kind, and is never freed. So an expression
/// refers to its kind with a plain reference: building a node does no
/// reference counting on the kind, and two kinds are the same kind exactly
/// when the references are the same.
struct KindData {
    /// The position of the kind in the order of declaration. Used in hashes.
    id: usize,
    name: String,
    /// The Python object for this kind. Set when the kind is made.
    object: PyOnceLock<Py<Kind>>,
    /// The function each operator calls for this kind, indexed by
    /// `Operator`. Filled in from Python with `set_operator`.
    operators: [PyOnceLock<Py<PyAny>>; Operator::COUNT],
    /// The family this kind is an instance of, or None for a kind declared
    /// with `declare_kind(name)` and for a function kind.
    family: Option<Py<KindFamily>>,
    /// The parameters the family was instantiated with. Empty for a kind
    /// declared with `declare_kind(name)` and for a function kind.
    params: Box<[KindRef]>,
    /// For a function kind, what it accepts and returns. None for any
    /// other kind.
    signature: Option<Signature>,
}

/// The inputs, further arguments and output of a function kind.
struct Signature {
    inputs: Box<[KindRef]>,
    /// The kind of any number of further arguments, or None.
    rest: Option<KindRef>,
    output: KindRef,
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
) -> KindRef {
    Box::leak(Box::new(KindData {
        id: KIND_COUNT.fetch_add(1, Ordering::Relaxed),
        name,
        object: PyOnceLock::new(),
        operators: [const { PyOnceLock::new() }; Operator::COUNT],
        family,
        params,
        signature,
    }))
}

/// The Python object of a kind, made the first time it is asked for.
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

/// A kind of expression, such as NumberKind. Declared with
/// `declare_kind(name)`, made by instantiating a kind family,
/// `TupleKind(NumberKind, BoolKind)`, or a function kind,
/// `FunctionKind((NumberKind,), NumberKind)`.
///
/// Calling a kind with a name makes a symbol of that kind: `NumberKind("x")`.
#[pyclass(frozen, module = "nary")]
struct Kind {
    data: KindRef,
}

#[pymethods]
impl Kind {
    /// `NumberKind("x")` is a symbol named x of this kind. The name is the
    /// only argument accepted: any other is a TypeError. A node with
    /// arguments is built only by calling an expression of a function kind,
    /// so every argument of every node has passed a kind check.
    #[pyo3(signature = (head, *extra))]
    fn __call__(
        &self,
        py: Python<'_>,
        head: Py<PyString>,
        extra: &Bound<'_, PyTuple>,
    ) -> PyResult<Py<Expr>> {
        if !extra.is_empty() {
            return Err(PyTypeError::new_err(format!(
                "{} takes 1 argument, the name of a leaf, got {}; \
                 a node is built by calling a function",
                self.data.name,
                extra.len() + 1
            )));
        }
        Py::new(py, Expr { kind: self.data, form: Form::Symbol { name: head } })
    }

    #[getter]
    fn name(&self) -> &str {
        &self.data.name
    }

    fn __repr__(&self) -> &str {
        &self.data.name
    }

    /// The family this kind is an instance of, or None.
    #[getter]
    fn family(&self, py: Python<'_>) -> Option<Py<KindFamily>> {
        self.data.family.as_ref().map(|family| family.clone_ref(py))
    }

    /// The parameters of this kind: `TupleKind(NumberKind, BoolKind).params` is
    /// `(NumberKind, BoolKind)`. Empty for a kind declared with
    /// `declare_kind(name)`.
    #[getter]
    fn params<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        kind_tuple(py, &self.data.params)
    }

    /// The kinds of the leading arguments of a function kind, or None for
    /// any other kind.
    #[getter]
    fn inputs<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyTuple>>> {
        self.data.signature.as_ref().map(|sig| kind_tuple(py, &sig.inputs)).transpose()
    }

    /// The kind of any further arguments of a function kind, or None.
    #[getter]
    fn rest(&self, py: Python<'_>) -> PyResult<Option<Py<Kind>>> {
        match &self.data.signature {
            Some(Signature { rest: Some(rest), .. }) => Ok(Some(kind_object(py, rest)?)),
            _ => Ok(None),
        }
    }

    /// The kind of the result of a function kind, or None for any other
    /// kind.
    #[getter]
    fn output(&self, py: Python<'_>) -> PyResult<Option<Py<Kind>>> {
        self.data.signature.as_ref().map(|sig| kind_object(py, sig.output)).transpose()
    }
}

/// Declare a kind: `NumberKind = declare_kind("NumberKind")`.
///
/// Every call makes a new kind, different from every other, and a kind
/// lasts for the life of the process. Declare each kind once, when a module
/// is imported.
#[pyfunction]
fn declare_kind(py: Python<'_>, name: String) -> PyResult<Py<Kind>> {
    kind_object(py, new_kind_data(name, None, Box::new([]), None))
}

/// The function kinds made so far. The key is the id of the output, the id
/// of the rest kind (or `usize::MAX` for none), then the ids of the inputs.
static FUNCTION_KINDS: LazyLock<Mutex<HashMap<Box<[usize]>, KindRef>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

fn function_kind_name(inputs: &[KindRef], rest: Option<KindRef>, output: KindRef) -> String {
    let names: Vec<&str> = inputs.iter().map(|kind| kind.name.as_str()).collect();
    let inputs = match names.len() {
        1 => format!("({},)", names[0]),
        _ => format!("({})", names.join(", ")),
    };
    match rest {
        Some(rest) => format!("FunctionKind({inputs}, {}, rest={})", output.name, rest.name),
        None => format!("FunctionKind({inputs}, {})", output.name),
    }
}

/// The function kind with these inputs, rest and output: made the first
/// time, and the same record every time after.
fn function_kind(
    py: Python<'_>,
    inputs: &[KindRef],
    rest: Option<KindRef>,
    output: KindRef,
) -> PyResult<KindRef> {
    let mut key = Vec::with_capacity(inputs.len() + 2);
    key.push(output.id);
    key.push(rest.map_or(usize::MAX, |kind| kind.id));
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
                    function_kind_name(inputs, rest, output),
                    None,
                    Box::new([]),
                    Some(Signature { inputs: inputs.into(), rest, output }),
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

/// The kind of a function: `FunctionKind((NumberKind, NumberKind), BoolKind)`
/// takes two NumberKinds and returns a BoolKind, and
/// `FunctionKind((), NumberKind, rest=NumberKind)` takes any number of
/// NumberKinds.
///
/// The same arguments always give the same kind.
#[pyfunction(name = "FunctionKind")]
#[pyo3(signature = (inputs, output, rest=None))]
fn function_kind_py(
    py: Python<'_>,
    inputs: &Bound<'_, PyAny>,
    output: &Bound<'_, PyAny>,
    rest: Option<&Bound<'_, PyAny>>,
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
    let rest = rest.map(expect_kind).transpose()?;
    kind_object(py, function_kind(py, &kinds, rest, output)?)
}

/// A family of kinds, each given by a list of parameters that are kinds.
/// Declared with `declare_kind_family(name, params=None)`.
///
/// `TupleKind(NumberKind, BoolKind)` is the kind of the family with those
/// parameters. It is made the first time and the same kind is returned every
/// time after, so two kinds of a family are the same kind exactly when their
/// parameters are the same kinds in the same order.
#[pyclass(frozen, module = "nary")]
struct KindFamily {
    name: String,
    /// The number of parameters every kind of the family has, or None for
    /// any number from one up.
    params: Option<usize>,
    /// The kinds made so far, by the ids of their parameters. Only looked at
    /// when the family is instantiated.
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
                )
            })
        };
        kind_object(py, data)
    }

    #[getter]
    fn name(&self) -> &str {
        &self.name
    }

    /// The number of parameters, or None if any number from one up is
    /// accepted.
    #[getter]
    fn params(&self) -> Option<usize> {
        self.params
    }

    fn __repr__(&self) -> String {
        format!("<kind family {}>", self.name)
    }
}

/// Declare a kind family: `TupleKind = declare_kind_family("TupleKind")`
/// takes any number of parameters from one up, and
/// `MatrixKind = declare_kind_family("MatrixKind", params=1)` takes exactly
/// one.
///
/// Every call makes a new family, and the kinds of a family last for the
/// life of the process. Declare each family once, when a module is imported.
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

/// In a declaration, `Symbol(NumberKind)` is a leading position of kind
/// NumberKind that accepts only a symbol, not any expression of that kind.
/// It is a marker, not a kind: the function kind is built from the plain
/// kinds.
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

/// An expression, of some kind.
///
/// A symbol is made by calling a kind and a declared function by
/// `declare_function`. An application is made only by `apply`, which checks
/// that each argument is an `Expr` of the kind the head's function kind
/// expects.
/// Nothing else makes an `Expr`.
#[pyclass(frozen, module = "nary")]
struct Expr {
    kind: KindRef,
    form: Form,
}

enum Form {
    /// `NumberKind("x")`.
    Symbol { name: Py<PyString> },
    /// An opaque named constant of a function kind, made by
    /// `declare_function`. Equal only to itself.
    Declared {
        name: Py<PyString>,
        /// Names for the leading arguments of its applications.
        names: Option<Py<PyTuple>>,
        /// For each leading position, whether it was declared
        /// `Symbol(kind)` and so accepts only a symbol. None when no
        /// position was.
        symbols: Option<Box<[bool]>>,
    },
    /// A head of a function kind applied to arguments.
    Apply { head: Py<Expr>, args: Py<PyTuple> },
}

impl Expr {
    /// The name of a symbol or declared function.
    fn plain_name(&self) -> Option<&Py<PyString>> {
        match &self.form {
            Form::Symbol { name } | Form::Declared { name, .. } => Some(name),
            _ => None,
        }
    }

    /// How a head is named in an error: its name, or else its repr.
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
        (Form::Apply { head: h1, args: a1 }, Form::Apply { head: h2, args: a2 }) => {
            structural_eq(py, h1.get(), h2.get())? && a1.bind(py).as_any().eq(a2.bind(py))?
        }
        // Declared functions are equal only when identical, checked above,
        // and different forms are never equal.
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

/// Combine the hashes of the parts of an expression into one hash.
fn combine_hashes(parts: [usize; 3]) -> isize {
    const MULTIPLIER: u64 = 0x9E37_79B9_7F4A_7C15;
    let mut hash = MULTIPLIER;
    for part in parts {
        hash = (hash ^ part as u64).wrapping_mul(MULTIPLIER);
        hash ^= hash >> 32;
    }
    hash as isize
}

/// A hash that agrees with `structural_eq`. The first part tells the forms
/// apart.
fn expr_hash(py: Python<'_>, e: &Expr) -> PyResult<isize> {
    let parts = match &e.form {
        Form::Symbol { name } => [0, e.kind.id, name.bind(py).hash()? as usize],
        // Equal only to itself, so hashed by address.
        Form::Declared { .. } => [1, e.kind.id, e as *const Expr as usize],
        Form::Apply { head, args } => {
            [2, expr_hash(py, head.get())? as usize, args.bind(py).hash()? as usize]
        }
    };
    Ok(combine_hashes(parts))
}

fn wrong_kind(py: Python<'_>, head: &Expr, expected: KindRef, arg: &Bound<'_, PyAny>) -> PyErr {
    let text = (|| -> PyResult<String> {
        // An expression is described by its kind, anything else by its type.
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

/// Check that each leading argument at a position declared `Symbol(kind)` is
/// a symbol. Called after the kind check, so every argument is an `Expr` of
/// the right kind.
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

/// Apply `head` to `args`: check them against the head's function kind (and,
/// for a declared function, its `Symbol(kind)` positions) and build the
/// application node, of the kind's output.
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
    let fixed = sig.inputs.len();
    let given = args.len();
    if given < fixed || (sig.rest.is_none() && given > fixed) {
        let expected = if sig.rest.is_some() {
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
    for (position, arg) in args.iter_borrowed().enumerate() {
        let expected = match sig.inputs.get(position) {
            Some(&kind) => kind,
            None => sig.rest.unwrap(),
        };
        let matches = arg
            .cast_exact::<Expr>()
            .is_ok_and(|arg| same_kind(arg.get().kind, expected));
        if !matches {
            return Err(wrong_kind(py, expr, expected, &arg));
        }
    }
    if let Form::Declared { symbols: Some(symbols), .. } = &expr.form {
        check_symbols(py, expr, &sig.inputs, symbols, args)?;
    }
    Bound::new(
        py,
        Expr {
            kind: sig.output,
            form: Form::Apply { head: head.clone().unbind(), args: args.clone().unbind() },
        },
    )
}

/// The operators. For each kind, each builds whatever was registered for it
/// with `set_operator`. `Neg` is unary minus, spelled "neg".
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

/// Call `function`, given to `set_operator` for `operator` on `kind`, with
/// `operands`. The result must be an expression.
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

/// What `operator` builds for the kind of `left`, from `left` and `right`.
/// If the kind has nothing for the operator, the result is NotImplemented,
/// as for any Python object that does not support an operator.
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

#[pymethods]
impl Expr {
    /// Apply this expression, which must be of a function kind, to
    /// arguments: `sin(x)`, `f(x)`, `g(sin)(x)`.
    #[pyo3(signature = (*args))]
    fn __call__<'py>(slf: &Bound<'py, Self>, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, Expr>> {
        apply(slf, args)
    }

    /// The kind of this expression: `e.kind is NumberKind`.
    #[getter]
    fn kind(&self, py: Python<'_>) -> Option<Py<Kind>> {
        self.kind.object.get(py).map(|kind| kind.clone_ref(py))
    }

    /// The head expression of an application, or None.
    #[getter]
    fn head(&self, py: Python<'_>) -> Option<Py<Expr>> {
        match &self.form {
            Form::Apply { head, .. } => Some(head.clone_ref(py)),
            _ => None,
        }
    }

    /// The arguments of an application, or `()`.
    #[getter]
    fn args<'py>(&self, py: Python<'py>) -> Bound<'py, PyTuple> {
        match &self.form {
            Form::Apply { args, .. } => args.bind(py).clone(),
            _ => PyTuple::empty(py),
        }
    }

    /// The name of a symbol or declared function, or None.
    #[getter]
    fn name(&self, py: Python<'_>) -> Option<Py<PyString>> {
        self.plain_name().map(|name| name.clone_ref(py))
    }

    /// The argument names of a declared function, or `()`.
    #[getter]
    fn names<'py>(&self, py: Python<'py>) -> Bound<'py, PyTuple> {
        match &self.form {
            Form::Declared { names: Some(names), .. } => names.bind(py).clone(),
            _ => PyTuple::empty(py),
        }
    }

    /// What a declared function was declared with: for each leading
    /// position, its kind or a `Symbol(kind)` marker. None for any other
    /// expression.
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

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        match &self.form {
            Form::Symbol { name } | Form::Declared { name, .. } => Ok(name.bind(py).to_string()),
            Form::Apply { head, args } => {
                let head = head.get();
                let args = args.bind(py);
                let head = match head.plain_name() {
                    // A named head applied to nothing prints as its name.
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

    fn __sub__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Sub)
    }

    fn __mul__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Mul)
    }

    fn __truediv__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Div)
    }

    fn __pow__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        modulo: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        if !modulo.is_none() {
            return Err(PyTypeError::new_err("pow() with a modulus is not supported"));
        }
        binary(slf, other, Operator::Pow)
    }

    /// Unary minus, `-x`: what the "neg" operator builds for the kind.
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

    /// Named arguments such as `eq.lhs`, declared with `names=(...)` on the
    /// head of an application.
    fn __getattr__(&self, py: Python<'_>, name: &Bound<'_, PyString>) -> PyResult<Py<PyAny>> {
        if let Form::Apply { head, args } = &self.form {
            if let Form::Declared { names: Some(names), .. } = &head.get().form {
                for (index, declared) in names.bind(py).iter().enumerate() {
                    if declared.eq(name)? {
                        return Ok(args.bind(py).get_item(index)?.unbind());
                    }
                }
            }
        }
        Err(PyAttributeError::new_err(format!(
            "'Expr' object has no attribute '{name}'"
        )))
    }
}

/// Declare a function: a new named constant of the function kind
/// `FunctionKind(arg_kinds, returns, rest=rest)`.
///
/// `arg_kinds` are the leading positions. Each is a kind, or `Symbol(kind)`
/// for a position of that kind that accepts only a symbol; the function
/// kind is built from the plain kinds, and `f.params` shows the markers. If
/// `rest` (a kind) is given, any number of further arguments of that kind
/// are accepted. The result is always of the kind `returns`. `names` gives
/// attribute names for the leading arguments, so that `names=("lhs", "rhs")`
/// makes `.lhs` and `.rhs` available on an application. Every call makes a
/// different function.
#[pyfunction]
#[pyo3(signature = (name, *arg_kinds, rest=None, returns, names=None))]
fn declare_function<'py>(
    py: Python<'py>,
    name: Py<PyString>,
    arg_kinds: &Bound<'py, PyTuple>,
    rest: Option<&Bound<'py, PyAny>>,
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
                kinds.push(marker.get().kind);
                symbols.push(true);
            }
            Err(_) => {
                kinds.push(expect_kind(&param)?);
                symbols.push(false);
            }
        }
    }
    // A function with no Symbol(kind) position stores no flags, so applying
    // it costs one test more than before.
    let symbols = symbols.contains(&true).then(|| symbols.into_boxed_slice());
    let rest = rest.map(expect_kind).transpose()?;
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
    let kind = function_kind(py, &kinds, rest, returns)?;
    Bound::new(py, Expr { kind, form: Form::Declared { name, names, symbols } })
}

/// Say what an operator builds for a kind:
/// `set_operator(NumberKind, "+", Add)`. The operators are "+", "-", "*",
/// "/", "**", "neg" (unary minus), "<", ">", "<=" and ">=".
///
/// The operator calls `function` with the operands, and the result must be
/// an expression. Each operator can be set once for each kind. A kind with
/// nothing set for an operator does not support it.
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
    m.add_class::<SymbolMarker>()?;
    m.add_function(wrap_pyfunction!(declare_kind, m)?)?;
    m.add_function(wrap_pyfunction!(declare_kind_family, m)?)?;
    m.add_function(wrap_pyfunction!(function_kind_py, m)?)?;
    m.add_function(wrap_pyfunction!(declare_function, m)?)?;
    m.add_function(wrap_pyfunction!(set_operator, m)?)?;
    Ok(())
}

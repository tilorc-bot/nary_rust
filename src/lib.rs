//! Typed, inert expression trees for Python, written in Rust.
//!
//! `Expr` is the only class of expression: a symbol, an integer, or a head
//! applied to arguments. Each expression has a kind. A kind is an object
//! declared from Python with `kind(name)`, or made by instantiating a kind
//! family declared with `kind_family(name)`: `MatrixKind(NumberKind)`. A
//! function declares the kinds it accepts and the kind it returns, with
//! optional names for its arguments. The checking and node construction
//! happen here.
//!
//! No kind, no family and no particular function is defined in this file.
//! The kinds (NumberKind, BoolKind), the families (SetKind, MatrixKind) and
//! the functions (Add, Mul, Eq and the rest) are declared in Python
//! (python/nary/). Python also says which function an operator builds for
//! each kind, with `set_operator`, and which kind an integer is, with
//! `set_integer_kind`.

use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Mutex, PoisonError};

use pyo3::exceptions::{PyAttributeError, PyTypeError, PyValueError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pyclass::CompareOp;
use pyo3::sync::{MutexExt, PyOnceLock};
use pyo3::types::{PyDict, PyInt, PyString, PyTuple};

/// What is known about a kind.
///
/// One of these is made for each `kind(name)` call, and for each different
/// list of parameters a kind family is instantiated with, and is never
/// freed. So an expression refers to its kind with a plain reference:
/// building a node does no reference counting on the kind, and two kinds are
/// the same kind exactly when the references are the same.
///
// TODO: the package declares no tuple kind and no function kind. Anything
// that needs one is left out: Lambda, passing an undefined function itself
// as an argument, and derivatives written as operators. Grouped arguments
// are written flat instead (see `rest` groups and the binders declared in
// Python).
struct KindData {
    /// The position of the kind in the order of declaration. Used in hashes.
    id: usize,
    name: String,
    /// The Python object for this kind, made the first time it is asked for.
    object: PyOnceLock<Py<Kind>>,
    /// The function each operator builds for this kind, indexed by
    /// `Operator`. Filled in from Python with `set_operator`.
    operators: [PyOnceLock<Py<Function>>; Operator::COUNT],
    /// The family this kind is an instance of, or None for a kind declared
    /// with `kind(name)`.
    family: Option<Py<KindFamily>>,
    /// The parameters the family was instantiated with. Empty for a kind
    /// declared with `kind(name)`.
    params: Box<[KindRef]>,
}

type KindRef = &'static KindData;

fn same_kind(a: KindRef, b: KindRef) -> bool {
    std::ptr::eq(a, b)
}

static KIND_COUNT: AtomicUsize = AtomicUsize::new(0);

/// Make the record for a new kind. It is never freed.
fn new_kind_data(name: String, family: Option<Py<KindFamily>>, params: Box<[KindRef]>) -> KindRef {
    Box::leak(Box::new(KindData {
        id: KIND_COUNT.fetch_add(1, Ordering::Relaxed),
        name,
        object: PyOnceLock::new(),
        operators: [const { PyOnceLock::new() }; Operator::COUNT],
        family,
        params,
    }))
}

/// The Python object of a kind, made the first time it is asked for.
fn kind_object(py: Python<'_>, data: KindRef) -> PyResult<Py<Kind>> {
    let object = data.object.get_or_try_init(py, || Py::new(py, Kind { data }))?;
    Ok(object.clone_ref(py))
}

/// The kind of an integer, declared from Python with `set_integer_kind`.
static INTEGER_KIND: PyOnceLock<KindRef> = PyOnceLock::new();

const NO_INTEGER_KIND: &str =
    "no kind has been declared for integers: call set_integer_kind(kind)";

/// A kind of expression, such as NumberKind. Declared with `kind(name)`, or
/// made by instantiating a kind family: `MatrixKind(NumberKind)`.
///
/// Calling a kind with a name makes a symbol of that kind: `NumberKind("x")`.
#[pyclass(frozen, module = "nary")]
struct Kind {
    data: KindRef,
}

#[pymethods]
impl Kind {
    /// `NumberKind("x")` is a symbol named x of this kind, a leaf with no
    /// arguments. The name is the only argument accepted: any other is a
    /// TypeError. A node with arguments is built only by calling a declared
    /// function, so every argument of every node has passed a kind check.
    #[pyo3(signature = (name, *extra))]
    fn __call__(
        &self,
        py: Python<'_>,
        name: Py<PyString>,
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
        Py::new(
            py,
            Expr {
                kind: self.data,
                form: Form::Symbol,
                head: name,
                args: PyTuple::empty(py).unbind(),
                names: None,
            },
        )
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

    /// The parameters of this kind: `MatrixKind(NumberKind).params` is
    /// `(NumberKind,)`. Empty for a kind declared with `kind(name)`.
    #[getter]
    fn params<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        let mut params = Vec::with_capacity(self.data.params.len());
        for &param in self.data.params.iter() {
            params.push(kind_object(py, param)?);
        }
        PyTuple::new(py, params)
    }
}

/// Declare a kind: `NumberKind = kind("NumberKind")`.
///
/// Every call makes a new kind, different from every other, and a kind
/// lasts for the life of the process. Declare each kind once, when a module
/// is imported.
#[pyfunction(name = "kind")]
fn declare_kind(py: Python<'_>, name: String) -> PyResult<Py<Kind>> {
    kind_object(py, new_kind_data(name, None, Box::new([])))
}

/// A family of kinds, each given by a list of parameters that are kinds.
/// Declared with `kind_family(name, params=None)`.
///
/// `MatrixKind(NumberKind)` is the kind of the family with that parameter.
/// It is made the first time and the same kind is returned every time after,
/// so two kinds of a family are the same kind exactly when their parameters
/// are the same kinds in the same order.
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

/// `count(1, "argument")` is "1 argument", `count(2, "argument")` is
/// "2 arguments".
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

/// Declare a kind family: `TupleKind = kind_family("TupleKind")` takes any
/// number of parameters from one up, and
/// `MatrixKind = kind_family("MatrixKind", params=1)` takes exactly one.
///
/// Every call makes a new family, and the kinds of a family last for the
/// life of the process. Declare each family once, when a module is imported.
#[pyfunction]
#[pyo3(signature = (name, params=None))]
fn kind_family(name: String, params: Option<isize>) -> PyResult<KindFamily> {
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

/// What an expression is, apart from its kind.
enum Form {
    /// A function applied to arguments, possibly none (a constant such as pi).
    Apply,
    /// A symbol. `head` is its name.
    Symbol,
    /// An integer. `head` is "Integer" and the value is held here.
    Integer(Py<PyInt>),
}

impl Form {
    fn tag(&self) -> usize {
        match self {
            Form::Apply => 0,
            Form::Symbol => 1,
            Form::Integer(_) => 2,
        }
    }
}

/// An expression: a symbol, an integer, or a head applied to arguments.
///
/// A symbol, made by calling a kind, and an integer have no arguments. Any
/// other expression is made by `Function::apply`, which checks that each
/// argument is an `Expr` of the kind declared for it, converting a Python
/// int where integers are expected. Nothing else makes an `Expr`.
#[pyclass(frozen, module = "nary")]
struct Expr {
    kind: KindRef,
    form: Form,
    // TODO: a head is a bare string. Two functions declared with the same
    // name in different modules build equal nodes, and a node cannot be
    // traced back to the function that built it. Heads need a namespace or
    // an identity before the set of declared functions grows.
    head: Py<PyString>,
    args: Py<PyTuple>,
    /// Names for the leading arguments, shared with the declaring function.
    names: Option<Py<PyTuple>>,
}

fn integer_expr(kind: KindRef, value: &Bound<'_, PyInt>) -> Expr {
    let py = value.py();
    Expr {
        kind,
        form: Form::Integer(value.clone().unbind()),
        head: intern!(py, "Integer").clone().unbind(),
        args: PyTuple::empty(py).unbind(),
        names: None,
    }
}

/// `obj` as a Python int, if it is exactly an int. A bool is not accepted.
fn exact_int<'a, 'py>(obj: &'a Bound<'py, PyAny>) -> Option<&'a Bound<'py, PyInt>> {
    obj.cast_exact::<PyInt>().ok()
}

fn structural_eq(a: &Expr, b: &Expr, py: Python<'_>) -> PyResult<bool> {
    if !same_kind(a.kind, b.kind) {
        return Ok(false);
    }
    match (&a.form, &b.form) {
        (Form::Integer(x), Form::Integer(y)) => x.bind(py).as_any().eq(y.bind(py)),
        (Form::Apply, Form::Apply) | (Form::Symbol, Form::Symbol) => {
            Ok(a.head.bind(py).as_any().eq(b.head.bind(py))?
                && a.args.bind(py).as_any().eq(b.args.bind(py))?)
        }
        _ => Ok(false),
    }
}

fn compare(slf: &Expr, other: &Bound<'_, PyAny>, op: CompareOp) -> PyResult<Py<PyAny>> {
    let py = other.py();
    let equal = match other.cast_exact::<Expr>() {
        Ok(other) => structural_eq(slf, other.get(), py)?,
        Err(_) => return Ok(py.NotImplemented()),
    };
    Ok(match op {
        CompareOp::Eq => equal.into_pyobject(py)?.to_owned().into_any().unbind(),
        CompareOp::Ne => (!equal).into_pyobject(py)?.to_owned().into_any().unbind(),
        _ => py.NotImplemented(),
    })
}

/// Combine the hashes of the parts of an expression into one hash.
fn combine_hashes(parts: &[usize]) -> isize {
    const MULTIPLIER: u64 = 0x9E37_79B9_7F4A_7C15;
    let mut hash = MULTIPLIER;
    for part in parts {
        hash = (hash ^ *part as u64).wrapping_mul(MULTIPLIER);
        hash ^= hash >> 32;
    }
    hash as isize
}

/// The operators. For each kind, each builds whichever function was
/// registered for it with `set_operator`.
///
// TODO: there is no `-` or `/`. An inert tree has to choose between separate
// Sub and Div heads and spellings such as Add(x, Mul(-1, y)) and
// Mul(x, Pow(y, -1)), and that has not been decided.
#[derive(Clone, Copy)]
enum Operator {
    Add,
    Mul,
    Pow,
    Lt,
    Gt,
    Le,
    Ge,
}

impl Operator {
    const COUNT: usize = 7;
    const ALL: [Operator; Operator::COUNT] = [
        Operator::Add,
        Operator::Mul,
        Operator::Pow,
        Operator::Lt,
        Operator::Gt,
        Operator::Le,
        Operator::Ge,
    ];

    fn symbol(self) -> &'static str {
        match self {
            Operator::Add => "+",
            Operator::Mul => "*",
            Operator::Pow => "**",
            Operator::Lt => "<",
            Operator::Gt => ">",
            Operator::Le => "<=",
            Operator::Ge => ">=",
        }
    }
}

/// The function registered for `operator` on the kind of `owner`, applied to
/// `lhs` and `rhs`. `owner` is the left operand, or the right one for a
/// reflected operator. If the kind has no function for the operator, the
/// result is NotImplemented, as for any Python object that does not support
/// an operator.
// Inlined into each operator method. As a separate function it measurably
// slows `x + y` and `x < y`.
#[inline(always)]
fn binary<'py>(
    owner: &Bound<'py, Expr>,
    lhs: &Bound<'py, PyAny>,
    rhs: &Bound<'py, PyAny>,
    operator: Operator,
) -> PyResult<Bound<'py, PyAny>> {
    let py = owner.py();
    match owner.get().kind.operators[operator as usize].get(py) {
        Some(function) => {
            let args = PyTuple::new(py, [lhs, rhs])?;
            Ok(function.get().apply(&args)?.into_any())
        }
        None => Ok(py.NotImplemented().into_bound(py)),
    }
}

fn power<'py>(
    owner: &Bound<'py, Expr>,
    base: &Bound<'py, PyAny>,
    exponent: &Bound<'py, PyAny>,
    modulo: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let py = owner.py();
    if owner.get().kind.operators[Operator::Pow as usize].get(py).is_none() {
        return Ok(py.NotImplemented().into_bound(py));
    }
    if !modulo.is_none() {
        return Err(PyTypeError::new_err("pow() with a modulus is not supported"));
    }
    binary(owner, base, exponent, Operator::Pow)
}

#[pymethods]
impl Expr {
    /// The kind of this expression: `e.kind is NumberKind`.
    #[getter]
    fn kind(&self, py: Python<'_>) -> PyResult<Py<Kind>> {
        kind_object(py, self.kind)
    }

    /// The name of the function that built this node. For a symbol it is the
    /// symbol's name, and for an integer it is "Integer".
    #[getter]
    fn head(&self, py: Python<'_>) -> Py<PyString> {
        self.head.clone_ref(py)
    }

    #[getter]
    fn args(&self, py: Python<'_>) -> Py<PyTuple> {
        self.args.clone_ref(py)
    }

    /// True for a symbol. A constant such as pi is not a symbol.
    #[getter]
    fn is_symbol(&self) -> bool {
        matches!(self.form, Form::Symbol)
    }

    #[getter]
    fn is_integer(&self) -> bool {
        matches!(self.form, Form::Integer(_))
    }

    /// The Python int held by an integer, and None for anything else.
    #[getter]
    fn value(&self, py: Python<'_>) -> Option<Py<PyInt>> {
        match &self.form {
            Form::Integer(value) => Some(value.clone_ref(py)),
            _ => None,
        }
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        if let Form::Integer(value) = &self.form {
            return Ok(value.bind(py).str()?.to_string());
        }
        let head = self.head.bind(py).to_string();
        let args = self.args.bind(py);
        if args.is_empty() {
            return Ok(head);
        }
        let mut parts = Vec::with_capacity(args.len());
        for arg in args.iter() {
            parts.push(arg.repr()?.to_string());
        }
        Ok(format!("{}({})", head, parts.join(", ")))
    }

    fn __add__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, slf.as_any(), other, Operator::Add)
    }

    fn __radd__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, slf.as_any(), Operator::Add)
    }

    fn __mul__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, slf.as_any(), other, Operator::Mul)
    }

    fn __rmul__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, slf.as_any(), Operator::Mul)
    }

    fn __pow__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        modulo: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        power(slf, slf.as_any(), other, modulo)
    }

    fn __rpow__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        modulo: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        power(slf, other, slf.as_any(), modulo)
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
        Ok(binary(slf, slf.as_any(), other, operator)?.unbind())
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        let tag = self.form.tag();
        Ok(match &self.form {
            Form::Integer(value) => {
                combine_hashes(&[self.kind.id, tag, value.bind(py).hash()? as usize])
            }
            _ => combine_hashes(&[
                self.kind.id,
                tag,
                self.head.bind(py).hash()? as usize,
                self.args.bind(py).hash()? as usize,
            ]),
        })
    }

    /// Named arguments such as `eq.lhs`, declared with `names=(...)`.
    fn __getattr__(&self, py: Python<'_>, name: &Bound<'_, PyString>) -> PyResult<Py<PyAny>> {
        if let Some(names) = &self.names {
            for (index, declared) in names.bind(py).iter().enumerate() {
                if declared.eq(name)? {
                    return Ok(self.args.bind(py).get_item(index)?.unbind());
                }
            }
        }
        Err(PyAttributeError::new_err(format!(
            "'Expr' object has no attribute '{name}'"
        )))
    }
}

/// An integer. Python ints given to a function or an operator where an
/// expression of the kind of integers is expected are converted with this.
/// The kind of integers is declared from Python with `set_integer_kind`.
#[pyfunction(name = "Integer")]
fn integer<'py>(value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, Expr>> {
    let py = value.py();
    let Some(value) = exact_int(value) else {
        return Err(PyTypeError::new_err(format!(
            "Integer expects an int, got {}: {}",
            value.get_type().name()?,
            describe(value)
        )));
    };
    let Some(kind) = INTEGER_KIND.get(py) else {
        return Err(PyTypeError::new_err(NO_INTEGER_KIND));
    };
    Bound::new(py, integer_expr(kind, value))
}

/// Say which kind an integer is: `set_integer_kind(NumberKind)`. It can be
/// said once, because integers that already exist keep their kind.
#[pyfunction]
fn set_integer_kind(py: Python<'_>, kind: &Bound<'_, PyAny>) -> PyResult<()> {
    let kind = expect_kind(kind)?;
    INTEGER_KIND.set(py, kind).map_err(|_| {
        let current = INTEGER_KIND.get(py).map_or("a kind", |kind| kind.name.as_str());
        PyValueError::new_err(format!("integers are already declared to be {current}"))
    })
}

/// In a signature, `Symbol(NumberKind)` is a position that accepts only a
/// symbol of that kind, not an arbitrary expression.
#[pyclass(frozen, module = "nary")]
struct Symbol {
    kind: KindRef,
}

#[pymethods]
impl Symbol {
    #[new]
    fn new(kind: &Bound<'_, PyAny>) -> PyResult<Self> {
        if kind.is_instance_of::<PyString>() {
            return Err(PyTypeError::new_err(format!(
                "Symbol(kind) marks a position in a signature; \
                 to make a symbol call the kind, as in NumberKind({})",
                describe(kind)
            )));
        }
        Ok(Symbol { kind: expect_kind(kind)? })
    }

    #[getter]
    fn kind(&self, py: Python<'_>) -> PyResult<Py<Kind>> {
        kind_object(py, self.kind)
    }

    fn __repr__(&self) -> String {
        format!("Symbol({})", self.kind.name)
    }
}

/// One position in a signature: a kind, and whether only a symbol will do.
#[derive(Clone, Copy)]
struct Slot {
    kind: KindRef,
    symbol: bool,
}

impl Slot {
    fn parse(obj: &Bound<'_, PyAny>) -> PyResult<Slot> {
        if let Ok(marker) = obj.cast_exact::<Symbol>() {
            return Ok(Slot { kind: marker.get().kind, symbol: true });
        }
        match obj.cast_exact::<Kind>() {
            Ok(kind) => Ok(Slot { kind: kind.get().data, symbol: false }),
            Err(_) => Err(PyTypeError::new_err(format!(
                "a signature is made of kinds and Symbol(kind), got {}",
                describe(obj)
            ))),
        }
    }

    fn describe(self) -> String {
        if self.symbol {
            format!("a {} symbol", self.kind.name)
        } else {
            self.kind.name.clone()
        }
    }

    fn to_object<'py>(self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        if self.symbol {
            Ok(Bound::new(py, Symbol { kind: self.kind })?.into_any())
        } else {
            Ok(kind_object(py, self.kind)?.into_bound(py).into_any())
        }
    }
}

fn slots_to_tuple<'py>(py: Python<'py>, slots: &[Slot]) -> PyResult<Bound<'py, PyTuple>> {
    let mut objects = Vec::with_capacity(slots.len());
    for slot in slots {
        objects.push(slot.to_object(py)?);
    }
    PyTuple::new(py, objects)
}

/// A declared function: a name, the kinds accepted, and the kind returned.
#[pyclass(frozen, module = "nary")]
struct Function {
    name: Py<PyString>,
    /// The leading arguments.
    params: Vec<Slot>,
    /// A group of kinds that may repeat any number of times after the
    /// leading arguments. Empty if the function takes no further arguments.
    rest: Vec<Slot>,
    returns: KindRef,
    names: Option<Py<PyTuple>>,
    /// For each bound variable, its position and the positions of the
    /// arguments it is bound in. Recorded for later use; nothing here reads it.
    binds: Vec<(usize, Vec<usize>)>,
}

impl Function {
    fn slot(&self, position: usize) -> Slot {
        let fixed = self.params.len();
        if position < fixed {
            self.params[position]
        } else {
            self.rest[(position - fixed) % self.rest.len()]
        }
    }

    fn wrong_kind(&self, py: Python<'_>, expected: Slot, arg: &Bound<'_, PyAny>) -> PyErr {
        let text = (|| -> PyResult<String> {
            // An expression is described by its kind, anything else by its type.
            let got = match arg.cast_exact::<Expr>() {
                Ok(expr) => expr.get().kind.name.clone(),
                Err(_) => arg.get_type().name()?.to_string(),
            };
            Ok(format!(
                "{} expects {}, got {}: {}",
                self.name.bind(py),
                expected.describe(),
                got,
                arg.repr()?
            ))
        })();
        match text {
            Ok(text) => PyTypeError::new_err(text),
            Err(error) => error,
        }
    }

    fn check_count(&self, py: Python<'_>, given: usize) -> PyResult<()> {
        let fixed = self.params.len();
        let group = self.rest.len();
        let name = self.name.bind(py);
        if given < fixed || (group == 0 && given > fixed) {
            let at_least = if group == 0 { "" } else { "at least " };
            return Err(PyTypeError::new_err(format!(
                "{name} takes {at_least}{}, got {given}",
                count(fixed, "argument")
            )));
        }
        if group > 1 && (given - fixed) % group != 0 {
            let leading = if fixed == 0 {
                String::new()
            } else {
                format!("{} and then ", count(fixed, "argument"))
            };
            return Err(PyTypeError::new_err(format!(
                "{name} takes {leading}arguments in groups of {group}, got {given}"
            )));
        }
        Ok(())
    }

    fn apply<'py>(&self, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, Expr>> {
        let py = args.py();
        self.check_count(py, args.len())?;
        // Set only if a Python int had to be converted.
        let mut converted: Option<Vec<Bound<'py, PyAny>>> = None;
        for (position, arg) in args.iter_borrowed().enumerate() {
            let slot = self.slot(position);
            if let Ok(expr) = arg.cast_exact::<Expr>() {
                let expr = expr.get();
                if !same_kind(expr.kind, slot.kind)
                    || (slot.symbol && !matches!(expr.form, Form::Symbol))
                {
                    return Err(self.wrong_kind(py, slot, &arg));
                }
                if let Some(converted) = converted.as_mut() {
                    converted.push(arg.to_owned());
                }
                continue;
            }
            // Not an expression. An int is converted where an expression of
            // the kind of integers is expected.
            let value = match exact_int(&arg) {
                Some(value) if !slot.symbol => value,
                _ => return Err(self.wrong_kind(py, slot, &arg)),
            };
            let kind = match INTEGER_KIND.get(py) {
                Some(kind) if same_kind(kind, slot.kind) => *kind,
                Some(_) => return Err(self.wrong_kind(py, slot, &arg)),
                None => {
                    return Err(PyTypeError::new_err(format!(
                        "{} was given the int {}, but {NO_INTEGER_KIND}",
                        self.name.bind(py),
                        describe(&arg)
                    )));
                }
            };
            let node = Bound::new(py, integer_expr(kind, value))?.into_any();
            converted
                .get_or_insert_with(|| args.iter().take(position).collect())
                .push(node);
        }
        let args = match converted {
            Some(converted) => PyTuple::new(py, converted)?,
            None => args.clone(),
        };
        Bound::new(
            py,
            Expr {
                kind: self.returns,
                form: Form::Apply,
                head: self.name.clone_ref(py),
                args: args.unbind(),
                names: self.names.as_ref().map(|names| names.clone_ref(py)),
            },
        )
    }
}

#[pymethods]
impl Function {
    #[pyo3(signature = (*args))]
    fn __call__<'py>(&self, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, Expr>> {
        self.apply(args)
    }

    #[getter]
    fn name(&self, py: Python<'_>) -> Py<PyString> {
        self.name.clone_ref(py)
    }

    /// The leading positions: kinds and `Symbol(kind)` markers.
    #[getter]
    fn params<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        slots_to_tuple(py, &self.params)
    }

    /// The repeating group, or an empty tuple.
    #[getter]
    fn rest<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        slots_to_tuple(py, &self.rest)
    }

    #[getter]
    fn returns(&self, py: Python<'_>) -> PyResult<Py<Kind>> {
        kind_object(py, self.returns)
    }

    #[getter]
    fn names<'py>(&self, py: Python<'py>) -> Bound<'py, PyTuple> {
        match &self.names {
            Some(names) => names.bind(py).clone(),
            None => PyTuple::empty(py),
        }
    }

    /// `{variable: (positions it is bound in, ...)}`, as given to `function`.
    #[getter]
    fn binds<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        for (variable, scope) in &self.binds {
            dict.set_item(*variable, PyTuple::new(py, scope)?)?;
        }
        Ok(dict)
    }

    fn __repr__(&self, py: Python<'_>) -> String {
        format!("<function {}>", self.name.bind(py))
    }
}

fn parse_binds(
    name: &Bound<'_, PyString>,
    params: &[Slot],
    binds: &Bound<'_, PyDict>,
) -> PyResult<Vec<(usize, Vec<usize>)>> {
    let fixed = params.len();
    let position = |obj: &Bound<'_, PyAny>| -> PyResult<usize> {
        match obj.extract::<usize>() {
            Ok(index) if index < fixed => Ok(index),
            _ => Err(PyValueError::new_err(format!(
                "{name}: binds refers to argument {}, which is not one of the {fixed} declared",
                describe(obj)
            ))),
        }
    };
    let mut parsed = Vec::with_capacity(binds.len());
    for (variable, scope) in binds.iter() {
        let variable = position(&variable)?;
        if !params[variable].symbol {
            return Err(PyValueError::new_err(format!(
                "{name}: argument {variable} is bound, so it must be declared as Symbol(kind)"
            )));
        }
        let scope = scope.cast::<PyTuple>().map_err(|_| {
            PyTypeError::new_err(format!(
                "{name}: binds maps a position to a tuple of positions, got {}",
                describe(&scope)
            ))
        })?;
        let mut positions = Vec::with_capacity(scope.len());
        for item in scope.iter() {
            let item = position(&item)?;
            if item == variable {
                return Err(PyValueError::new_err(format!(
                    "{name}: argument {variable} cannot be bound in itself"
                )));
            }
            positions.push(item);
        }
        parsed.push((variable, positions));
    }
    Ok(parsed)
}

/// Declare a function.
///
/// `params` are the leading positions. Each is a kind, or `Symbol(kind)` for
/// a position that must be a symbol. `rest` is a kind, or a tuple of kinds
/// that repeats as a group: with `rest=NumberKind` any number of further
/// NumberKind arguments are accepted, and with `rest=(NumberKind, BoolKind)`
/// any number of (NumberKind, BoolKind) pairs. The result is always of the
/// kind `returns`.
///
/// `names` gives attribute names for the leading arguments, so that
/// `names=("lhs", "rhs")` makes `.lhs` and `.rhs` available on the result.
///
/// `binds` records bound variables. `binds={1: (0,)}` says that argument 1
/// is a variable bound in argument 0. It does not change what is built.
#[pyfunction]
#[pyo3(signature = (name, *params, rest=None, returns, names=None, binds=None))]
fn function(
    py: Python<'_>,
    name: Py<PyString>,
    params: &Bound<'_, PyTuple>,
    rest: Option<&Bound<'_, PyAny>>,
    returns: &Bound<'_, PyAny>,
    names: Option<Py<PyTuple>>,
    binds: Option<&Bound<'_, PyDict>>,
) -> PyResult<Function> {
    let returns = match returns.cast_exact::<Kind>() {
        Ok(kind) => kind.get().data,
        Err(_) => {
            return Err(PyValueError::new_err(format!(
                "returns must be a kind, got {}",
                describe(returns)
            )));
        }
    };
    let mut slots = Vec::with_capacity(params.len());
    for param in params.iter() {
        slots.push(Slot::parse(&param)?);
    }
    let rest = match rest {
        None => Vec::new(),
        Some(rest) => match rest.cast::<PyTuple>() {
            Ok(group) if group.is_empty() => {
                return Err(PyValueError::new_err(format!(
                    "{}: rest cannot be an empty tuple",
                    name.bind(py)
                )));
            }
            Ok(group) => {
                let mut slots = Vec::with_capacity(group.len());
                for item in group.iter() {
                    slots.push(Slot::parse(&item)?);
                }
                slots
            }
            Err(_) => vec![Slot::parse(rest)?],
        },
    };
    let names = match names {
        Some(names) if names.bind(py).len() > slots.len() => {
            return Err(PyValueError::new_err(format!(
                "{}: more names than declared arguments",
                name.bind(py)
            )));
        }
        Some(names) if names.bind(py).is_empty() => None,
        other => other,
    };
    if let Some(names) = &names {
        // An attribute that every expression has would hide the argument.
        let expr = py.get_type::<Expr>();
        for declared in names.bind(py).iter() {
            let declared = declared.cast::<PyString>().map_err(|_| {
                PyTypeError::new_err(format!(
                    "{}: names must be strings, got {}",
                    name.bind(py),
                    describe(&declared)
                ))
            })?;
            if expr.hasattr(declared)? {
                return Err(PyValueError::new_err(format!(
                    "{}: an argument cannot be named {}, which every expression already has",
                    name.bind(py),
                    describe(declared)
                )));
            }
        }
    }
    let binds = match binds {
        Some(binds) => parse_binds(name.bind(py), &slots, binds)?,
        None => Vec::new(),
    };
    Ok(Function { name, params: slots, rest, returns, names, binds })
}

/// Say which function an operator builds for a kind:
/// `set_operator(NumberKind, "+", Add)`. The operators are "+", "*", "**",
/// "<", ">", "<=" and ">=". Each can be set once for each kind. A kind with
/// no function for an operator does not support that operator.
#[pyfunction]
fn set_operator(
    py: Python<'_>,
    kind: &Bound<'_, PyAny>,
    symbol: &str,
    function: Py<Function>,
) -> PyResult<()> {
    let kind = expect_kind(kind)?;
    let Some(operator) = Operator::ALL.into_iter().find(|op| op.symbol() == symbol) else {
        return Err(PyValueError::new_err(format!("unknown operator {symbol:?}")));
    };
    kind.operators[operator as usize].set(py, function).map_err(|_| {
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
    m.add_class::<Symbol>()?;
    m.add_class::<Function>()?;
    m.add_function(wrap_pyfunction!(declare_kind, m)?)?;
    m.add_function(wrap_pyfunction!(kind_family, m)?)?;
    m.add_function(wrap_pyfunction!(integer, m)?)?;
    m.add_function(wrap_pyfunction!(set_integer_kind, m)?)?;
    m.add_function(wrap_pyfunction!(function, m)?)?;
    m.add_function(wrap_pyfunction!(set_operator, m)?)?;
    Ok(())
}

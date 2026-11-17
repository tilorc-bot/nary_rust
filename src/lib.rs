//! Typed, inert expression trees for Python, written in Rust.
//!
//! `Expr` is a head applied to arguments, and it is the only class of
//! expression. Each expression has a kind. A kind is an object declared from
//! Python with `kind(name)`, and a function declares the kinds it accepts and
//! the kind it returns, with optional names for its arguments. The checking
//! and node construction happen here.
//!
//! No kind and no particular function is defined in this file. The kinds
//! (NumberKind, Bool) and the functions (Add, Mul, Eq and the rest) are
//! declared in Python (nary_rs.py), and each kind is told which function an
//! operator builds with `set_operator`.

use std::sync::atomic::{AtomicUsize, Ordering};

use pyo3::exceptions::{PyAttributeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::pyclass::CompareOp;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyString, PyTuple};

/// What is known about a kind.
///
/// One of these is made for each `kind(name)` call and is never freed, so an
/// expression refers to its kind with a plain reference: building a node
/// does no reference counting on the kind, and two kinds are the same kind
/// exactly when the references are the same.
struct KindData {
    /// The position of the kind in the order of declaration. Used in hashes.
    id: usize,
    name: String,
    /// The Python object for this kind. Set when the kind is declared.
    object: PyOnceLock<Py<Kind>>,
    /// The function each operator builds for this kind, indexed by
    /// `Operator`. Filled in from Python with `set_operator`.
    operators: [PyOnceLock<Py<Function>>; Operator::COUNT],
}

type KindRef = &'static KindData;

fn same_kind(a: KindRef, b: KindRef) -> bool {
    std::ptr::eq(a, b)
}

static KIND_COUNT: AtomicUsize = AtomicUsize::new(0);

/// A kind of expression, such as NumberKind. Declared with `kind(name)`.
///
/// Calling a kind makes a leaf of that kind: `NumberKind("x")`.
#[pyclass(frozen, module = "nary_rust")]
struct Kind {
    data: KindRef,
}

#[pymethods]
impl Kind {
    /// `NumberKind("x")` is a leaf named x of this kind. Further arguments
    /// build a node without any checking.
    #[pyo3(signature = (head, *args))]
    fn __call__(
        &self,
        py: Python<'_>,
        head: Py<PyString>,
        args: &Bound<'_, PyTuple>,
    ) -> PyResult<Py<Expr>> {
        Py::new(py, Expr { kind: self.data, head, args: args.clone().unbind(), names: None })
    }

    #[getter]
    fn name(&self) -> &str {
        &self.data.name
    }

    fn __repr__(&self) -> &str {
        &self.data.name
    }
}

/// Declare a kind: `NumberKind = kind("NumberKind")`.
///
/// Every call makes a new kind, different from every other, and a kind
/// lasts for the life of the process. Declare each kind once, when a module
/// is imported.
#[pyfunction(name = "kind")]
fn declare_kind(py: Python<'_>, name: String) -> PyResult<Py<Kind>> {
    let data: KindRef = Box::leak(Box::new(KindData {
        id: KIND_COUNT.fetch_add(1, Ordering::Relaxed),
        name,
        object: PyOnceLock::new(),
        operators: [const { PyOnceLock::new() }; Operator::COUNT],
    }));
    let object = Py::new(py, Kind { data })?;
    // Nothing else can have set it: `data` was made above.
    let _ = data.object.set(py, object.clone_ref(py));
    Ok(object)
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

/// A head applied to arguments, of some kind.
#[pyclass(frozen, module = "nary_rust")]
struct Expr {
    kind: KindRef,
    head: Py<PyString>,
    args: Py<PyTuple>,
    /// Names for the leading arguments, shared with the declaring function.
    names: Option<Py<PyTuple>>,
}

fn structural_eq(a: &Expr, b: &Expr, py: Python<'_>) -> PyResult<bool> {
    Ok(same_kind(a.kind, b.kind)
        && a.head.bind(py).as_any().eq(b.head.bind(py))?
        && a.args.bind(py).as_any().eq(b.args.bind(py))?)
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
fn combine_hashes(parts: [usize; 3]) -> isize {
    const MULTIPLIER: u64 = 0x9E37_79B9_7F4A_7C15;
    let mut hash = MULTIPLIER;
    for part in parts {
        hash = (hash ^ part as u64).wrapping_mul(MULTIPLIER);
        hash ^= hash >> 32;
    }
    hash as isize
}

/// The operators. For each kind, each builds whichever function was
/// registered for it with `set_operator`.
#[derive(Clone, Copy)]
enum Operator {
    Add,
    Mul,
    Lt,
}

impl Operator {
    const COUNT: usize = 3;
    const ALL: [Operator; Operator::COUNT] = [Operator::Add, Operator::Mul, Operator::Lt];

    fn symbol(self) -> &'static str {
        match self {
            Operator::Add => "+",
            Operator::Mul => "*",
            Operator::Lt => "<",
        }
    }
}

/// The function registered for `operator` on the kind of `slf`, applied to
/// `slf` and `other`. If the kind has none, the result is NotImplemented, as
/// for any Python object that does not support an operator.
fn binary<'py>(
    slf: &Bound<'py, Expr>,
    other: &Bound<'py, PyAny>,
    operator: Operator,
) -> PyResult<Bound<'py, PyAny>> {
    let py = slf.py();
    match slf.get().kind.operators[operator as usize].get(py) {
        Some(function) => {
            let args = PyTuple::new(py, [slf.as_any(), other])?;
            Ok(function.get().apply(&args)?.into_any())
        }
        None => Ok(py.NotImplemented().into_bound(py)),
    }
}

#[pymethods]
impl Expr {
    /// The kind of this expression: `e.kind is NumberKind`.
    #[getter]
    fn kind(&self, py: Python<'_>) -> Option<Py<Kind>> {
        self.kind.object.get(py).map(|kind| kind.clone_ref(py))
    }

    #[getter]
    fn head(&self, py: Python<'_>) -> Py<PyString> {
        self.head.clone_ref(py)
    }

    #[getter]
    fn args(&self, py: Python<'_>) -> Py<PyTuple> {
        self.args.clone_ref(py)
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
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
        binary(slf, other, Operator::Add)
    }

    fn __mul__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, Operator::Mul)
    }

    fn __richcmp__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        op: CompareOp,
    ) -> PyResult<Py<PyAny>> {
        match op {
            CompareOp::Lt => Ok(binary(slf, other, Operator::Lt)?.unbind()),
            _ => compare(slf.get(), other, op),
        }
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        Ok(combine_hashes([
            self.kind.id,
            self.head.bind(py).hash()? as usize,
            self.args.bind(py).hash()? as usize,
        ]))
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

/// A declared function: a name, the kinds accepted, and the kind returned.
#[pyclass(frozen, module = "nary_rust")]
struct Function {
    name: Py<PyString>,
    arg_kinds: Vec<KindRef>,
    rest: Option<KindRef>,
    returns: KindRef,
    names: Option<Py<PyTuple>>,
}

impl Function {
    fn wrong_kind(&self, py: Python<'_>, expected: KindRef, arg: &Bound<'_, PyAny>) -> PyErr {
        let text = (|| -> PyResult<String> {
            // An expression is described by its kind, anything else by its type.
            let got = match arg.cast_exact::<Expr>() {
                Ok(expr) => expr.get().kind.name.clone(),
                Err(_) => arg.get_type().name()?.to_string(),
            };
            Ok(format!(
                "{} expects {}, got {}: {}",
                self.name.bind(py),
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

    fn apply<'py>(&self, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, Expr>> {
        let py = args.py();
        let fixed = self.arg_kinds.len();
        let given = args.len();
        if given < fixed || (self.rest.is_none() && given > fixed) {
            let expected = if self.rest.is_some() {
                format!("at least {}", fixed)
            } else {
                fixed.to_string()
            };
            return Err(PyTypeError::new_err(format!(
                "{} takes {} arguments, got {}",
                self.name.bind(py),
                expected,
                given
            )));
        }
        for (position, arg) in args.iter_borrowed().enumerate() {
            let expected = if position < fixed {
                self.arg_kinds[position]
            } else {
                self.rest.unwrap()
            };
            let matches = arg
                .cast_exact::<Expr>()
                .is_ok_and(|expr| same_kind(expr.get().kind, expected));
            if !matches {
                return Err(self.wrong_kind(py, expected, &arg));
            }
        }
        Bound::new(
            py,
            Expr {
                kind: self.returns,
                head: self.name.clone_ref(py),
                args: args.clone().unbind(),
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

    fn __repr__(&self, py: Python<'_>) -> String {
        format!("<function {}>", self.name.bind(py))
    }
}

/// Declare a function.
///
/// `arg_kinds` are the kinds of the leading arguments. If `rest` is given,
/// any number of further arguments of that kind are accepted. The result is
/// always of the kind `returns`. `names` gives attribute names for the
/// leading arguments, so that `names=("lhs", "rhs")` makes `.lhs` and `.rhs`
/// available on the result.
#[pyfunction]
#[pyo3(signature = (name, *arg_kinds, rest=None, returns, names=None))]
fn function(
    py: Python<'_>,
    name: Py<PyString>,
    arg_kinds: &Bound<'_, PyTuple>,
    rest: Option<&Bound<'_, PyAny>>,
    returns: &Bound<'_, PyAny>,
    names: Option<Py<PyTuple>>,
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
    let mut kinds = Vec::with_capacity(arg_kinds.len());
    for kind in arg_kinds.iter() {
        kinds.push(expect_kind(&kind)?);
    }
    let rest = match rest {
        Some(rest) => Some(expect_kind(rest)?),
        None => None,
    };
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
    Ok(Function { name, arg_kinds: kinds, rest, returns, names })
}

/// Say which function an operator builds for a kind:
/// `set_operator(NumberKind, "+", Add)`. The operators are "+", "*" and "<".
/// Each can be set once for each kind. A kind with no function for an
/// operator does not support that operator.
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
fn nary_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Expr>()?;
    m.add_class::<Kind>()?;
    m.add_class::<Function>()?;
    m.add_function(wrap_pyfunction!(declare_kind, m)?)?;
    m.add_function(wrap_pyfunction!(function, m)?)?;
    m.add_function(wrap_pyfunction!(set_operator, m)?)?;
    Ok(())
}

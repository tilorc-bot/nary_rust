//! Typed, inert expression trees for Python, written in Rust.
//!
//! A class per kind (`NumberKind`, `Bool`), functions that declare the kinds
//! they accept and the kind they return, and optional names for arguments.
//! The checking and node construction happen here.
//!
//! No particular function is defined in this file. Add, Mul, Eq and the rest
//! are declared in Python (nary_rs.py) with `function(...)`, and the
//! operators are told which function to build with `set_operator`.

use pyo3::exceptions::{PyAttributeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::pyclass::CompareOp;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyString, PyTuple, PyType};

/// Which kind class a function returns.
#[derive(Clone, Copy, PartialEq)]
enum Kind {
    Number,
    Bool,
}

/// A head applied to arguments. No operators.
#[pyclass(subclass, module = "nary_rust")]
struct Expr {
    head: Py<PyString>,
    args: Py<PyTuple>,
    /// Names for the leading arguments, shared with the declaring function.
    names: Option<Py<PyTuple>>,
}

#[pyclass(extends = Expr, module = "nary_rust")]
struct NumberKind;

#[pyclass(extends = Expr, module = "nary_rust")]
struct Bool;

fn new_node<'py>(
    py: Python<'py>,
    kind: Kind,
    head: Py<PyString>,
    args: Py<PyTuple>,
    names: Option<Py<PyTuple>>,
) -> PyResult<Bound<'py, PyAny>> {
    let base = PyClassInitializer::from(Expr { head, args, names });
    Ok(match kind {
        Kind::Number => Bound::new(py, base.add_subclass(NumberKind))?.into_any(),
        Kind::Bool => Bound::new(py, base.add_subclass(Bool))?.into_any(),
    })
}

fn structural_eq(a: &Expr, b: &Expr, py: Python<'_>) -> PyResult<bool> {
    Ok(a.head.bind(py).as_any().eq(b.head.bind(py))?
        && a.args.bind(py).as_any().eq(b.args.bind(py))?)
}

fn compare(slf: &Expr, other: &Bound<'_, PyAny>, op: CompareOp) -> PyResult<Py<PyAny>> {
    let py = other.py();
    let equal = match other.cast::<Expr>() {
        Ok(other) => structural_eq(slf, &other.borrow(), py)?,
        Err(_) => return Ok(py.NotImplemented()),
    };
    Ok(match op {
        CompareOp::Eq => equal.into_pyobject(py)?.to_owned().into_any().unbind(),
        CompareOp::Ne => (!equal).into_pyobject(py)?.to_owned().into_any().unbind(),
        _ => py.NotImplemented(),
    })
}

fn structural_hash(slf: &Expr, py: Python<'_>) -> PyResult<isize> {
    (slf.head.bind(py), slf.args.bind(py)).into_pyobject(py)?.hash()
}

#[pymethods]
impl Expr {
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

    fn __richcmp__(&self, other: &Bound<'_, PyAny>, op: CompareOp) -> PyResult<Py<PyAny>> {
        compare(self, other, op)
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        structural_hash(self, py)
    }

    /// Named arguments such as `eq.lhs`, declared with `names=(...)`.
    fn __getattr__(slf: &Bound<'_, Self>, name: &Bound<'_, PyString>) -> PyResult<Py<PyAny>> {
        let py = slf.py();
        let this = slf.borrow();
        if let Some(names) = &this.names {
            for (index, declared) in names.bind(py).iter().enumerate() {
                if declared.eq(name)? {
                    return Ok(this.args.bind(py).get_item(index)?.unbind());
                }
            }
        }
        Err(PyAttributeError::new_err(format!(
            "'{}' object has no attribute '{}'",
            slf.get_type().name()?,
            name
        )))
    }
}

fn leaf_or_node(head: Py<PyString>, args: &Bound<'_, PyTuple>) -> Expr {
    Expr { head, args: args.clone().unbind(), names: None }
}

#[pymethods]
impl NumberKind {
    #[new]
    #[pyo3(signature = (head, *args))]
    fn new(head: Py<PyString>, args: &Bound<'_, PyTuple>) -> PyClassInitializer<Self> {
        PyClassInitializer::from(leaf_or_node(head, args)).add_subclass(NumberKind)
    }

    fn __add__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, &ADD, "+")
    }

    fn __mul__<'py>(slf: &Bound<'py, Self>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        binary(slf, other, &MUL, "*")
    }

    fn __richcmp__<'py>(
        slf: &Bound<'py, Self>,
        other: &Bound<'py, PyAny>,
        op: CompareOp,
    ) -> PyResult<Py<PyAny>> {
        match op {
            CompareOp::Lt => Ok(binary(slf, other, &LT, "<")?.unbind()),
            _ => compare(slf.as_super().borrow().deref(), other, op),
        }
    }

    fn __hash__(slf: &Bound<'_, Self>) -> PyResult<isize> {
        structural_hash(slf.as_super().borrow().deref(), slf.py())
    }
}

#[pymethods]
impl Bool {
    #[new]
    #[pyo3(signature = (head, *args))]
    fn new(head: Py<PyString>, args: &Bound<'_, PyTuple>) -> PyClassInitializer<Self> {
        PyClassInitializer::from(leaf_or_node(head, args)).add_subclass(Bool)
    }
}

use std::ops::Deref;

/// A declared function: a name, the classes accepted, and the class returned.
#[pyclass(module = "nary_rust")]
struct Function {
    name: Py<PyString>,
    arg_types: Vec<Py<PyType>>,
    rest: Option<Py<PyType>>,
    returns: Kind,
    names: Option<Py<PyTuple>>,
}

impl Function {
    fn wrong_kind(&self, py: Python<'_>, expected: &Py<PyType>, arg: &Bound<'_, PyAny>) -> PyErr {
        let text = (|| -> PyResult<String> {
            Ok(format!(
                "{} expects {}, got {}: {}",
                self.name.bind(py),
                expected.bind(py).name()?,
                arg.get_type().name()?,
                arg.repr()?
            ))
        })();
        match text {
            Ok(text) => PyTypeError::new_err(text),
            Err(error) => error,
        }
    }

    fn apply<'py>(&self, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, PyAny>> {
        let py = args.py();
        let fixed = self.arg_types.len();
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
                &self.arg_types[position]
            } else {
                self.rest.as_ref().unwrap()
            };
            let ty = expected.bind(py);
            if !arg.get_type().is(ty) && !arg.is_instance(ty)? {
                return Err(self.wrong_kind(py, expected, &arg));
            }
        }
        new_node(
            py,
            self.returns,
            self.name.clone_ref(py),
            args.clone().unbind(),
            self.names.as_ref().map(|names| names.clone_ref(py)),
        )
    }
}

#[pymethods]
impl Function {
    #[pyo3(signature = (*args))]
    fn __call__<'py>(&self, args: &Bound<'py, PyTuple>) -> PyResult<Bound<'py, PyAny>> {
        self.apply(args)
    }

    fn __repr__(&self, py: Python<'_>) -> String {
        format!("<function {}>", self.name.bind(py))
    }
}

/// Declare a function.
///
/// `arg_types` are the classes of the leading arguments. If `rest` is given,
/// any number of further arguments of that class are accepted. The result is
/// always an instance of `returns`. `names` gives attribute names for the
/// leading arguments, so that `names=("lhs", "rhs")` makes `.lhs` and `.rhs`
/// available on the result.
#[pyfunction]
#[pyo3(signature = (name, *arg_types, rest=None, returns, names=None))]
fn function(
    py: Python<'_>,
    name: Py<PyString>,
    arg_types: &Bound<'_, PyTuple>,
    rest: Option<Py<PyType>>,
    returns: &Bound<'_, PyType>,
    names: Option<Py<PyTuple>>,
) -> PyResult<Function> {
    let returns = if returns.is(&py.get_type::<NumberKind>()) {
        Kind::Number
    } else if returns.is(&py.get_type::<Bool>()) {
        Kind::Bool
    } else {
        return Err(PyValueError::new_err("returns must be NumberKind or Bool"));
    };
    let mut types = Vec::with_capacity(arg_types.len());
    for ty in arg_types.iter() {
        types.push(ty.cast_into::<PyType>()?.unbind());
    }
    let names = match names {
        Some(names) if names.bind(py).len() > types.len() => {
            return Err(PyValueError::new_err(format!(
                "{}: more names than declared arguments",
                name.bind(py)
            )));
        }
        Some(names) if names.bind(py).is_empty() => None,
        other => other,
    };
    Ok(Function { name, arg_types: types, rest, returns, names })
}

// The functions the operators build, registered from Python with set_operator.
static ADD: PyOnceLock<Py<Function>> = PyOnceLock::new();
static MUL: PyOnceLock<Py<Function>> = PyOnceLock::new();
static LT: PyOnceLock<Py<Function>> = PyOnceLock::new();

fn binary<'py>(
    slf: &Bound<'py, NumberKind>,
    other: &Bound<'py, PyAny>,
    function: &PyOnceLock<Py<Function>>,
    symbol: &str,
) -> PyResult<Bound<'py, PyAny>> {
    let py = slf.py();
    let Some(function) = function.get(py) else {
        return Err(PyTypeError::new_err(format!(
            "no function has been registered for the {symbol} operator"
        )));
    };
    let args = PyTuple::new(py, [slf.as_any(), other])?;
    function.bind(py).borrow().apply(&args)
}

/// Say which function an operator on NumberKind builds: "+", "*" or "<".
#[pyfunction]
fn set_operator(py: Python<'_>, symbol: &str, function: Py<Function>) -> PyResult<()> {
    let slot = match symbol {
        "+" => &ADD,
        "*" => &MUL,
        "<" => &LT,
        _ => return Err(PyValueError::new_err(format!("unknown operator {symbol:?}"))),
    };
    slot.set(py, function)
        .map_err(|_| PyValueError::new_err(format!("the {symbol} operator is already set")))
}

#[pymodule]
fn nary_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Expr>()?;
    m.add_class::<NumberKind>()?;
    m.add_class::<Bool>()?;
    m.add_class::<Function>()?;
    m.add_function(wrap_pyfunction!(function, m)?)?;
    m.add_function(wrap_pyfunction!(set_operator, m)?)?;
    Ok(())
}

"""The functions built on the Rust module, each declared here in Python.

The compiled module ``nary_rust`` provides the kind classes, ``function`` and
``set_operator``, and knows nothing about any particular function. Each one is
declared below with a ``function(...)`` call. A declaration is only data;
calling the function still runs entirely in Rust.

    import nary_rs as nr
"""

from nary_rust import Bool, Expr, Function, NumberKind, function, set_operator

Add = function("Add", rest=NumberKind, returns=NumberKind)
Mul = function("Mul", rest=NumberKind, returns=NumberKind)
Pow = function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp")
)
sin = function("sin", NumberKind, returns=NumberKind)
Lt = function("Lt", NumberKind, NumberKind, returns=Bool)
Eq = function("Eq", NumberKind, NumberKind, returns=Bool, names=("lhs", "rhs"))

# Which function each operator on a NumberKind builds.
set_operator("+", Add)
set_operator("*", Mul)
set_operator("<", Lt)

__all__ = [
    "Add", "Bool", "Eq", "Expr", "Function", "Lt", "Mul", "NumberKind", "Pow",
    "function", "set_operator", "sin",
]

"""The kinds and the functions built on the Rust module, declared in Python.

The compiled module ``nary_rust`` provides ``Expr``, ``kind``, ``function``
and ``set_operator``, and knows nothing about any particular kind or
function. Each kind is declared below with a ``kind(...)`` call and each
function with a ``function(...)`` call. A declaration is only data; calling
the function still runs entirely in Rust.

    import nary_rs as nr
"""

from nary_rust import Expr, Function, Kind, function, kind, set_operator

# Adding a kind is adding a line here; nothing in Rust changes. Every
# expression is an Expr, and ``e.kind`` is one of these objects.
NumberKind = kind("NumberKind")
Bool = kind("Bool")

Add = function("Add", rest=NumberKind, returns=NumberKind)
Mul = function("Mul", rest=NumberKind, returns=NumberKind)
Pow = function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp")
)
sin = function("sin", NumberKind, returns=NumberKind)
Lt = function("Lt", NumberKind, NumberKind, returns=Bool)
Eq = function("Eq", NumberKind, NumberKind, returns=Bool, names=("lhs", "rhs"))

# Which function each operator builds, for each kind. A Bool has none, so
# ``p + q`` on two Bools is a TypeError.
set_operator(NumberKind, "+", Add)
set_operator(NumberKind, "*", Mul)
set_operator(NumberKind, "<", Lt)

__all__ = [
    "Add", "Bool", "Eq", "Expr", "Function", "Kind", "Lt", "Mul",
    "NumberKind", "Pow", "function", "kind", "set_operator", "sin",
]

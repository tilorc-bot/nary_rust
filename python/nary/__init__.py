"""Typed, inert expression trees.

The compiled module ``nary._core`` provides ``Expr``, ``kind``,
``kind_family``, ``Integer``, ``Symbol``, ``function`` and ``set_operator``,
and knows nothing about any particular kind or function. The kinds and the
kind families are declared in ``nary.kinds``, and each function is declared
in one of the other modules of this package with a ``function(...)`` call.
A declaration is only data; calling the function still runs entirely in
Rust.

    import nary as nr
"""

from ._core import (
    Expr,
    Function,
    Integer,
    Kind,
    KindFamily,
    Symbol,
    function,
    kind,
    kind_family,
    set_integer_kind,
    set_operator,
)
from .kinds import BoolKind, MatrixKind, NumberKind, SetKind
from .arithmetic import Add, Mul, Pow
from .calculus import (
    Antiderivative,
    Derivative,
    Integral,
    Limit,
    Product,
    Subs,
    Sum,
)
from .elementary import cos, exp, log, pi, sin, tan
from .logic import And, Not, Or, false, true
from .matrices import Determinant, Inverse, MatAdd, MatMul, Transpose
from .piecewise import Piecewise
from .relational import Eq, Ge, Gt, Le, Lt
from .sets import Contains, FiniteSet, Intersection, Interval, Union

__all__ = [
    # the declaration machinery
    "Expr", "Function", "Integer", "Kind", "KindFamily", "Symbol", "function",
    "kind", "kind_family", "set_integer_kind", "set_operator",
    # kinds and kind families
    "BoolKind", "MatrixKind", "NumberKind", "SetKind",
    # arithmetic
    "Add", "Mul", "Pow",
    # calculus
    "Antiderivative", "Derivative", "Integral", "Limit", "Product", "Subs",
    "Sum",
    # elementary
    "cos", "exp", "log", "pi", "sin", "tan",
    # logic
    "And", "Not", "Or", "false", "true",
    # matrices
    "Determinant", "Inverse", "MatAdd", "MatMul", "Transpose",
    # piecewise
    "Piecewise",
    # relational
    "Eq", "Ge", "Gt", "Le", "Lt",
    # sets
    "Contains", "FiniteSet", "Intersection", "Interval", "Union",
]

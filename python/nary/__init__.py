"""Typed, inert expression trees.

The compiled module ``nary._core`` provides ``Expr``, ``kind``,
``kind_family``, ``Symbol``, ``function`` and ``set_operator``, and knows
nothing about any particular kind or function. The kinds are declared in
``nary.kinds``, and each function is declared in one of the other modules of
this package with a ``function(...)`` call. A declaration is only data;
calling the function still runs entirely in Rust.

    import nary as nr
"""

from ._core import (
    Expr,
    Function,
    Kind,
    KindFamily,
    Symbol,
    function,
    kind,
    kind_family,
    set_operator,
)
from .kinds import BoolKind, NumberKind
from .arithmetic import Add, Mul, Pow
from .elementary import sin
from .relational import Eq, Ge, Gt, Le, Lt

__all__ = [
    # the declaration machinery
    "Expr", "Function", "Kind", "KindFamily", "Symbol", "function", "kind",
    "kind_family", "set_operator",
    # kinds
    "BoolKind", "NumberKind",
    # functions
    "Add", "Eq", "Ge", "Gt", "Le", "Lt", "Mul", "Pow", "sin",
]

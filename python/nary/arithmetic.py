"""
    >>> from nary import Add, Many, NumberKind
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> terms = Many(NumberKind)("terms")
    >>> terms.kind, Add.kind
    (Many(NumberKind), FunctionKind((Many(NumberKind),), NumberKind))
    >>> Add(x, y, 1).terms
    (x, y, 1)
"""

from __future__ import annotations

from ._core import Expr, set_operator
from .domains import declare_function
from .kinds import Many, NumberKind
from .logic import Or, true
from .relational import Gt, Ne, re

__all__ = ["Add", "Mul", "Pow", "NegativeOne"]

base, exponent = NumberKind("base"), NumberKind("exp")
terms, factors = Many(NumberKind)("terms"), Many(NumberKind)("factors")

Add = declare_function("Add", terms, returns=NumberKind, domain=true)
Mul = declare_function("Mul", factors, returns=NumberKind, domain=true)
Pow = declare_function(
    "Pow", base, exponent, returns=NumberKind,
    domain=Or(Ne(base, 0), Gt(re(exponent), 0)),
)

NegativeOne = NumberKind(-1)


def _subtract(a: Expr, b: object) -> Expr:
    return Add(a, Mul(NegativeOne, b))


def _divide(a: Expr, b: object) -> Expr:
    return Mul(a, Pow(b, NegativeOne))


def _negate(a: Expr) -> Expr:
    return Mul(NegativeOne, a)


set_operator(NumberKind, "+", Add)
set_operator(NumberKind, "*", Mul)
set_operator(NumberKind, "**", Pow)
set_operator(NumberKind, "-", _subtract)
set_operator(NumberKind, "/", _divide)
set_operator(NumberKind, "neg", _negate)

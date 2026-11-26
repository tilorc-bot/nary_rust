from ._core import Many, set_operator
from .domains import declare_function
from .kinds import NumberKind
from .logic import Or, true
from .relational import Gt, Ne, re

__all__ = ["Add", "Mul", "Pow", "NegativeOne"]

terms, factors = NumberKind("terms"), NumberKind("factors")
base, exponent = NumberKind("base"), NumberKind("exp")

Add = declare_function("Add", Many(terms), returns=NumberKind, domain=true)
Mul = declare_function("Mul", Many(factors), returns=NumberKind, domain=true)
Pow = declare_function(
    "Pow", base, exponent, returns=NumberKind,
    domain=Or(Ne(base, 0), Gt(re(exponent), 0)),
)

NegativeOne = NumberKind(-1)


def _subtract(a, b):
    return Add(a, Mul(NegativeOne, b))


def _divide(a, b):
    return Mul(a, Pow(b, NegativeOne))


def _negate(a):
    return Mul(NegativeOne, a)


set_operator(NumberKind, "+", Add)
set_operator(NumberKind, "*", Mul)
set_operator(NumberKind, "**", Pow)
set_operator(NumberKind, "-", _subtract)
set_operator(NumberKind, "/", _divide)
set_operator(NumberKind, "neg", _negate)

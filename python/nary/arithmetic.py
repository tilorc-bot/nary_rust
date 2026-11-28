"""
    >>> from nary import Add, Many, NumberKind
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> terms = Many(NumberKind)("terms")
    >>> terms.kind, Add.kind
    (Many(NumberKind), FunctionKind((Many(NumberKind),), NumberKind))
    >>> Add(x, y, 1).terms
    (x, y, 1)
"""

from ._core import set_operator
from ._numbers import exact_power, exact_product, exact_sum
from .domains import declare_function
from .kinds import Many, NumberKind
from .logic import Or, true
from .properties import declare_properties
from .relational import Gt, Ne, re

__all__ = ["Add", "Mul", "Pow", "NegativeOne"]

base, exponent = NumberKind("base"), NumberKind("exp")
terms, factors = Many(NumberKind)("terms"), Many(NumberKind)("factors")

Add = declare_function("Add", terms, returns=NumberKind, domain=true)
declare_properties(
    Add, is_associative=True, is_commutative=True, identity_element=0, evaluate_literals=exact_sum,
)
Mul = declare_function("Mul", factors, returns=NumberKind, domain=true)
declare_properties(
    Mul, is_associative=True, is_commutative=True, identity_element=1, absorbing_element=0,
    evaluate_literals=exact_product,
)
Pow = declare_function(
    "Pow", base, exponent, returns=NumberKind,
    domain=Or(Ne(base, 0), Gt(re(exponent), 0)),
)
declare_properties(Pow, evaluate_literals=exact_power)

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

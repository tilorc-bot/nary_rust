"""Add, Mul and Pow, the literal -1, and the operators that build them.

There are no Sub, Div or Neg functions. As in SymPy, ``x - y`` is
``Add(x, Mul(-1, y))``, ``x / y`` is ``Mul(x, Pow(y, -1))`` and ``-x`` is
``Mul(-1, x)``, built by Python functions given to ``set_operator``.
"""

from ._core import set_operator
from .domains import declare_function
from .identities import (
    Equal,
    absorbing,
    associative,
    commutative,
    declare_identities,
    distributive,
    identity,
    inverse,
    repeated,
)
from .kinds import NumberKind
from .logic import Or, true
from .relational import Gt, Ne, re

__all__ = ["Add", "Mul", "Pow", "NegativeOne"]

base, exponent = NumberKind("base"), NumberKind("exp")

Add = declare_function("Add", rest=NumberKind, returns=NumberKind, domain=true)
Mul = declare_function("Mul", rest=NumberKind, returns=NumberKind, domain=true)
# Division is Pow(y, -1), so the domain of Pow is where division by zero is
# excluded. Under it 0**0 has no value.
Pow = declare_function(
    "Pow", base, exponent, returns=NumberKind,
    domain=Or(Ne(base, 0), Gt(re(exponent), 0)),
)

# An ordinary literal, used by -, / and unary minus. It prints as -1.
NegativeOne = NumberKind(-1)


def _subtract(a, b):
    """``a - b``."""
    return Add(a, Mul(NegativeOne, b))


def _divide(a, b):
    """``a / b``."""
    return Mul(a, Pow(b, NegativeOne))


def _negate(a):
    """``-a``."""
    return Mul(NegativeOne, a)


# What each operator builds when the left operand is a NumberKind. A BoolKind
# has none, so ``p + q`` on two BoolKinds is a TypeError.
set_operator(NumberKind, "+", Add)
set_operator(NumberKind, "*", Mul)
set_operator(NumberKind, "**", Pow)
set_operator(NumberKind, "-", _subtract)
set_operator(NumberKind, "/", _divide)
set_operator(NumberKind, "neg", _negate)


# Everything that holds for each function, in one place (see nary.identities).
a = NumberKind("a_")

declare_identities(Add, [
    associative,
    commutative,
    identity(0),
    inverse(Mul(-1, a)),          # a + (-1)*a = 0
    repeated(Mul(2, a)),          # a + a = 2*a
])

declare_identities(Mul, [
    associative,
    commutative,
    identity(1),
    absorbing(0),
    inverse(Pow(a, -1), when=Ne(a, 0)),
    repeated(Pow(a, 2)),          # a * a = a**2
    distributive(Add),
])

declare_identities(Pow, [
    Equal(Pow(a, 1), a, name="pow_one"),
    Equal(Pow(a, 0), 1, when=Ne(a, 0), name="pow_zero"),
])

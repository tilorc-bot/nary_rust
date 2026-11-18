"""Add, Mul and Pow, the literal -1, and the operators that build them.

There are no Sub, Div or Neg functions. As in SymPy, ``x - y`` is
``Add(x, Mul(-1, y))``, ``x / y`` is ``Mul(x, Pow(y, -1))`` and ``-x`` is
``Mul(-1, x)``, built by Python functions given to ``set_operator``.
"""

from ._core import declare_function, set_operator
from .domains import set_domain
from .elementary import re
from .kinds import NumberKind
from .logic import Or
from .relational import Gt, Ne

__all__ = ["Add", "Mul", "Pow", "NegativeOne"]

Add = declare_function("Add", rest=NumberKind, returns=NumberKind)
Mul = declare_function("Mul", rest=NumberKind, returns=NumberKind)
Pow = declare_function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp")
)

# Division is Pow(y, -1), so this is where division by zero is excluded.
# Under this rule 0**0 has no value.
set_domain(Pow, lambda base, exp: Or(Ne(base, 0), Gt(re(exp), 0)))

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

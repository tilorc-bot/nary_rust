"""Add, Mul and Pow, the literal -1, and the operators that build them.

There are no Sub, Div or Neg functions. As in SymPy, ``x - y`` is
``Add(x, Mul(-1, y))``, ``x / y`` is ``Mul(x, Pow(y, -1))`` and ``-x`` is
``Mul(-1, x)``, built by Python functions given to ``set_operator``.
"""

from ._core import set_operator
from .domains import declare_function
from .elementary import re
from .kinds import NumberKind
from .logic import Or, true
from .relational import Gt, Ne

__all__ = ["Add", "Mul", "Pow", "NegativeOne"]

Add = declare_function("Add", rest=NumberKind, returns=NumberKind, domain=lambda *args: true)
Mul = declare_function("Mul", rest=NumberKind, returns=NumberKind, domain=lambda *args: true)
# Division is Pow(y, -1), so the domain of Pow is where division by zero is
# excluded. Under it 0**0 has no value.
Pow = declare_function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp"),
    domain=lambda base, exp: Or(Ne(base, 0), Gt(re(exp), 0)),
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

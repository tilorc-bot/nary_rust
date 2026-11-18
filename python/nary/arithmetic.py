"""Add, Mul and Pow, the constant -1, and the operators that build them.

There are no Sub, Div or Neg functions. As in SymPy, ``x - y`` is
``Add(x, Mul(-1, y))``, ``x / y`` is ``Mul(x, Pow(y, -1))`` and ``-x`` is
``Mul(-1, x)``, built by Python functions given to ``set_operator``.
"""

from ._core import declare_function, set_operator
from .kinds import NumberKind

__all__ = ["Add", "Mul", "Pow", "NegativeOne"]

Add = declare_function("Add", rest=NumberKind, returns=NumberKind)
Mul = declare_function("Mul", rest=NumberKind, returns=NumberKind)
Pow = declare_function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp")
)

# A constant is a function of no arguments, applied once (as true/false in
# nary/logic.py). It prints as -1.
NegativeOne = declare_function("-1", returns=NumberKind)()


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

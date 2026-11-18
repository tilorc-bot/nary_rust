"""Add, Mul and Pow, and the operators that build them.

There are no functions for subtraction, division or negation. As in SymPy,
``x - y`` is ``Add(x, Mul(-1, y))``, ``x / y`` is ``Mul(x, Pow(y, -1))`` and
``-x`` is ``Mul(-1, x)``. The operators ``-``, ``/`` and unary minus (spelled
``"neg"``) are given Python functions below that build those expressions.
"""

from ._core import Integer, declare_function, set_operator
from .kinds import NumberKind

__all__ = ["Add", "Mul", "Pow"]

Add = declare_function("Add", rest=NumberKind, returns=NumberKind)
Mul = declare_function("Mul", rest=NumberKind, returns=NumberKind)
Pow = declare_function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp")
)

# Which function each operator builds when the left operand is a NumberKind.
# A BoolKind has none, so ``p + q`` on two BoolKinds is a TypeError.
set_operator(NumberKind, "+", Add)
set_operator(NumberKind, "*", Mul)
set_operator(NumberKind, "**", Pow)


def _subtract(a, b):
    """``a - b``, built as ``Add(a, Mul(-1, b))``."""
    return Add(a, Mul(Integer(-1), b))


def _divide(a, b):
    """``a / b``, built as ``Mul(a, Pow(b, -1))``."""
    return Mul(a, Pow(b, Integer(-1)))


def _negate(a):
    """``-a``, built as ``Mul(-1, a)``."""
    return Mul(Integer(-1), a)


# An operator can be given a Python function instead of a declared one: it
# is called with the operands, each int already an Integer, and returns the
# expression.
set_operator(NumberKind, "-", _subtract)
set_operator(NumberKind, "/", _divide)
set_operator(NumberKind, "neg", _negate)

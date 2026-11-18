"""Add, Mul and Pow, and the operators that build them."""

from ._core import declare_function, set_operator
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

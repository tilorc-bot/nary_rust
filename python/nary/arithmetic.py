"""Add, Mul and Pow, and the operators that build them."""

from ._core import function, set_operator
from .kinds import NumberKind

Add = function("Add", rest=NumberKind, returns=NumberKind)
Mul = function("Mul", rest=NumberKind, returns=NumberKind)
Pow = function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp")
)

# Which function each operator builds when the left operand is a NumberKind.
# A BoolKind has none, so ``p + q`` on two BoolKinds is a TypeError.
set_operator(NumberKind, "+", Add)
set_operator(NumberKind, "*", Mul)
set_operator(NumberKind, "**", Pow)

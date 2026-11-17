"""Add, Mul and Pow, and the operators that build them."""

from ._core import function, set_operator
from .kinds import NumberKind

Add = function("Add", rest=NumberKind, returns=NumberKind)
Mul = function("Mul", rest=NumberKind, returns=NumberKind)
Pow = function(
    "Pow", NumberKind, NumberKind, returns=NumberKind, names=("base", "exp")
)

# Which function each operator builds when the operand is a NumberKind.
set_operator(NumberKind, "+", Add)
set_operator(NumberKind, "*", Mul)
set_operator(NumberKind, "**", Pow)

# TODO: there is no - or /. An inert tree has to choose between separate Sub
# and Div functions and spellings such as Add(x, Mul(-1, y)) and
# Mul(x, Pow(y, -1)), and that has not been decided. Until then write the
# second form by hand.

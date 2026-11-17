"""Comparisons of numbers. Each returns a BoolKind."""

from ._core import function, set_operator
from .kinds import BoolKind, NumberKind

_sides = ("lhs", "rhs")

Lt = function("Lt", NumberKind, NumberKind, returns=BoolKind, names=_sides)
Gt = function("Gt", NumberKind, NumberKind, returns=BoolKind, names=_sides)
Le = function("Le", NumberKind, NumberKind, returns=BoolKind, names=_sides)
Ge = function("Ge", NumberKind, NumberKind, returns=BoolKind, names=_sides)

# == compares structure and returns a Python bool, so Eq has no operator.
Eq = function("Eq", NumberKind, NumberKind, returns=BoolKind, names=_sides)

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

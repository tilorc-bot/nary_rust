"""Comparisons of numbers. Each returns a BoolKind."""

from ._core import function, set_operator
from .kinds import BoolKind, NumberKind

__all__ = ["Eq", "Ge", "Gt", "Le", "Lt"]

Lt = function("Lt", NumberKind, NumberKind, returns=BoolKind)
Gt = function("Gt", NumberKind, NumberKind, returns=BoolKind)
Le = function("Le", NumberKind, NumberKind, returns=BoolKind)
Ge = function("Ge", NumberKind, NumberKind, returns=BoolKind)
# == compares structure and returns a Python bool, so Eq has no operator.
Eq = function("Eq", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

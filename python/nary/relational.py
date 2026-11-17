"""Comparisons of numbers. Each returns a BoolKind."""

from ._core import function, set_operator
from .kinds import BoolKind, NumberKind

__all__ = ["Eq", "Lt"]

Lt = function("Lt", NumberKind, NumberKind, returns=BoolKind)
# == compares structure and returns a Python bool, so Eq has no operator.
Eq = function("Eq", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))

set_operator(NumberKind, "<", Lt)

"""Comparisons of numbers. Each returns a BoolKind."""

from ._core import declare_function, set_operator
from .kinds import BoolKind, NumberKind

__all__ = ["Eq", "Ge", "Gt", "Le", "Lt", "Ne"]

Lt = declare_function("Lt", NumberKind, NumberKind, returns=BoolKind)
Gt = declare_function("Gt", NumberKind, NumberKind, returns=BoolKind)
Le = declare_function("Le", NumberKind, NumberKind, returns=BoolKind)
Ge = declare_function("Ge", NumberKind, NumberKind, returns=BoolKind)
# == and != compare structure and return a Python bool, so Eq and Ne have no
# operator.
Eq = declare_function("Eq", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))
Ne = declare_function("Ne", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

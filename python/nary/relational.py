"""Comparisons of numbers. Each returns a BoolKind."""

from ._core import set_operator
from .domains import declare_function
from .kinds import BoolKind, NumberKind
from .logic import true

__all__ = ["Eq", "Ge", "Gt", "Le", "Lt", "Ne"]

# No domain stated: issue #2 proposes that a comparison has a value only when
# both sides are real, which is not confirmed and cannot be written yet.
Lt = declare_function("Lt", NumberKind, NumberKind, returns=BoolKind, domain=None)
Gt = declare_function("Gt", NumberKind, NumberKind, returns=BoolKind, domain=None)
Le = declare_function("Le", NumberKind, NumberKind, returns=BoolKind, domain=None)
Ge = declare_function("Ge", NumberKind, NumberKind, returns=BoolKind, domain=None)
# == and != compare structure and return a Python bool, so Eq and Ne have no
# operator.
Eq = declare_function(
    "Eq", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"),
    domain=lambda lhs, rhs: true,
)
Ne = declare_function(
    "Ne", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"),
    domain=lambda lhs, rhs: true,
)

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

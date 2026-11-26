"""Comparisons of numbers, each returning a BoolKind, and ``re``, the real
part of a number, which the domains of the comparisons need."""

from ._core import declare_kind, set_operator
from .domains import declare_function
from .generic import concretize
from .kinds import BoolKind, NumberKind
from .logic import And, true

__all__ = ["AnyEq", "AnyNe", "Eq", "Ge", "Gt", "Le", "Lt", "Ne", "re"]

x = NumberKind("x")
lhs, rhs = NumberKind("lhs"), NumberKind("rhs")

# The real part of a number. It is declared here rather than in
# elementary.py, which imports this module for Ne.
re = declare_function("re", x, returns=NumberKind, domain=true)
# == and != compare structure and return a Python bool, so Eq and Ne have no
# operator.
K = declare_kind("K")
AnyEq = declare_function("Eq", K("lhs"), K("rhs"), returns=BoolKind, domain=true)
AnyNe = declare_function("Ne", K("lhs"), K("rhs"), returns=BoolKind, domain=true)
Eq, Ne = concretize(AnyEq, {K: NumberKind}), concretize(AnyNe, {K: NumberKind})
# A comparison has a value only when both sides are real, as in
# lean/Nary/Logic.lean. Issue #2 proposes this; the owner has not confirmed it.
both_real = And(Eq(re(lhs), lhs), Eq(re(rhs), rhs))
Lt = declare_function("Lt", lhs, rhs, returns=BoolKind, domain=both_real)
Gt = declare_function("Gt", lhs, rhs, returns=BoolKind, domain=both_real)
Le = declare_function("Le", lhs, rhs, returns=BoolKind, domain=both_real)
Ge = declare_function("Ge", lhs, rhs, returns=BoolKind, domain=both_real)

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

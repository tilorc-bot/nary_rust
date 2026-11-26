"""Comparisons of numbers, each returning a BoolKind, and ``re``, the real
part of a number, which the domains of the comparisons need."""

from ._core import set_operator
from .domains import Family, declare_function
from .kinds import BoolKind, NumberKind
from .logic import And, true

__all__ = ["Eq", "Equal", "Ge", "Gt", "Le", "Lt", "Ne", "re"]

x = NumberKind("x")
lhs, rhs = NumberKind("lhs"), NumberKind("rhs")

# The real part of a number. It is declared here rather than in
# elementary.py, which imports this module for Ne.
re = declare_function("re", x, returns=NumberKind, domain=true)
# == and != compare structure and return a Python bool, so Eq and Ne have no
# operator.
Eq = declare_function("Eq", lhs, rhs, returns=BoolKind, domain=true)
Ne = declare_function("Ne", lhs, rhs, returns=BoolKind, domain=true)
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


_equal_functions = Family("Equal", lambda kind: ((kind("lhs"), kind("rhs")), BoolKind, true))


def Equal(lhs, rhs):
    """Both sides have no value, or the same value, for any kind; Eq is for numbers with values:

    >>> from nary import Lambda
    >>> from nary.logic import Not, false
    >>> x = NumberKind("x")
    >>> Equal(x / x, 1), Equal(true, Not(false)).kind, Equal(Lambda(x, x), Lambda(x, x * 1)).lhs
    (Equal(Mul(x, Pow(x, -1)), 1), BoolKind, Lambda(x, x))
    """
    return _equal_functions(lhs.kind)(lhs, rhs)

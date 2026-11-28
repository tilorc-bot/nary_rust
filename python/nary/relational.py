from ._core import set_operator
from .domains import declare_function
from .kinds import BoolKind, NumberKind
from .logic import And, false, true
from .properties import declare_properties

__all__ = ["Eq", "Ge", "Gt", "Le", "Lt", "Ne", "re"]

x = NumberKind("x")
lhs, rhs = NumberKind("lhs"), NumberKind("rhs")

re = declare_function("re", x, returns=NumberKind, domain=true)
Eq = declare_function("Eq", lhs, rhs, returns=BoolKind, domain=true)
Ne = declare_function("Ne", lhs, rhs, returns=BoolKind, domain=true)
both_real = And(Eq(re(lhs), lhs), Eq(re(rhs), rhs))
Lt = declare_function("Lt", lhs, rhs, returns=BoolKind, domain=both_real)
Gt = declare_function("Gt", lhs, rhs, returns=BoolKind, domain=both_real)
Le = declare_function("Le", lhs, rhs, returns=BoolKind, domain=both_real)
Ge = declare_function("Ge", lhs, rhs, returns=BoolKind, domain=both_real)

declare_properties(re, evaluate_literals=NumberKind)
declare_properties(Eq, evaluate_literals=lambda a, b: _true_or_false(a == b))
declare_properties(Ne, evaluate_literals=lambda a, b: _true_or_false(a != b))
declare_properties(Lt, evaluate_literals=lambda a, b: _true_or_false(a < b))
declare_properties(Gt, evaluate_literals=lambda a, b: _true_or_false(a > b))
declare_properties(Le, evaluate_literals=lambda a, b: _true_or_false(a <= b))
declare_properties(Ge, evaluate_literals=lambda a, b: _true_or_false(a >= b))

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)


def _true_or_false(holds):
    """true where holds is True, false elsewhere.

    >>> _true_or_false(1 < 2), _true_or_false(2 < 2)
    (true, false)
    """
    return true if holds else false

import operator

from ._core import set_operator
from .domains import declare_function
from .kinds import BoolKind, NumberKind
from .logic import And, true

__all__ = ["Eq", "Ge", "Gt", "Le", "Lt", "Ne", "re"]

x = NumberKind("x")
lhs, rhs = NumberKind("lhs"), NumberKind("rhs")


re = declare_function(
    "re", x, returns=NumberKind, domain=true, evaluate_literals=lambda value: value,
)
Eq = declare_function(
    "Eq", lhs, rhs, returns=BoolKind, domain=true, evaluate_literals=operator.eq,
)
Ne = declare_function(
    "Ne", lhs, rhs, returns=BoolKind, domain=true, evaluate_literals=operator.ne,
)
both_real = And(Eq(re(lhs), lhs), Eq(re(rhs), rhs))
Lt = declare_function(
    "Lt", lhs, rhs, returns=BoolKind, domain=both_real, evaluate_literals=operator.lt,
)
Gt = declare_function(
    "Gt", lhs, rhs, returns=BoolKind, domain=both_real, evaluate_literals=operator.gt,
)
Le = declare_function(
    "Le", lhs, rhs, returns=BoolKind, domain=both_real, evaluate_literals=operator.le,
)
Ge = declare_function(
    "Ge", lhs, rhs, returns=BoolKind, domain=both_real, evaluate_literals=operator.ge,
)

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

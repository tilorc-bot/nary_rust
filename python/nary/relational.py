import operator

from ._core import set_operator
from ._numbers import true_or_false
from .domains import declare_function
from .kinds import BoolKind, NumberKind
from .logic import And, true
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

declare_properties(re, value_of_literals=lambda value: NumberKind(value))
for comparison, compare in [
    (Eq, operator.eq), (Ne, operator.ne), (Lt, operator.lt),
    (Gt, operator.gt), (Le, operator.le), (Ge, operator.ge),
]:
    declare_properties(comparison, value_of_literals=true_or_false(compare))

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

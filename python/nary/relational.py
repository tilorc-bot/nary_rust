from ._core import set_operator
from .domains import declare_function
from .kinds import BoolKind, NumberKind
from .logic import And, true

__all__ = ["Eq", "Ge", "Gt", "Le", "Lt", "Ne", "re"]

arg = NumberKind("arg")
lhs, rhs = NumberKind("lhs"), NumberKind("rhs")

re = declare_function("re", arg, returns=NumberKind, domain=true)
Eq = declare_function("Eq", lhs, rhs, returns=BoolKind, domain=true)
Ne = declare_function("Ne", lhs, rhs, returns=BoolKind, domain=true)
both_real = And(Eq(re(lhs), lhs), Eq(re(rhs), rhs))
Lt = declare_function("Lt", lhs, rhs, returns=BoolKind, domain=both_real)
Gt = declare_function("Gt", lhs, rhs, returns=BoolKind, domain=both_real)
Le = declare_function("Le", lhs, rhs, returns=BoolKind, domain=both_real)
Ge = declare_function("Ge", lhs, rhs, returns=BoolKind, domain=both_real)

set_operator(NumberKind, "<", Lt)
set_operator(NumberKind, ">", Gt)
set_operator(NumberKind, "<=", Le)
set_operator(NumberKind, ">=", Ge)

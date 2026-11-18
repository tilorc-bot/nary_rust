"""Elementary functions, and the domains of those that are partial."""

from ._core import declare_function
from .domains import set_domain
from .kinds import NumberKind
from .relational import Ne

__all__ = ["cos", "exp", "log", "re", "sin", "tan"]

sin = declare_function("sin", NumberKind, returns=NumberKind)
cos = declare_function("cos", NumberKind, returns=NumberKind)
tan = declare_function("tan", NumberKind, returns=NumberKind)
exp = declare_function("exp", NumberKind, returns=NumberKind)
log = declare_function("log", NumberKind, returns=NumberKind)
# The real part of a number.
re = declare_function("re", NumberKind, returns=NumberKind)

set_domain(log, lambda x: Ne(x, 0))
set_domain(tan, lambda x: Ne(cos(x), 0))

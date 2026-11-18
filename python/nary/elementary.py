"""Elementary functions, each with its domain."""

from .domains import declare_function
from .kinds import NumberKind
from .logic import true
from .relational import Ne

__all__ = ["cos", "exp", "log", "re", "sin", "tan"]

sin = declare_function("sin", NumberKind, returns=NumberKind, domain=lambda x: true)
cos = declare_function("cos", NumberKind, returns=NumberKind, domain=lambda x: true)
tan = declare_function("tan", NumberKind, returns=NumberKind, domain=lambda x: Ne(cos(x), 0))
exp = declare_function("exp", NumberKind, returns=NumberKind, domain=lambda x: true)
log = declare_function("log", NumberKind, returns=NumberKind, domain=lambda x: Ne(x, 0))
# The real part of a number.
re = declare_function("re", NumberKind, returns=NumberKind, domain=lambda x: true)

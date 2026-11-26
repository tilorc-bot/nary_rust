from .domains import declare_function
from .kinds import NumberKind
from .logic import true
from .relational import Ne

__all__ = ["cos", "exp", "log", "sin", "tan"]

x = NumberKind("x")

sin = declare_function("sin", x, returns=NumberKind, domain=true)
cos = declare_function("cos", x, returns=NumberKind, domain=true)
tan = declare_function("tan", x, returns=NumberKind, domain=Ne(cos(x), 0))
exp = declare_function("exp", x, returns=NumberKind, domain=true)
log = declare_function("log", x, returns=NumberKind, domain=Ne(x, 0))

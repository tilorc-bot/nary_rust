from .domains import declare_function
from .kinds import NumberKind
from .logic import true
from .relational import Ne

__all__ = ["cos", "exp", "log", "sin", "tan"]

arg = NumberKind("arg")

sin = declare_function("sin", arg, returns=NumberKind, domain=true)
cos = declare_function("cos", arg, returns=NumberKind, domain=true)
tan = declare_function("tan", arg, returns=NumberKind, domain=Ne(cos(arg), 0))
exp = declare_function("exp", arg, returns=NumberKind, domain=true)
log = declare_function("log", arg, returns=NumberKind, domain=Ne(arg, 0))

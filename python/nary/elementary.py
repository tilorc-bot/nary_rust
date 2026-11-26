from .domains import declare_function
from .kinds import NumberKind
from .logic import true
from .relational import Eq, Ne, re

__all__ = [
    "Abs", "arg", "ceiling", "conjugate", "cos", "cosh", "exp", "floor", "im", "log",
    "sign", "sin", "sinh", "tan", "tanh",
]

x = NumberKind("x")

sin = declare_function("sin", x, returns=NumberKind, domain=true)
cos = declare_function("cos", x, returns=NumberKind, domain=true)
tan = declare_function("tan", x, returns=NumberKind, domain=Ne(cos(x), 0))
exp = declare_function("exp", x, returns=NumberKind, domain=true)
log = declare_function("log", x, returns=NumberKind, domain=Ne(x, 0))
sinh = declare_function("sinh", x, returns=NumberKind, domain=true)
cosh = declare_function("cosh", x, returns=NumberKind, domain=true)
tanh = declare_function("tanh", x, returns=NumberKind, domain=Ne(cosh(x), 0))
im = declare_function("im", x, returns=NumberKind, domain=true)
Abs = declare_function("Abs", x, returns=NumberKind, domain=true)
arg = declare_function("arg", x, returns=NumberKind, domain=Ne(x, 0))
conjugate = declare_function("conjugate", x, returns=NumberKind, domain=true)
sign = declare_function("sign", x, returns=NumberKind, domain=true)
floor = declare_function("floor", x, returns=NumberKind, domain=Eq(re(x), x))
ceiling = declare_function("ceiling", x, returns=NumberKind, domain=Eq(re(x), x))

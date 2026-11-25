"""Elementary functions, each with its domain. ``re`` is declared in
``relational.py``."""

from .domains import declare_function
from .identities import Equal, declare_identities, hole
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


# Everything that holds for each function, in one place (see nary.identities).
_a = hole(NumberKind, "a")

declare_identities(exp, [
    ("log", Equal(exp(log(_a)), _a, when=Ne(_a, 0))),
])

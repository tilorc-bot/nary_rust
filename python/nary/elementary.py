"""Elementary functions, each with its domain. ``re`` is declared in
``relational.py``."""

from .arithmetic import Add, Mul
from .constants import pi
from .domains import declare_function
from .identities import Equal, declare_identities
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
a = NumberKind("a_")

declare_identities(exp, [
    Equal(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
])

declare_identities(sin, [
    Equal(sin(0), 0),
    Equal(sin(Mul(-1, a)), Mul(-1, sin(a))),
    Equal(sin(Add(a, Mul(2, pi))), sin(a)),
])

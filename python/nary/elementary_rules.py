from .arithmetic import Add, Mul
from .constants import I, pi
from .elementary import cos, exp, log, sin, tan
from ._identities import declare_identities, maps, undoes
from .kinds import NumberKind
from .logic import And
from .relational import Gt, Le, Lt, re

a = NumberKind("a")
negative, imaginary = Mul(-1, a), re(Mul(-1, I, a))

declare_identities(exp, [
    maps(exp(a), a, Add, Mul, normal="merged"),
    maps(exp(a), a, Add(a, Mul(2, pi, I)), a, name="exp_periodic"),
    undoes(log(a)),
])
declare_identities(log, [
    maps(log(a), a, Mul, Add, when=Gt(a, 0)),
    undoes(exp(a), when=And(Lt(Mul(-1, pi), imaginary), Le(imaginary, pi))),
])
declare_identities(sin, [
    maps(sin(a), a, negative, negative, name="sin_odd"),
    maps(sin(a), a, Add(a, pi), negative, name="sin_antiperiodic"),
])
declare_identities(cos, [
    maps(cos(a), a, negative, a, name="cos_even"),
    maps(cos(a), a, Add(a, pi), negative, name="cos_antiperiodic"),
])
declare_identities(tan, [
    maps(tan(a), a, negative, negative, name="tan_odd"),
    maps(tan(a), a, Add(a, pi), a, name="tan_periodic"),
])

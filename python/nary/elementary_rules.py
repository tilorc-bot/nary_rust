"""The rules for sin, cos, tan, re and Derivative.

    >>> from nary import NumberKind, cos, pi, sin
    >>> from nary.elementary_rules import rules
    >>> from nary.rewriting import rewrite
    >>> x = NumberKind("x")
    >>> rewrite(sin(x) ** 2 + cos(x) ** 2, rules)
    1
    >>> rewrite(sin(pi / 6), rules)
    Pow(2, -1)
"""

from .arithmetic import Add, Mul, Pow
from .calculus import Derivative
from .constants import E, I, pi
from .elementary import cos, exp, sin, tan
from ._identities import Equal, declare_identities
from .kinds import Many, NumberKind
from .relational import Eq, Ge, Lt, re

a, b, c = NumberKind("a"), NumberKind("b"), NumberKind("c")
rest, cs = Many(NumberKind)("rest"), Many(NumberKind)("cs")
half = Pow(2, -1)
k = Mul(cs)
plus_k_pi = Add(Mul(pi, cs), rest)
minus_half_pi, plus_half_pi = Add(Mul(k - half, pi), rest), Add(Mul(k + half, pi), rest)
minus_pi, plus_pi = Add(Mul(k - 1, pi), rest), Add(Mul(k + 1, pi), rest)

sine = declare_identities(sin, [
    Equal(sin(Mul(c, rest)), -sin(Mul(-c, rest)), when=Lt(c, 0), name="sin_odd"),
    Equal(sin(plus_k_pi), cos(minus_half_pi), when=Ge(k, half), name="sin_shift_down"),
    Equal(sin(plus_k_pi), -cos(plus_half_pi), when=Lt(k, 0), name="sin_shift_up"),
    Equal(sin(0), 0, name="sin_zero"),
    Equal(sin(pi / 6), half, name="sin_pi_6"),
    Equal(sin(pi / 4), half * Pow(2, half), name="sin_pi_4"),
    Equal(sin(pi / 3), half * Pow(3, half), name="sin_pi_3"),
])
cosine = declare_identities(cos, [
    Equal(cos(Mul(c, rest)), cos(Mul(-c, rest)), when=Lt(c, 0), name="cos_even"),
    Equal(cos(plus_k_pi), -sin(minus_half_pi), when=Ge(k, half), name="cos_shift_down"),
    Equal(cos(plus_k_pi), sin(plus_half_pi), when=Lt(k, 0), name="cos_shift_up"),
    Equal(cos(0), 1, name="cos_zero"),
    Equal(cos(pi / 6), half * Pow(3, half), name="cos_pi_6"),
    Equal(cos(pi / 4), half * Pow(2, half), name="cos_pi_4"),
    Equal(cos(pi / 3), half, name="cos_pi_3"),
    Equal(sin(a) ** 2 + cos(a) ** 2, 1, name="pythagoras"),
    Equal(b * sin(a) ** 2 + b * cos(a) ** 2, b, name="pythagoras_scaled"),
    Equal(1 - sin(a) ** 2, cos(a) ** 2, name="one_minus_sin_squared"),
    Equal(1 - cos(a) ** 2, sin(a) ** 2, name="one_minus_cos_squared"),
])
tangent = declare_identities(tan, [
    Equal(tan(Mul(c, rest)), -tan(Mul(-c, rest)), when=Lt(c, 0), name="tan_odd"),
    Equal(tan(plus_k_pi), tan(minus_pi), when=Ge(k, 1), name="tan_period_down"),
    Equal(tan(plus_k_pi), tan(plus_pi), when=Lt(k, 0), name="tan_period_up"),
    Equal(tan(0), 0, name="tan_zero"),
    Equal(tan(pi / 4), 1, name="tan_pi_4"),
    Equal(sin(a) / cos(a), tan(a), name="sin_over_cos"),
])
real_part = declare_identities(re, [
    Equal(re(a), a, when=Eq(re(a), a), name="re_real"),
    Equal(re(pi), pi, name="re_pi"),
    Equal(re(E), E, name="re_e"),
    Equal(re(I), 0, name="re_i"),
    Equal(re(re(a)), re(a), name="re_re"),
    Equal(re(Add(a, rest)), re(a) + re(Add(rest)), name="re_add"),
])
derivative = declare_identities(Derivative, [
    Equal(Derivative(sin), cos, name="derivative_sin"),
    Equal(Derivative(exp), exp, name="derivative_exp"),
])

rules = sine + cosine + tangent + real_part + derivative

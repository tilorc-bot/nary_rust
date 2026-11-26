"""The rules for sin, cos, tan, re, log and Derivative that autosimp does not apply.

    >>> from nary import Eq, NumberKind, cos, exp, re, sin
    >>> from nary.elementary_rules import rules
    >>> from nary.rewriting import rewrite
    >>> x = NumberKind("x")
    >>> rewrite(re(re(sin(x))), rules), rewrite(re(exp(x)), rules, [Eq(re(x), x)].__contains__)
    (re(sin(x)), exp(x))
"""

from .arithmetic import Add, Mul
from .calculus import Derivative
from .constants import I, pi
from .elementary import cos, exp, log, sin, tan
from ._identities import Equal, declare_identities
from .kinds import Many, NumberKind
from .logic import And
from .relational import Eq, Gt, Lt, re
from .rules import rule

a, b, c, d, n = (NumberKind(s) for s in "abcdn")
rest = Many(NumberKind)("rest")
number_minus_term = Add(n, Mul(c, d, rest))
opposite_signs = And(Gt(exp(n), 1), Lt(exp(c), 1))

sign = [
    declare_identities(sin, [Equal(sin(number_minus_term), -sin(-number_minus_term),
                                   when=opposite_signs, name="sin_number_minus_term")]),
    declare_identities(cos, [Equal(cos(number_minus_term), cos(-number_minus_term),
                                   when=opposite_signs, name="cos_number_minus_term")]),
    declare_identities(tan, [Equal(tan(number_minus_term), -tan(-number_minus_term),
                                   when=opposite_signs, name="tan_number_minus_term")]),
]

real_part = declare_identities(re, [
    Equal(re(a), a, when=Eq(re(a), a), name="re_real"),
    Equal(re(re(a)), re(a), name="re_re"),
    Equal(re(Mul(a, b, rest)), a * re(Mul(b, rest)), when=Eq(re(a), a), name="re_real_factor"),
    Equal(re(exp(a)), exp(a), when=Eq(re(a), a), name="re_exp_real"),
])
logarithm = declare_identities(log, [
    Equal(log(a), log(-a) + I * pi, when=And(Lt(a, 0), Lt(exp(a), 1)), name="log_negative_number"),
])
derivative = declare_identities(Derivative, [
    Equal(Derivative(sin), cos, name="derivative_sin"),
    Equal(Derivative(exp), exp, name="derivative_exp"),
])

rules = [r for block in sign for r in block] + real_part + logarithm + derivative

pythagorean = [
    rule(sin(a) ** 2 + cos(a) ** 2, 1, name="pythagoras"),
    rule(b * sin(a) ** 2 + b * cos(a) ** 2, b, name="pythagoras_scaled"),
    rule(1 - sin(a) ** 2, cos(a) ** 2, name="one_minus_sin_squared"),
    rule(1 - cos(a) ** 2, sin(a) ** 2, name="one_minus_cos_squared"),
    rule(sin(a) / cos(a), tan(a), name="sin_over_cos"),
]
log_power = [
    rule(log(a ** b), b * log(a), when=And(Gt(a, 0), Eq(re(b), b)), name="log_pow"),
]

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

from fractions import Fraction

from .arithmetic import Add, Mul, Pow
from .calculus import Derivative
from .constants import E, I, pi
from .elementary import cos, exp, sin, tan
from ._identities import Equal, declare_identities
from .kinds import Many, NumberKind
from .logic import And
from .relational import Eq, Ge, Gt, Le, Lt, re

a, b, c, d, n = (NumberKind(s) for s in "abcdn")
rest, cs, r1, r2 = (Many(NumberKind)(s) for s in ("rest", "cs", "r1", "r2"))
half = Pow(2, -1)
k = Mul(cs)
k_pi = Mul(pi, cs)
plus_k_pi = Add(k_pi, b, rest)
minus_half_pi, plus_half_pi = Add(Mul(k - half, pi), b, rest), Add(Mul(k + half, pi), b, rest)
minus_pi, plus_pi = Add(Mul(k - 1, pi), b, rest), Add(Mul(k + 1, pi), b, rest)


def negative_number(t):
    return Lt(exp(t), 1)


def positive_number(t):
    return Gt(exp(t), 1)


C, D = Mul(c, r1), Mul(d, r2)
signed_arguments = [
    ("", Mul(c, rest), negative_number(c)),
    ("_two_negative_terms", Add(C, D), And(negative_number(c), negative_number(d))),
    ("_two_of_three_negative", Add(C, D, b), And(negative_number(c), negative_number(d))),
    ("_number_minus_term", Add(n, Mul(c, d, r1)), And(positive_number(n), negative_number(c))),
]


def odd(g, name):
    return [Equal(g(u), -g(-u), when=when, name=f"{name}{suffix}") for suffix, u, when in signed_arguments]


def even(g, name):
    return [Equal(g(u), g(-u), when=when, name=f"{name}{suffix}") for suffix, u, when in signed_arguments]


def sqrt(x):
    return Pow(x, half)


cosines = {
    Fraction(0): NumberKind(1),
    Fraction(1, 12): (sqrt(2) + sqrt(6)) / 4,
    Fraction(1, 10): sqrt(5 * Pow(8, -1) + sqrt(5) / 8),
    Fraction(1, 8): sqrt(half + sqrt(2) / 4),
    Fraction(1, 6): half * Pow(3, half),
    Fraction(1, 5): Pow(4, -1) + sqrt(5) / 4,
    Fraction(1, 4): half * Pow(2, half),
    Fraction(3, 10): sqrt(5 * Pow(8, -1) - sqrt(5) / 8),
    Fraction(1, 3): half,
    Fraction(3, 8): sqrt(half - sqrt(2) / 4),
    Fraction(2, 5): sqrt(5) / 4 - Pow(4, -1),
    Fraction(5, 12): (sqrt(6) - sqrt(2)) / 4,
    Fraction(1, 2): NumberKind(0),
}
tangents = {
    Fraction(1, 12): 2 - sqrt(3),
    Fraction(1, 10): sqrt(1 - 2 * sqrt(5) / 5),
    Fraction(1, 8): sqrt(2) - 1,
    Fraction(1, 6): sqrt(3) / 3,
    Fraction(1, 5): sqrt(5 - 2 * sqrt(5)),
    Fraction(1, 4): NumberKind(1),
    Fraction(3, 10): sqrt(1 + 2 * sqrt(5) / 5),
    Fraction(1, 3): sqrt(3),
    Fraction(3, 8): 1 + sqrt(2),
    Fraction(2, 5): sqrt(5 + 2 * sqrt(5)),
    Fraction(5, 12): 2 + sqrt(3),
}


def times_pi(q):
    return pi / q.denominator if q.numerator == 1 else Mul(q.numerator, pi, Pow(q.denominator, -1))


def table(g, name, values):
    return [
        Equal(g(times_pi(q)), v, name=f"{name}_pi_{q.denominator}" if q.numerator == 1
              else f"{name}_{q.numerator}pi_{q.denominator}")
        for q, v in values.items() if q
    ]


above_half, above_one = Gt(k - half, 0), Gt(k - 1, 0)
reflected = And(above_half, Le(k, 1))

sine = declare_identities(sin, [
    Equal(sin(k_pi), -sin(Mul(k - 1, pi)), when=above_one, name="sin_minus_pi"),
    Equal(sin(k_pi), sin(Mul(1 - k, pi)), when=reflected, name="sin_reflect"),
    Equal(sin(plus_k_pi), cos(minus_half_pi), when=Ge(k - half, 0), name="sin_shift_down"),
    Equal(sin(plus_k_pi), -cos(plus_half_pi), when=Lt(k, 0), name="sin_shift_up"),
    *odd(sin, "sin_odd"),
    Equal(sin(0), 0, name="sin_zero"),
    *table(sin, "sin", {Fraction(1, 2) - q: v for q, v in cosines.items()}),
])
cosine = declare_identities(cos, [
    Equal(cos(k_pi), -cos(Mul(k - 1, pi)), when=above_one, name="cos_minus_pi"),
    Equal(cos(k_pi), -cos(Mul(1 - k, pi)), when=reflected, name="cos_reflect"),
    Equal(cos(plus_k_pi), -sin(minus_half_pi), when=Ge(k - half, 0), name="cos_shift_down"),
    Equal(cos(plus_k_pi), sin(plus_half_pi), when=Lt(k, 0), name="cos_shift_up"),
    *even(cos, "cos_even"),
    Equal(cos(0), 1, name="cos_zero"),
    *table(cos, "cos", cosines),
    Equal(sin(a) ** 2 + cos(a) ** 2, 1, name="pythagoras"),
    Equal(b * sin(a) ** 2 + b * cos(a) ** 2, b, name="pythagoras_scaled"),
    Equal(1 - sin(a) ** 2, cos(a) ** 2, name="one_minus_sin_squared"),
    Equal(1 - cos(a) ** 2, sin(a) ** 2, name="one_minus_cos_squared"),
])
tangent = declare_identities(tan, [
    Equal(tan(k_pi), tan(Mul(k - 1, pi)), when=above_one, name="tan_minus_pi"),
    Equal(tan(k_pi), -tan(Mul(1 - k, pi)), when=reflected, name="tan_reflect"),
    Equal(tan(plus_k_pi), tan(minus_pi), when=Ge(k - 1, 0), name="tan_period_down"),
    Equal(tan(plus_k_pi), tan(plus_pi), when=Lt(k + half, 0), name="tan_period_up"),
    *odd(tan, "tan_odd"),
    Equal(tan(0), 0, name="tan_zero"),
    *table(tan, "tan", tangents),
    Equal(sin(a) / cos(a), tan(a), name="sin_over_cos"),
])
real_part = declare_identities(re, [
    Equal(re(a), a, when=Eq(re(a), a), name="re_real"),
    Equal(re(pi), pi, name="re_pi"),
    Equal(re(E), E, name="re_e"),
    Equal(re(I), 0, name="re_i"),
    Equal(re(re(a)), re(a), name="re_re"),
    Equal(re(Add(a, b, rest)), re(a) + re(Add(b, rest)), name="re_add"),
    Equal(re(Mul(a, b, rest)), a * re(Mul(b, rest)), when=Eq(re(a), a), name="re_real_factor"),
    Equal(re(exp(a)), exp(a), when=Eq(re(a), a), name="re_exp_real"),
])
derivative = declare_identities(Derivative, [
    Equal(Derivative(sin), cos, name="derivative_sin"),
    Equal(Derivative(exp), exp, name="derivative_exp"),
])

rules = sine + cosine + tangent + real_part + derivative

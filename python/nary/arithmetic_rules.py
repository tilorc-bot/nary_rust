"""Add is recorded as unordered and flat, and Pow is not unordered.

    >>> from nary import Add, NumberKind, Pow
    >>> from nary.arithmetic_rules import rules
    >>> from nary.rules import is_flat, is_unordered
    >>> is_unordered(Add), is_flat(Add), is_unordered(Pow)
    (True, True, False)

The rule a * 0 -> 0 erases a.

    >>> a = NumberKind("a")
    >>> [(r, r.erased) for r in rules if r.pattern == a * 0]
    [(Rule(Mul(a, 0), 0, name='mul_absorbing'), (a,))]

"""

from .arithmetic import Add, Mul, Pow
from .constants import E, I, pi
from .elementary import exp, log
from ._identities import (
    Equal, absorbing, associative, commutative, declare_identities, identity, inverse,
)
from .kinds import Many, NumberKind
from .logic import And
from .relational import Eq, Gt, Le, Lt, Ne, re

a, b, c = NumberKind("a"), NumberKind("b"), NumberKind("c")
rest, cs = Many(NumberKind)("rest"), Many(NumberKind)("cs")
half, k = Pow(2, -1), Mul(cs)

add = declare_identities(Add, [
    associative,
    commutative,
    identity(0),
    Equal(a + a, 2 * a, name="add_self"),
    inverse(Mul(-1, a)),
])
mul = declare_identities(Mul, [
    associative,
    commutative,
    identity(1),
    absorbing(0),
    inverse(Pow(a, -1), when=Ne(a, 0)),
])
power = declare_identities(Pow, [
    Equal(a ** 1, a, name="pow_one"),
    Equal(a ** 0, 1, when=Ne(a, 0), name="pow_zero"),
    Equal(1 ** a, 1, name="one_pow"),
    Equal(0 ** a, 0, when=Gt(re(a), 0), name="zero_pow"),
    Equal(E ** a, exp(a), name="pow_e"),
    Equal(a ** b, exp(b * log(a)), when=And(Ne(a, 0), Ne(re(b), b)), name="pow_complex"),
])
exponential = declare_identities(exp, [
    Equal(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
    Equal(exp(Mul(log(a), cs)), a ** k, when=And(Ne(a, 0), Eq(re(k), k)), name="exp_log_power"),
    Equal(exp(0), 1, name="exp_zero"),
    Equal(exp(1), E, name="exp_one"),
    Equal(exp(a) ** b, exp(a * b), when=Eq(re(a), a), name="exp_pow"),
    Equal(exp(Add(Mul(I, pi, cs), rest)), exp(Add(Mul(k - 2, I, pi), rest)),
          when=Gt(k, 1), name="exp_period_down"),
    Equal(exp(Add(Mul(I, pi, cs), rest)), exp(Add(Mul(k + 2, I, pi), rest)),
          when=Le(k, -1), name="exp_period_up"),
    Equal(exp(Add(I * pi, rest)), -exp(Add(rest)), name="exp_i_pi"),
    Equal(exp(Add(Mul(half, I, pi), rest)), I * exp(Add(rest)), name="exp_half_i_pi"),
    Equal(exp(Add(Mul(-1, half, I, pi), rest)), -I * exp(Add(rest)), name="exp_minus_half_i_pi"),
])
logarithm = declare_identities(log, [
    Equal(log(1), 0, name="log_one"),
    Equal(log(E), 1, name="log_e"),
    Equal(log(exp(a)), a, when=Eq(re(a), a), name="log_exp"),
    Equal(log(a), log(-a) + I * pi, when=And(Lt(a, 0), Lt(exp(a), 1)), name="log_negative_number"),
    Equal(log(I), Mul(half, I, pi), name="log_i"),
    Equal(log(-I), Mul(-1, half, I, pi), name="log_minus_i"),
    Equal(log(a ** b), b * log(a), when=And(Gt(a, 0), Eq(re(b), b)), name="log_pow"),
])

rules = add + mul + power + exponential + logarithm

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
from .elementary import exp, log
from ._identities import (
    Equal, absorbing, associative, commutative, declare_identities, identity, inverse, repeats,
)
from .kinds import NumberKind
from .relational import Ne

a, n = NumberKind("a"), NumberKind("n")

add = declare_identities(Add, [
    associative,
    commutative,
    identity(0),
    repeats(Mul(n, a), n, name="add_self"),
    inverse(Mul(-1, a)),
])
mul = declare_identities(Mul, [
    associative,
    commutative,
    identity(1),
    absorbing(0),
    repeats(Pow(a, n), n),
    inverse(Pow(a, -1), when=Ne(a, 0)),
])
power = declare_identities(Pow, [
    Equal(a ** 1, a, name="pow_one"),
    Equal(a ** 0, 1, when=Ne(a, 0), name="pow_zero"),
])
exponential = declare_identities(exp, [
    Equal(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
])

rules = add + mul + power + exponential

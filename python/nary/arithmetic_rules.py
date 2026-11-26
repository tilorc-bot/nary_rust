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
from .constants import I, pi
from .elementary import exp
from ._identities import (
    absorbing, associative, commutative, composes, declare_identities, identity, inverse, maps,
    repeats,
)
from .kinds import NumberKind
from .relational import Eq, Gt, Ne

a, n = NumberKind("a"), NumberKind("n")
whole = Eq(exp(Mul(2, pi, I, n)), 1)

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
declare_identities(Pow, [
    maps(Pow(a, n), a, Mul, Mul, normal="split", when=whole, name="pow_whole_split"),
    maps(Pow(a, n), a, Mul, Mul, normal="split", when=Gt(a, 0), name="pow_positive_split"),
    composes(Pow(a, n), n, Mul, when=whole),
])

rules = add + mul

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
from ._identities import (
    absorbing, associative, commutative, declare_identities, identity, inverse, left_absorbing,
    right_identity,
)
from .kinds import NumberKind
from .relational import Ne

a = NumberKind("a")

add = declare_identities(Add, [
    associative,
    commutative,
    identity(0),
    inverse(Mul(-1, a)),
])
mul = declare_identities(Mul, [
    associative,
    commutative,
    identity(1),
    absorbing(0),
    inverse(Pow(a, -1), when=Ne(a, 0)),
])
power = declare_identities(Pow, [right_identity(1), left_absorbing(1)])

rules = add + mul + power

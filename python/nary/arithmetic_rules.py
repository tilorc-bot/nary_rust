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
from .kinds import NumberKind
from .properties import declare_properties, property_rules
from .relational import Ne
from .rules import rule

a = NumberKind("a")

declare_properties(Add, is_associative=True, is_commutative=True, identity_element=0)
declare_properties(
    Mul, is_associative=True, is_commutative=True, identity_element=1, absorbing_element=0
)

add = property_rules(Add) + [
    rule(a + a, 2 * a, name="add_self"),
    rule(Add(a, Mul(-1, a)), Add.identity_element, name="add_inverse"),
]
mul = property_rules(Mul) + [
    rule(Mul(a, Pow(a, -1)), Mul.identity_element, when=Ne(a, 0), name="mul_inverse"),
]
power = [
    rule(a ** 1, a, name="pow_one"),
    rule(a ** 0, 1, when=Ne(a, 0), name="pow_zero"),
]
exponential = [
    rule(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
]

rules = add + mul + power + exponential

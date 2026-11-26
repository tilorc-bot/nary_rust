"""Add is recorded as unordered and flat, and Pow is not unordered.

    >>> from nary import Add, NumberKind, Pow
    >>> from nary.arithmetic_rules import rules
    >>> from nary.rules import is_flat, is_unordered
    >>> is_unordered(Add), is_flat(Add), is_unordered(Pow)
    (True, True, False)

The rule a * 0 -> 0 erases a.

    >>> a = NumberKind("a")
    >>> [(r, r.erased) for r in rules if r.pattern == a * 0]
    [(Rule(Mul(a, 0), 0, name='mul_zero'), (a,))]

"""

from .arithmetic import Add, Mul
from .elementary import exp, log
from .kinds import NumberKind
from .relational import Ne
from .rules import flat, rule, unordered

a = NumberKind("a")

unordered(Add)
flat(Add)
unordered(Mul)
flat(Mul)

rules = [
    rule(a + 0, a, name="add_zero"),
    rule(a * 1, a, name="mul_one"),
    rule(a * 0, 0, name="mul_zero"),
    rule(a + a, 2 * a, name="add_self"),
    rule(a - a, 0, name="sub_self"),
    rule(a / a, 1, when=Ne(a, 0), name="div_self"),
    rule(a ** 1, a, name="pow_one"),
    rule(a ** 0, 1, when=Ne(a, 0), name="pow_zero"),
    rule(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
]

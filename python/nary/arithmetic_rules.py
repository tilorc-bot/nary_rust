"""Rules about numbers: the facts about ``Add`` and ``Mul``, and the first
rewrite rules.

Importing this module records them with ``nary.rules``. Each rule is sound
by the definitions in ``lean/Nary/Number.lean``: wherever its condition
holds and its erased variables have a value, both sides have no value or
both have the same value (see ``nary.rules``). None of them is proved in
Lean yet except ``a + 0 -> a``, ``0 * a -> 0`` and ``a / a -> 1``, in
``lean/Nary/Rules.lean``.

    >>> import nary.arithmetic_rules
    >>> from nary import Add, NumberKind, Pow
    >>> from nary.rules import is_flat, is_unordered, rules
    >>> is_unordered(Add), is_flat(Add), is_unordered(Pow)
    (True, True, False)
    >>> a = NumberKind("a")
    >>> [(r, r.erased) for r in rules() if r.pattern == 0 * a]
    [(Rule(Mul(0, a), 0), (a,))]

``a ** 0 -> 1`` needs ``Ne(a, 0)`` because ``0**0`` has no value here: there
is no separate power with a natural-number exponent yet.
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

rule(a + 0, a)
rule(a * 1, a)
rule(0 * a, 0)
rule(a + a, 2 * a)
rule(a - a, 0)
rule(a / a, 1, when=Ne(a, 0))
rule(a ** 1, a)
rule(a ** 0, 1, when=Ne(a, 0))
rule(exp(log(a)), a, when=Ne(a, 0))

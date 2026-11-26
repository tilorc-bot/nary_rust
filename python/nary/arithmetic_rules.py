"""Rules about numbers: the facts about ``Add`` and ``Mul``, and the first
rewrite rules.

Importing this module records the facts. The rules are the list ``rules``,
which is what ``nary.rewriting.rewrite`` is given.

Every rule and every fact here is proved in Lean, from the definitions in
``lean/Nary/Number.lean``. For a rule that means: wherever its condition
holds and its erased variables have a value, both sides have no value or
both have the same value (see ``nary.rules``). The Lean statements are
printed from this file: ``lean/generate_rules.py`` writes them to
``lean/Nary/ArithmeticRules/Statements.lean``, and the proofs are written by
hand in ``lean/Nary/ArithmeticRules.lean``. The name of a rule is the name
of its theorem, ``Nary.ArithmeticRules.pow_one`` and so on, and every rule
here needs one. After changing or adding a rule, run that script and prove
the new statement; until then ``tests/test_lean.py`` fails (the script was
not run) or ``lake build`` fails (a statement has no proof that fits).
``lean/README.md`` explains the arrangement.

    >>> from nary import Add, NumberKind, Pow
    >>> from nary.arithmetic_rules import rules
    >>> from nary.rules import is_flat, is_unordered
    >>> is_unordered(Add), is_flat(Add), is_unordered(Pow)
    (True, True, False)
    >>> a = NumberKind("a")
    >>> [(r, r.erased) for r in rules if r.pattern == a * 0]
    [(Rule(Mul(a, 0), 0, name='mul_absorbing'), (a,))]

``a ** 0 -> 1`` needs ``Ne(a, 0)`` because ``0**0`` has no value here: there
is no separate power with a natural-number exponent yet.
"""

from .arithmetic import Add, Mul, Pow
from .elementary import exp, log
from .identities import (
    Equal, absorbing, associative, commutative, declare_identities, identity, inverse,
)
from .kinds import NumberKind
from .relational import Ne

a = NumberKind("a")

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
])
exponential = declare_identities(exp, [
    Equal(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
])

rules = add + mul + power + exponential

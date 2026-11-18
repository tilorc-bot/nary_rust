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
of its theorem, ``Nary.ArithmeticRules.add_zero`` and so on, and every rule
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
    [(Rule(Mul(a, 0), 0, name='mul_zero'), (a,))]

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

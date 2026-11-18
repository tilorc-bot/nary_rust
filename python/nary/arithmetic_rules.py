"""Rules about numbers: the facts about ``Add`` and ``Mul``, and the first
rewrite rules.

Importing this module records the facts, and what ``Add`` and ``Mul`` do on
integers (``computes``). The rules are the list ``rules``,
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

The last four rules do arithmetic on literals. ``computed(m + n)`` is the
literal whose value is ``m + n``, worked out with Python integers, and
``m`` and ``n`` match only literals:

    >>> from nary.rewriting import rewrite
    >>> x = NumberKind("x")
    >>> rewrite(Add(x, 2, 3), rules), rewrite(2 * x + 3 * x, rules)
    (Add(x, 5), Mul(5, x))

``a ** 0 -> 1`` needs ``Ne(a, 0)`` because ``0**0`` has no value here: there
is no separate power with a natural-number exponent yet.
"""

import math

from .arithmetic import Add, Mul
from .elementary import exp, log
from .kinds import NumberKind
from .relational import Ne
from .rules import computed, computes, flat, rule, unordered

a = NumberKind("a")
# Literal variables: each appears inside computed(...), so matches only a literal.
m, n = NumberKind("m"), NumberKind("n")

unordered(Add)
flat(Add)
unordered(Mul)
flat(Mul)

# What Add and Mul do on integers, for computed(...). nary.lean prints them
# as + and * on Lean's ℤ; that the two agree is taken on trust.
computes(Add, lambda *integers: sum(integers))
computes(Mul, lambda *integers: math.prod(integers))

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
    rule(m + n, computed(m + n), name="add_literals"),
    rule(m * n, computed(m * n), name="mul_literals"),
    rule(m * a + n * a, computed(m + n) * a, name="collect"),
    rule(a + n * a, computed(n + 1) * a, name="collect_one"),
]

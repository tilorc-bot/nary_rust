"""The rewrite rules about numbers, as the list ``rules``, which is what
``nary.rewriting.rewrite`` is given.

The rules are not written here: they come from the identities listed for
``Add``, ``Mul``, ``Pow`` and ``exp`` in ``nary.arithmetic`` and
``nary.elementary`` (see ``nary.identities``), through
``nary.rules.identity_rules``. Each rule is named after its identity. The
facts that ``Add`` and ``Mul`` are unordered and flat come from the same
blocks, which list ``commutative`` and ``associative``.

Every identity, and every rule the engine applies, is proved in Lean
(``lean/README.md``): ``lean/generate_rules.py`` writes the statements to
``lean/Nary/ArithmeticRules/Statements.lean`` and the proofs are written by
hand in ``lean/Nary/ArithmeticRules.lean``.

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
from .elementary import exp
from .rules import identity_rules

rules = identity_rules(Add) + identity_rules(Mul) + identity_rules(Pow) + identity_rules(exp)

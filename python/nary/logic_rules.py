"""A relation is true or false where holds decides it.

    >>> from nary import Gt, NumberKind
    >>> from nary.logic_rules import rules
    >>> from nary.rewriting import rewrite
    >>> x = NumberKind("x")
    >>> rewrite(x**2 >= 0, rules, [Gt(x, 0)].__contains__), rewrite(x < 0, rules, [Gt(x, 0)].__contains__)
    (true, false)
"""

from ._identities import associative, commutative, declare_identities, identity
from .kinds import BoolKind, Many, NumberKind
from .logic import And, Not, Or, false, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne
from .rules import rule

p, q = BoolKind("p"), BoolKind("q")
ps = Many(BoolKind)("ps")
a, b = NumberKind("a"), NumberKind("b")

declare_identities(And, [associative, commutative, identity(true)])
declare_identities(Or, [associative, commutative, identity(false)])

OPPOSITE = {Eq: Ne, Ne: Eq, Lt: Ge, Le: Gt, Gt: Le, Ge: Lt}

rules = [
    r for relation, opposite in OPPOSITE.items() for r in (
        rule(relation(a, b), true, when=relation(a, b), name=f"{relation.name.lower()}_holds"),
        rule(relation(a, b), false, when=opposite(a, b), name=f"{relation.name.lower()}_fails"),
    )
]

to_nnf = [
    rule(Not(And(p, q, ps)), Or(Not(p), Not(And(q, ps))), name="to_nnf_not_and"),
    rule(Not(Or(p, q, ps)), And(Not(p), Not(Or(q, ps))), name="to_nnf_not_or"),
    rule(And(p, Not(p)), false, name="to_nnf_contradiction"),
    rule(Or(p, Not(p)), true, name="to_nnf_excluded_middle"),
]
simplify_logic = to_nnf + [
    rule(And(p, Or(p, ps)), p, name="simplify_logic_and_absorption"),
    rule(Or(p, And(p, ps)), p, name="simplify_logic_or_absorption"),
]

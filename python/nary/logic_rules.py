"""The rules for And, Or, Not and the relations.

    >>> from nary import BoolKind, NumberKind
    >>> from nary.logic import And, Not, Or, false, true
    >>> from nary.logic_rules import rules
    >>> from nary.rewriting import rewrite
    >>> p, q, x, y = BoolKind("p"), BoolKind("q"), NumberKind("x"), NumberKind("y")
    >>> rewrite(And(p, Or(q, true), Not(Not(p))), rules)
    p
    >>> rewrite(Not(x < y), rules)
    Ge(x, y)
"""

from ._identities import (
    Equal, absorbing, associative, commutative, declare_identities, idempotent, identity,
)
from .kinds import BoolKind, Many, NumberKind
from .logic import And, Not, Or, false, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re

p, q = BoolKind("p"), BoolKind("q")
ps = Many(BoolKind)("ps")
a, b = NumberKind("a"), NumberKind("b")
real = Eq(re(a), a)

conjunction = declare_identities(And, [
    associative,
    commutative,
    identity(true),
    absorbing(false),
    idempotent,
    Equal(And(), true, name="and_empty"),
    Equal(And(p), p, name="and_single"),
    Equal(And(p, Not(p)), false, name="and_contradiction"),
    Equal(And(p, Or(p, ps)), p, name="and_absorption"),
])
disjunction = declare_identities(Or, [
    associative,
    commutative,
    identity(false),
    absorbing(true),
    idempotent,
    Equal(Or(), false, name="or_empty"),
    Equal(Or(p), p, name="or_single"),
    Equal(Or(p, Not(p)), true, name="or_excluded_middle"),
    Equal(Or(p, And(p, ps)), p, name="or_absorption"),
])
negation = declare_identities(Not, [
    Equal(Not(Not(p)), p, name="not_not"),
    Equal(Not(true), false, name="not_true"),
    Equal(Not(false), true, name="not_false"),
    Equal(Not(Eq(a, b)), Ne(a, b), name="not_eq"),
    Equal(Not(Ne(a, b)), Eq(a, b), name="not_ne"),
    Equal(Not(Lt(a, b)), Ge(a, b), name="not_lt"),
    Equal(Not(Le(a, b)), Gt(a, b), name="not_le"),
    Equal(Not(Gt(a, b)), Le(a, b), name="not_gt"),
    Equal(Not(Ge(a, b)), Lt(a, b), name="not_ge"),
    Equal(Not(And(p, ps)), Or(Not(p), Not(And(ps))), name="not_and"),
    Equal(Not(Or(p, ps)), And(Not(p), Not(Or(ps))), name="not_or"),
])
equality = declare_identities(Eq, [Equal(Eq(a, a), true, name="eq_self")])
inequality = declare_identities(Ne, [Equal(Ne(a, a), false, name="ne_self")])
less = declare_identities(Lt, [Equal(Lt(a, a), false, when=real, name="lt_self")])
less_or_equal = declare_identities(Le, [Equal(Le(a, a), true, when=real, name="le_self")])
greater = declare_identities(Gt, [Equal(Gt(a, a), false, when=real, name="gt_self")])
greater_or_equal = declare_identities(Ge, [Equal(Ge(a, a), true, when=real, name="ge_self")])

rules = (
    conjunction + disjunction + negation
    + equality + inequality + less + less_or_equal + greater + greater_or_equal
)

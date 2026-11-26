"""The rules for And, Or, Not and the relations.

    >>> from nary import BoolKind, NumberKind
    >>> from nary.logic import And, Not, Or, false, true
    >>> from nary.logic_rules import rules
    >>> from nary.rewriting import rewrite
    >>> p, q, x, y = BoolKind("p"), BoolKind("q"), NumberKind("x"), NumberKind("y")
    >>> rewrite(And(p, Or(q, x < y, true), Not(Not(p))), rules), rewrite(Not(And(p, p)), rules)
    (p, Not(p))
    >>> rewrite(Not(x < y), rules)
    Ge(x, y)
"""

from ._identities import (
    Equal,
    absorbing,
    associative,
    commutative,
    declare_identities,
    idempotent,
    identity,
)
from .kinds import BoolKind, Many, NumberKind
from .logic import And, Not, Or, false, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re
from .rules import rule

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
])
disjunction = declare_identities(Or, [
    associative,
    commutative,
    identity(false),
    absorbing(true),
    idempotent,
    Equal(Or(), false, name="or_empty"),
    Equal(Or(p), p, name="or_single"),
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
])
equality = declare_identities(Eq, [
    Equal(Eq(a, a), true, name="eq_self"),
    Equal(Eq(a, b), true, when=Eq(a, b), name="eq_holds"),
    Equal(Eq(a, b), false, when=Ne(a, b), name="eq_fails"),
])
inequality = declare_identities(Ne, [
    Equal(Ne(a, a), false, name="ne_self"),
    Equal(Ne(a, b), true, when=Ne(a, b), name="ne_holds"),
    Equal(Ne(a, b), false, when=Eq(a, b), name="ne_fails"),
])
less = declare_identities(Lt, [
    Equal(Lt(a, a), false, when=real, name="lt_self"),
    Equal(Lt(a, b), true, when=Lt(a, b), name="lt_holds"),
    Equal(Lt(a, b), false, when=Ge(a, b), name="lt_fails"),
])
less_or_equal = declare_identities(Le, [
    Equal(Le(a, a), true, when=real, name="le_self"),
    Equal(Le(a, b), true, when=Le(a, b), name="le_holds"),
    Equal(Le(a, b), false, when=Gt(a, b), name="le_fails"),
])
greater = declare_identities(Gt, [
    Equal(Gt(a, a), false, when=real, name="gt_self"),
    Equal(Gt(a, b), true, when=Gt(a, b), name="gt_holds"),
    Equal(Gt(a, b), false, when=Le(a, b), name="gt_fails"),
])
greater_or_equal = declare_identities(Ge, [
    Equal(Ge(a, a), true, when=real, name="ge_self"),
    Equal(Ge(a, b), true, when=Ge(a, b), name="ge_holds"),
    Equal(Ge(a, b), false, when=Lt(a, b), name="ge_fails"),
])

rules = (
    conjunction + disjunction + negation
    + equality + inequality + less + less_or_equal + greater + greater_or_equal
)

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

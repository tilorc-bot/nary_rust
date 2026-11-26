import pytest

from nary import BoolKind, E, I, Mul, NumberKind, Pow, cos, exp, log, pi, re, sin, tan
from nary import arithmetic_rules, elementary_rules, logic_rules
from nary.calculus import Derivative
from nary.logic import And, Not, Or, false, true
from nary.normal import normal
from nary.relational import Eq, Ge, Gt, Lt, Ne
from nary.rewriting import rewrite
from nary.rules import Rule
from nary.simplify import simplify

LISTS = [arithmetic_rules.rules, elementary_rules.rules, logic_rules.rules]
RULES = [r for rules in LISTS for r in rules]

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
p, q = BoolKind("p"), BoolKind("q")


def symbols(e):
    if e.is_symbol:
        yield e
    elif e.head is not None:
        yield from symbols(e.head)
        for arg in e.args:
            yield from symbols(arg)


def facts(*conditions):
    return lambda c: c in conditions


def simp(e, rules, known=None):
    return rewrite(NumberKind(e) if isinstance(e, int) else e, rules, known, normal)


def test_every_entry_is_a_named_rule():
    assert all(isinstance(r, Rule) and r.name for r in RULES)


def test_the_names_are_unique():
    names = [r.name for r in RULES]
    assert len(set(names)) == len(names)


def test_conditions_mention_only_pattern_variables():
    for r in RULES:
        if r.condition is not None:
            assert set(symbols(r.condition)) <= set(r.variables), r


@pytest.mark.parametrize("e, expected", [
    (E ** x, exp(x)),
    (exp(1), E),
    (exp(0), 1),
    (exp(x) * exp(y) * 2, 2 * exp(x + y)),
    (exp(x + I * pi), -exp(x)),
    (log(E) + log(1), 1),
    (1 ** x, 1),
])
def test_arithmetic_rewrites(e, expected):
    assert simp(e, arithmetic_rules.rules) == simp(expected, arithmetic_rules.rules)


def test_conditioned_arithmetic_rewrites():
    rules = arithmetic_rules.rules
    assert simp(0 ** x, rules) == 0 ** x
    assert simp(0 ** x, rules, known=facts(Gt(re(x), 0))) == NumberKind(0)
    assert simp(exp(2 * log(x)), rules) == exp(2 * log(x))
    assert simp(exp(2 * log(x)), rules, known=facts(Ne(x, 0))) == x ** 2
    assert simp(log(exp(x)), rules) == log(exp(x))
    assert simp(log(exp(x)), rules, known=facts(Eq(re(x), x))) == x
    known = facts(Gt(x, 0), Eq(re(y), y))
    assert simp(log(x ** y), rules, known=known) == simp(y * log(x), rules)


@pytest.mark.parametrize("e, expected", [
    (sin(x) ** 2 + cos(x) ** 2 + y, 1 + y),
    (3 * sin(x) ** 2 + 3 * cos(x) ** 2, 3),
    (1 - cos(x) ** 2, sin(x) ** 2),
    (2 * sin(x) / cos(x), 2 * tan(x)),
    (sin(pi / 6) + cos(pi / 3), 1),
    (tan(pi / 4), 1),
    (re(x + pi) + re(I), pi + re(x)),
    (Derivative(sin)(x), cos(x)),
])
def test_elementary_rewrites(e, expected):
    rules = arithmetic_rules.rules + elementary_rules.rules
    assert simp(e, rules) == simp(expected, rules)


def test_signs_and_shifts_by_a_known_coefficient():
    rules = arithmetic_rules.rules + elementary_rules.rules
    known = facts(Lt(-1, 0), Lt(-2, 0))
    assert simp(sin(-x), rules, known=known) == -sin(x)
    assert simp(cos(-2 * x), rules, known=known) == cos(2 * x)
    assert simp(tan(-x), rules, known=known) == -tan(x)


def test_shift_by_half_pi():
    rules = arithmetic_rules.rules + elementary_rules.rules
    half = Pow(2, -1)
    known = facts(Ge(Mul(half), half))
    assert simp(cos(x + pi / 2), rules, known=known) == -sin(x)


@pytest.mark.parametrize("e, expected", [
    (And(p, Or(q, true), Not(Not(p))), p),
    (Or(p, Not(p), q), true),
    (And(q, p, Not(p)), false),
    (Not(And(p, q)), Or(Not(p), Not(q))),
    (Or(q, And(q, p)), q),
    (Not(Lt(x, y)), Ge(x, y)),
    (Not(Eq(x, y)), Ne(x, y)),
    (Eq(x + 1, x + 1), true),
    (Ne(x, x), false),
])
def test_logic_rewrites(e, expected):
    assert rewrite(e, logic_rules.rules) == expected


def test_reflexive_order_needs_a_real_argument():
    assert rewrite(Lt(x, x), logic_rules.rules) == Lt(x, x)
    assert rewrite(Lt(x, x), logic_rules.rules, known=facts(Eq(re(x), x))) == false


@pytest.mark.parametrize("e, expected", [
    (sin(pi), 0),
    (cos(pi), -1),
    (sin(pi / 2), 1),
    (cos(pi / 2), 0),
    (sin(7 * pi / 6), -Pow(2, -1)),
    (cos(4 * pi / 3), -Pow(2, -1)),
    (sin(x + 2 * pi), sin(x)),
    (sin(x + pi), -sin(x)),
    (cos(x + pi / 2), -sin(x)),
    (sin(x - pi / 3), -cos(x + pi / 6)),
    (tan(x + pi), tan(x)),
    (exp(I * pi), -1),
    (exp(2 * I * pi), 1),
    (exp(I * pi / 2), I),
    (exp(7 * I * pi / 3), exp(I * pi / 3)),
])
def test_values_and_shifts_through_simplify(e, expected):
    assert simplify(e) == simplify(NumberKind(expected) if isinstance(expected, int) else expected)


def test_complex_powers_and_logarithms_through_simplify():
    assert simplify(I ** I) == simplify(exp(-pi / 2))
    assert simplify(Pow(5, 6 + 7 * I)) == simplify(exp((6 + 7 * I) * log(NumberKind(5))))
    assert simplify(log(NumberKind(-2))) == simplify(log(NumberKind(2)) + I * pi)
    assert simplify(log(-x), [Gt(x, 0)]) == simplify(log(x) + I * pi)
    assert simplify((x * y) ** z, [Gt(x, 0)]) == simplify(x ** z * y ** z)
    assert simplify(x ** z, [Gt(x, 0)]) == x ** z

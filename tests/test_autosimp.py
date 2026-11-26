from collections import Counter

import nary as nr
import pytest
from nary import E, Add, Eq, Ge, Gt, I, Le, Lt, Mul, Ne, Pow, cos, exp, log, pi, re, sin, tan
from nary.autosimp import RULES, autosimp, node
from nary.functions import is_lambda
from nary.lean import to_lean_rule
from nary.logic import And, Not, Or, false, true
from numeric import counterexamples
from sympy_bridge import agrees, classify, random_expressions, subterms

a, b, c, p, x, y = (nr.NumberKind(n) for n in "abcpxy")
H = Pow(2, -1)
RANDOM = random_expressions(500, seed=1)


def q(n, d):
    return Mul(n, Pow(d, -1))


def real(v):
    return Eq(re(v), v)


@pytest.mark.parametrize("r", [r for group in RULES.values() for r in group], ids=lambda r: r.name)
def test_rule_is_sound_and_stated_in_lean(r):
    assert not counterexamples(r.pattern, r.replacement, [] if r.condition is None else [r.condition])
    assert to_lean_rule(r).startswith(f"abbrev {r.name} : Prop")


def test_idempotent_and_every_node_is_a_fixpoint():
    for e in RANDOM:
        s = autosimp(e)
        assert autosimp(s) == s
        nodes = [t for t in subterms(s) if t.head is not None and not is_lambda(t)]
        assert all(node(t.head, list(t.args)) == t for t in nodes)


def test_sound_on_random_expressions():
    assert [e for e in RANDOM if counterexamples(e, autosimp(e))] == []


def test_agreement_with_sympy_on_random_expressions():
    assert Counter(classify(e)[0] for e in RANDOM) == {
        "same": 435, "same once assumed": 15, "different": 28, "not yet": 22,
    }


GATED = [
    (x / x, [Ne(x, 0)], Pow(x, 0)),
    (x ** 0, [Ne(x, 0)], Pow(x, 0)),
    (x ** 2 / x, [Ne(x, 0)], Mul(Pow(x, -1), Pow(x, 2))),
    (Pow(Pow(x, -1), -1), [Ne(x, 0)], Pow(Pow(x, -1), -1)),
    (Pow(Pow(x, -1), -1) * x ** -1, [Ne(x, 0)], Pow(x, 0)),
    (Pow(x, y) * Pow(x, -y), [Ne(x, 0)], Mul(Pow(x, y), Pow(x, Mul(-1, y)))),
    (0 * log(x), [Ne(x, 0)], Mul(0, log(x))),
    (log(x) - log(x), [Ne(x, 0)], Mul(0, log(x))),
    (Mul(0, tan(x)), [Ne(cos(x), 0)], Mul(0, tan(x))),
    (Eq(log(x), log(x)), [Ne(x, 0)], Eq(log(x), log(x))),
    (exp(log(x)), [Ne(x, 0)], exp(log(x))),
    (exp(2 * log(x)), [Ne(x, 0)], exp(Mul(2, log(x)))),
    (log(exp(x)), [real(x)], log(exp(x))),
    (re(x), [real(x)], re(x)),
    (Pow(0, x), [Gt(x, 0)], Pow(0, x)),
    (Pow(Pow(x, 2), H), [Gt(x, 0)], Pow(Pow(x, 2), H)),
    (Lt(x, x + 1), [real(x)], Lt(x, Add(1, x))),
    (Lt(y, 0), [Lt(y, 0)], Lt(y, 0)),
    (Ge(y, 0), [Lt(y, 0)], Ge(y, 0)),
    (Le(y, 0), [Le(y, 0)], Le(y, 0)),
    (log(exp(y)), [Lt(y, 0)], log(exp(y))),
    (And(Lt(x, y), Ge(x, y)), [real(x), real(y)], And(Ge(x, y), Lt(x, y))),
    (Or(Lt(x, y), Ge(x, y)), [real(x), real(y)], Or(Ge(x, y), Lt(x, y))),
]


@pytest.mark.parametrize("e, known, without", GATED, ids=repr)
def test_gated_step_matches_sympy_when_assumed_and_waits_otherwise(e, known, without):
    assert agrees(e, known)
    assert not counterexamples(e, autosimp(e, known), known)
    assert autosimp(e) == without


SIBLINGS = [
    Add(Mul(0, cos(x) ** -2), cos(x) ** -4), Mul(cos(x) ** -4, Pow(cos(x) ** -1, -3)),
    Add(tan(x), Mul(0, cos(x) ** -1)), Add(Mul(0, log(x)), x ** -1),
]


@pytest.mark.parametrize("e", SIBLINGS, ids=repr)
def test_step_allowed_where_a_sibling_has_a_value(e):
    s = autosimp(e)
    assert agrees(e) and autosimp(s) == s and not counterexamples(e, s)


FROM_SYMPY_TESTS = [
    ("test_power", "same", [
        Pow(Pow(5, -1), Pow(2, -1)), Mul(2, Pow(Pow(5, -1), Pow(2, -1))),
        Pow(Pow(5, -1), Mul(3, Pow(2, -1))), Mul(2, Pow(Pow(5, -1), Mul(3, Pow(2, -1)))),
        Pow(Pow(5, -1), Mul(17, Pow(3, -1))), Mul(2, Pow(Pow(5, -1), Mul(17, Pow(3, -1)))),
        Pow(Add(1835878332164045600327283789016195386006135170226228373525065, Pow(7, -1)), Pow(3, -1)),
        Pow(Pow(x, Pow(3, -1)), 2), Pow(25, Pow(3, -1)),
        (Pow(Pow(a, 3), Mul(2, Pow(5, -1))), [Gt(a, 0)]),
        (Pow(Pow(a, 2), b), [Gt(a, 0), Eq(re(b), b)]),
        Mul(-1, Mul(-1, Pow(Add(Pow(5, Pow(2, -1)), Mul(-1, 1)), Pow(2, -1)))), Pow(123, 789),
        Pow(1, I), Pow(-2, -5), Pow(0, Mul(2, x)), Pow(0, Mul(Mul(2, x), y)),
        Pow(Mul(Mul(-1, Pow(3, Pow(2, -1))), Add(1, Mul(2, I))), Pow(2, -1)),
        (Pow(Pow(p, 2), Pow(3, -1)), [Gt(p, 0)]), Pow(Add(3, Mul(4, I)), Pow(2, -1)),
        Pow(Add(3, Mul(-1, Mul(4, I))), Pow(2, -1)), Pow(Add(-3, Mul(-1, Mul(4, I))), Pow(2, -1)),
        Pow(Add(-3, Mul(4, I)), Pow(2, -1)), Pow(Add(32, Mul(24, I)), Pow(2, -1)),
        Pow(Add(32, Mul(-1, Mul(24, I))), Pow(2, -1)),
        Pow(Add(-32, Mul(-1, Mul(24, I))), Pow(2, -1)), Pow(Add(-32, Mul(24, I)), Pow(2, -1)),
        Pow(Mul(Add(3, Mul(4, I)), Pow(4, -1)), Pow(2, -1)),
        Pow(Mul(Add(8, Mul(15, I)), Pow(8, -1)), Pow(2, -1)),
        Pow(Mul(Add(3, Mul(-1, Mul(4, I))), Pow(25, -1)), Pow(2, -1)),
        Pow(Mul(Add(3, Mul(-1, Mul(4, I))), Pow(26, -1)), Pow(2, -1)),
        Pow(Mul(2, Pow(Add(3, Mul(4, I)), -1)), Pow(2, -1)),
        Pow(Mul(1, Pow(Add(3, Mul(I, 4)), -1)), Pow(2, -1)),
        Pow(Pow(Add(3, Mul(4, I)), Pow(2, -1)), 3), Pow(Add(3, Mul(4, I)), Mul(3, Pow(2, -1))),
        Pow(Add(6, Mul(8, I)), Mul(3, Pow(2, -1))), Pow(Mul(2, I), Pow(2, -1)),
        Pow(Mul(2, I), Mul(3, Pow(2, -1))), Pow(Mul(Mul(-9, Pow(2, -1)), I), Mul(3, Pow(2, -1))),
        Pow(Mul(2, Pow(3, -1)), Mul(3, Pow(2, -1))), Pow(Pow(6, -1), Mul(9, Pow(4, -1))),
        Pow(Mul(3, Pow(7, -1)), Mul(7, Pow(3, -1))), Pow(2, 3),
        Pow(Pow(I, Pow(2, -1)), Mul(9, Pow(2, -1))),
    ]),
    ("test_power", "same once assumed", [
        Mul(1, Pow(Pow(x, y), -1)),
    ]),
    ("test_power", "different", [
        Pow(Pow(Add(1, I), Mul(Mul(12, I), Mul(pi, Pow(log(Pow(2, Pow(2, -1))), -1)))), Pow(3, -1)),
    ]),
    ("test_power", "not yet", [
        Pow(Pow(33, Mul(Mul(I, 9), Pow(10, -1))), Pow(2, -1)), Pow(exp(Mul(3, I)), Pow(2, -1)),
        Pow(exp(Mul(5, I)), Pow(2, -1)), Pow(Mul(1, Pow(Add(1, I), -1)), Pow(2, -1)),
        Pow(Mul(1, Pow(Add(1, Mul(-1, Pow(2, Pow(2, -1)))), -1)), Pow(2, -1)),
        Pow(Mul(1, Pow(Add(1, Mul(-1, Pow(2, Pow(2, -1)))), -1)), Mul(-1, Pow(2, -1))),
        (Pow(Pow(Add(p, I), Mul(4, Pow(3, -1))), Pow(2, -1)), [Gt(p, 0)]),
        Pow(Pow(Add(1, Mul(I, Pow(5, -1))), 5), Pow(2, -1)),
        Pow(Pow(Add(1, Mul(I, Pow(5, -1))), 6), Pow(2, -1)),
        Pow(Mul(Add(3, Mul(4, I)), Pow(Add(3, Mul(-1, Mul(4, I))), -1)), Pow(2, -1)),
        Pow(Mul(-2, Pow(Add(3, Mul(4, I)), -1)), Pow(2, -1)),
        Pow(Mul(1, Pow(Add(3, Mul(-1, I)), -1)), Pow(2, -1)),
        Pow(Mul(1, Pow(tan(Add(1, I)), -1)), Pow(2, -1)),
    ]),
    ("test_trigonometric", "same", [
        sin(0), sin(pi), sin(-pi), sin(2*pi), sin(-2*pi), sin(-3*10**73*pi), sin(7*10**103*pi),
        sin(pi/2), sin(-pi/2), sin(q(5,2)*pi), sin(q(7,2)*pi), sin(pi/3), sin(q(-2,3)*pi),
        sin(pi/4), sin(-pi/4), sin(q(17,4)*pi), sin(q(-3,4)*pi), sin(pi/6), sin(-pi/6),
        sin(q(7,6)*pi), sin(q(-5,6)*pi), sin(q(1,5)*pi), sin(q(2,5)*pi), sin(q(3,5)*pi),
        sin(q(4,5)*pi), sin(q(6,5)*pi), sin(q(8,5)*pi), sin(q(-1273,5)*pi), sin(pi/8), sin(pi/10),
        sin(pi/12), sin(q(5,12)*pi), sin(q(-7,12)*pi), sin(q(-11,12)*pi), sin(q(104,105)*pi),
        sin(q(106,105)*pi), sin(q(-104,105)*pi), sin(q(-106,105)*pi), sin(-x), cos(-x), tan(-x),
        sin(x + pi), sin(x + 2*pi), sin(x + 3*pi), sin(x + 4*pi), sin(x - 5*pi), cos(x + pi),
        cos(x + 2*pi), cos(x + 3*pi), cos(x + 4*pi), cos(x - 5*pi), tan(x + pi), tan(x - 3*pi),
    ]),
    ("test_trigonometric", "not yet", [
        sin(pi*I), sin(-pi*I), sin(-2*I), sin(x*I),
    ]),
    ("test_exponential", "same", [
        exp(0), exp(1), exp(pi*I/2), exp(pi*I), exp(pi*I*q(3,2)), exp(2*pi*I), exp(x*log(x)),
        exp(I*pi*q(9,4)), exp(I*pi*q(46,18)), exp(I*pi*q(25,7)), exp(I*pi*q(-19,3)),
        exp(I*pi*q(37,8)) - exp(I*pi*q(-11,8)),
        exp(I*pi*q(-5,3)) / exp(I*pi*q(11,5)) * exp(I*pi*q(148,15)), exp(2 - I*pi*q(17,5)),
        exp(log(3) + I*pi*q(29,9)), log(exp(x)), exp(x + y), log(1), log(-1), log(E), log(-17),
        log(I), log(-I), log(17*I), exp(-log(3))**(-1), log(H), log(6), log(18), log(Pow(-12, H)),
    ]),
    ("test_exponential", "same once assumed", [
        exp(log(x)), exp(2*log(x)), exp(pi*log(x)), exp(17*log(x) + E*log(y)),
        exp(4*log(x)*log(y) + 3*log(x)),
    ]),
    ("test_exponential", "not yet", [
        log(-1 + I*Pow(3, H)), log(5 + 5*I), log(H - I*Pow(3, H)/2),
    ]),
    ("test_boolalg/relational", "same", [
        And(), And(true), And(false), And(true, true), And(true, false), And(false, false),
        And(true, true, true), And(And(Eq(a, 0), Eq(b, 0)), And(Ne(a, 0), Eq(c, 0))), Or(),
        Or(true), Or(false), Or(true, true), Or(true, false), Or(false, false),
        Or(true, false, false), Not(true), Not(false), Eq(x, x), Eq(y, x + x**2), Lt(y, x + x**2),
    ]),
    ("test_boolalg/relational", "not yet", [
        And(Gt(x, y), Lt(y, x), Ge(x, y), Le(y, x)), Or(Gt(x, y), Lt(y, x), Ge(x, y), Le(y, x)),
    ]),
]


@pytest.mark.parametrize(
    "source, category, case",
    [(source, category, case) for source, category, cases in FROM_SYMPY_TESTS for case in cases],
    ids=lambda v: v if isinstance(v, str) else repr(v)[:60],
)
def test_case_from_sympy_tests(source, category, case):
    e, given = case if isinstance(case, tuple) else (case, [])
    assert classify(e, given)[0] == category
    assert not counterexamples(e, autosimp(e, given), given)


@pytest.mark.parametrize("e", [Pow(3 + I, -1), Pow(-8 * I, H), Pow(2 * I, -H)], ids=repr)
def test_sympy_result_that_sympy_changes_when_evaluated_again(e):
    assert classify(e) == ("different", "SymPy changes its own result")


def test_refusal_and_lambda():
    with pytest.raises(TypeError, match="expects an expression"):
        autosimp(3)
    body = nr.Lambda(x, sin(-x))
    assert autosimp(body) == nr.Lambda(x, Mul(-1, sin(x)))

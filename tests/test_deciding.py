import random
from fractions import Fraction

import pytest
from nary import Add, E, Eq, Ge, Gt, I, Le, Lt, Mul, Ne, NumberKind, Pow, cos, exp, log, pi, re, sin, tan
from nary.arithmetic_rules import rules
from nary.deciding import Facts
from nary.logic import Or
from nary.rewriting import rewrite

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")


def real(e):
    return Eq(re(e), e)


def test_an_order_needs_both_sides_real_before_the_solver_is_asked():
    complex_x = Facts([Ne(x, 0)])
    assert not complex_x(Gt(x, 0))
    assert not complex_x(Ge(x * x, 0))
    assert not Facts()(Gt(I, 0))
    assert not Facts()(Le(I, 0))
    assert not Facts([Ne(I * x, 0)])(Gt(I * x, 0))


def test_an_order_fact_makes_its_sides_real():
    assert Facts([Gt(x, 1)])(Gt(x, 0))
    assert Facts([Gt(x, 1)])(real(x))
    assert Facts([Le(x * y, 2)])(real(x * y))
    assert not Facts([Le(x * y, 2)])(real(x))
    assert Facts([Ge(x, 0)])(Ge(x * x, 0))


def test_nonzero_of_a_term_not_known_to_be_real_by_the_solver():
    known = Facts([Ne(x, 0)])
    assert known(Ne(2 * x, 0))
    assert known(Ne(-x / 3, 0))
    assert not Facts([Ne(x, 0), Ne(y, 0)])(Ne(x - y, 0))
    assert not Facts([Ne(x, 0)])(Ne(x + 1, 0))
    assert Facts([Eq(x, y + 1), Ne(y, 0)])(Ne(x - 1, 0))


def test_nonzero_of_a_term_not_known_to_be_real_by_implications():
    known = Facts([Ne(x, 0), Ne(y, 0)])
    assert known(Ne(x * y, 0))
    assert known(Ne(I * x, 0))
    assert known(Ne(x ** z, 0))
    assert Facts()(Ne(exp(x), 0))
    assert not Facts()(Ne(exp(log(x)), 0))
    assert not known(Gt(x * y, 0))


def test_chains_of_inequalities():
    assert Facts([Gt(x, y), Gt(y, 0)])(Gt(x, 0))
    assert Facts([Gt(x, y), Ge(y, z), Gt(z, 2)])(Ne(x, 1))
    assert not Facts([Gt(x, y), Gt(z, 0)])(Gt(x, 0))


def test_implications_and_the_solver_interlock():
    known = Facts([Gt(x, 0), Gt(y, 0), Gt(z, 1)])
    assert known(Gt(x * y + z, 1))
    assert known(Gt(x * y * z, 0))
    assert known(Gt(Mul(x, y, z), 0))
    assert known(Gt(Mul(x, y, z, x) + exp(x), 0))
    assert known(Ne(Mul(x, z, y), 0))
    assert not known(Gt(x * y + z, 2))
    assert Facts([real(x)])(Gt(sin(x) + 2, 0))
    assert not Facts([real(x)])(Gt(sin(x) + 1, 0))
    assert Facts([Gt(x, 0), Lt(x, 3)])(Gt(sin(x), 0))
    assert not Facts([Gt(x, 0), Lt(x, 4)])(Gt(sin(x), 0))
    assert Facts([Gt(x, 1)])(Gt(log(x) + exp(x), 1))
    assert Facts([Gt(x, 0), Lt(x, 1)])(Lt(log(x), 0))


def test_constants():
    assert Facts()(Gt(pi, 3))
    assert Facts()(Gt(pi + E, 5))
    assert Facts()(Ne(I, 0))
    assert not Facts()(real(I))
    assert Facts()(Gt(exp(pi), 1))


def test_values_and_domains():
    known = Facts([Gt(x, 0)])
    assert known(Eq(log(x), log(x)))
    assert not Facts()(Eq(log(x), log(x)))
    assert not Facts()(Eq(Mul(0, log(x)), Mul(0, log(x))))
    assert not Facts()(Eq(Pow(0, 0), Pow(0, 0)))
    assert Facts()(Eq(Pow(2, -1), Pow(2, -1)))
    assert Facts()(Eq(tan(1), tan(1))) is False
    assert Facts([real(x), Gt(cos(x), 0)])(real(tan(x)))


def test_re_of_a_real_term():
    assert not Facts()(Gt(re(-1), 0))
    assert Facts()(Gt(re(2), 0))
    assert Facts([Gt(x, 0)])(Gt(re(x), 0))
    assert not Facts()(Gt(re(x), 0))


def test_equalities_and_disequalities_among_the_facts():
    assert Facts([Ge(x, 2), Le(x, 2)])(Eq(x, 2))
    assert Facts([Ge(x, 1), Ne(x, 1)])(Gt(x, 1))
    assert Facts([Ge(x, 1), Ne(1, x)])(Gt(2 * x, 2))
    assert not Facts([Ge(x, 1), Ne(x, 2)])(Gt(x, 1))
    assert Facts([Eq(x, 2)])(Gt(x, 1))


def test_and_or_in_a_condition():
    known = Facts([Gt(x, 0)])
    assert known(Or(Lt(x, 0), Ne(x, 0)))
    assert not known(Or(Lt(x, 0), Gt(y, 0)))


def test_as_the_known_of_rewrite():
    known = Facts([Gt(x, 0)])
    assert rewrite(x / x, rules, known=known) == NumberKind(1)
    assert rewrite(log(x) * 0, rules, known=known) == NumberKind(0)
    assert rewrite(x ** 0, rules, known=known) == NumberKind(1)
    assert rewrite(log(y) * 0, rules, known=known) == Mul(log(y), 0)
    assert rewrite(exp(log(x + 1)), rules, known=known) == x + 1


def test_answers_do_not_depend_on_the_order_of_questions():
    questions = [Gt(x * y + 1, 0), Ne(x * y, 0), Gt(x, 0), Gt(exp(x) - 1, 0), Ne(log(x + 1), 0)]
    facts = [Gt(x, 0), Gt(y, 0)]
    expected = [Facts(facts)(q) for q in questions]
    known = Facts(facts)
    assert [known(q) for q in reversed(questions)][::-1] == expected


z3 = pytest.importorskip("z3")

SYMBOLS = [NumberKind(f"s{i}") for i in range(4)]


def nary_rational(q):
    if q.denominator == 1:
        return NumberKind(q.numerator)
    return Mul(q.numerator, Pow(q.denominator, -1))


def random_form(rng, count):
    chosen = rng.sample(range(count), rng.randint(1, min(3, count)))
    coefficients = [(i, Fraction(rng.randint(-3, 3) or 1, rng.choice([1, 1, 2]))) for i in chosen]
    constant = Fraction(rng.randint(-4, 4))
    nary = Add(*(Mul(nary_rational(c), SYMBOLS[i]) for i, c in coefficients), nary_rational(constant))
    return nary, lambda xs: sum(c * xs[i] for i, c in coefficients) + constant


RELATIONS = [
    (Gt, lambda a: a > 0), (Ge, lambda a: a >= 0), (Lt, lambda a: a < 0),
    (Le, lambda a: a <= 0), (Eq, lambda a: a == 0), (Ne, lambda a: a != 0),
]


def random_relation(rng, count, relations):
    form, z3_form = random_form(rng, count)
    head, z3_relation = rng.choice(relations)
    return head(form, 0), lambda xs: z3_relation(z3_form(xs))


def z3_entails(facts, goal, xs):
    solver = z3.Solver()
    for fact in facts:
        solver.add(fact(xs))
    solver.add(z3.Not(goal(xs)))
    return solver.check() == z3.unsat


@pytest.mark.parametrize("seed", range(150))
def test_agrees_with_z3_on_real_linear_problems(seed):
    rng = random.Random(seed)
    count = rng.randint(1, 4)
    xs = [z3.Real(f"s{i}") for i in range(count)]
    pairs = [random_relation(rng, count, RELATIONS) for _ in range(rng.randint(0, 4))]
    facts = [real(s) for s in SYMBOLS[:count]] + [p[0] for p in pairs]
    known = Facts(facts)
    for _ in range(6):
        goal, z3_goal = random_relation(rng, count, RELATIONS)
        assert known(goal) == z3_entails([p[1] for p in pairs], z3_goal, xs), (facts, goal)


@pytest.mark.parametrize("seed", range(150))
def test_agrees_with_z3_over_complex_numbers_on_equalities_and_disequalities(seed):
    rng = random.Random(seed)
    count = rng.randint(1, 4)
    parts = [z3.Real(f"a{i}") for i in range(count)], [z3.Real(f"b{i}") for i in range(count)]
    pairs = []
    for _ in range(rng.randint(0, 5)):
        form, z3_form = random_form(rng, count)
        head = rng.choice([Eq, Ne])
        zero = z3.And(z3_form(parts[0]) == 0, z3_form(parts[1]) == z3_form([0] * count))
        pairs.append((head(form, 0), zero if head is Eq else z3.Not(zero)))
    known = Facts([p[0] for p in pairs[:-1]])
    solver = z3.Solver()
    solver.add(*(p[1] for p in pairs[:-1]))
    if pairs:
        goal, z3_goal = pairs[-1]
        assert known(goal) == (solver.check(z3.Not(z3_goal)) == z3.unsat), (pairs, goal)

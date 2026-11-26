import random

import pytest
from nary._core import Simplex

z3 = pytest.importorskip("z3")

RELATIONS = [">", ">=", "=", "<=", "<", "!="]


def random_constraint(rng, variables):
    chosen = rng.sample(range(variables), rng.randint(1, min(3, variables)))
    terms = [(v, rng.randint(-4, 4) or 1, rng.choice([1, 1, 2, 3])) for v in chosen]
    return terms, rng.choice(RELATIONS), (rng.randint(-6, 6), rng.choice([1, 1, 2]))


def z3_form(xs, terms, relation, constant):
    total = sum(z3.Q(n, d) * xs[v] for v, n, d in terms) + z3.Q(*constant)
    return {
        ">": total > 0, ">=": total >= 0, "=": total == 0, "<=": total <= 0, "<": total < 0,
        "!=": total != 0,
    }[relation]


@pytest.mark.parametrize("seed", range(300))
def test_agrees_with_z3_on_random_problems(seed):
    rng = random.Random(seed)
    variables = rng.randint(1, 5)
    simplex = Simplex()
    for _ in range(variables):
        simplex.variable()
    xs = [z3.Real(f"x{i}") for i in range(variables)]
    oracle = z3.Solver()
    for _ in range(rng.randint(0, 4)):
        constraint = random_constraint(rng, variables)
        simplex.assert_(*constraint)
        oracle.add(z3_form(xs, *constraint))
    for _ in range(8):
        query = [random_constraint(rng, variables) for _ in range(rng.randint(1, 3))]
        simplex.push()
        oracle.push()
        for constraint in query:
            simplex.assert_(*constraint)
            oracle.add(z3_form(xs, *constraint))
        assert simplex.check() == (oracle.check() == z3.sat), (seed, query)
        simplex.pop()
        oracle.pop()
    assert simplex.check() == (oracle.check() == z3.sat)


def test_a_bound_on_a_new_form_reuses_nothing_it_should_not():
    simplex = Simplex()
    x, y = simplex.variable(), simplex.variable()
    simplex.assert_([(x, 1, 1), (y, 1, 1)], ">", (0, 1))
    simplex.push()
    simplex.assert_([(x, 2, 1), (y, 2, 1)], "<", (0, 1))
    assert not simplex.check()
    simplex.pop()
    simplex.push()
    simplex.assert_([(x, -1, 1), (y, -1, 1)], "<", (0, 1))
    assert simplex.check()
    simplex.pop()


def test_overflow_makes_it_answer_satisfiable():
    simplex = Simplex()
    x = simplex.variable()
    simplex.assert_([(x, 1, 1)], ">", (2**80, 1))
    simplex.assert_([(x, 1, 1)], "<", (0, 1))
    assert simplex.check()

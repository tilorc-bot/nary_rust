import json
import random
import sys
from fractions import Fraction

import z3

RELATIONS = {
    "Gt": lambda a: a > 0, "Ge": lambda a: a >= 0, "Lt": lambda a: a < 0,
    "Le": lambda a: a <= 0, "Eq": lambda a: a == 0, "Ne": lambda a: a != 0,
}


def random_relation(rng, count, relations):
    coefficients = [Fraction(0)] * count
    for i in rng.sample(range(count), rng.randint(1, min(3, count))):
        coefficients[i] = Fraction(rng.randint(-3, 3) or 1, rng.choice([1, 1, 2]))
    return rng.choice(relations), coefficients, Fraction(rng.randint(-4, 4))


def value(coefficients, constant, xs):
    return sum(z3.Q(c.numerator, c.denominator) * x for c, x in zip(coefficients, xs)) + z3.Q(
        constant.numerator, constant.denominator
    )


def real_formula(relation, xs):
    head, coefficients, constant = relation
    return RELATIONS[head](value(coefficients, constant, xs))


def complex_formula(relation, parts):
    head, coefficients, constant = relation
    zero = z3.And(
        value(coefficients, constant, parts[0]) == 0, value(coefficients, Fraction(0), parts[1]) == 0
    )
    return zero if head == "Eq" else z3.Not(zero)


def record(rng, numbers, relations, formula, goals):
    count = rng.randint(1, 4)
    xs = [z3.Real(f"a{i}") for i in range(count)], [z3.Real(f"b{i}") for i in range(count)]
    xs = xs if numbers == "complex" else xs[0]
    facts = [random_relation(rng, count, relations) for _ in range(rng.randint(0, 4))]
    solver = z3.Solver()
    solver.add(*(formula(f, xs) for f in facts))
    case = {"symbols": count, "facts": facts, "proved": [], "not proved": []}
    for _ in range(goals):
        goal = random_relation(rng, count, relations)
        proved = solver.check(z3.Not(formula(goal, xs))) == z3.unsat
        case["proved" if proved else "not proved"].append(goal)
    return case


def main(path):
    rng = random.Random(0)
    cases = {
        "real": [record(rng, "real", list(RELATIONS), real_formula, 6) for _ in range(150)],
        "complex": [record(rng, "complex", ["Eq", "Ne"], complex_formula, 4) for _ in range(150)],
    }
    lines = [
        json.dumps([numbers, case], default=str) for numbers, group in cases.items() for case in group
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])

import json
from fractions import Fraction
from pathlib import Path

import pytest
from nary import Add, E, Eq, Ge, Gt, I, Le, Lt, Mul, Ne, NumberKind, Pow, cos, exp, log, pi, re, sin, tan
from nary.arithmetic_rules import rules
from nary.deciding import Facts
from nary.logic import Or
from nary.rewriting import rewrite

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")


def real(e):
    return Eq(re(e), e)


def has_value(e):
    return Eq(e, e)


MUST_PROVE = {
    "linear consequences": [
        ([Gt(x, 1)], Gt(x, 0)),
        ([Gt(x, y), Gt(y, 0)], Gt(x, 0)),
        ([Gt(x, y), Ge(y, z), Gt(z, 2)], Ne(x, 1)),
        ([Ge(x, 2), Le(x, 2)], Eq(x, 2)),
        ([Eq(x, 2)], Gt(x, 1)),
        ([Ge(x, 1), Ne(x, 1)], Gt(x, 1)),
        ([Ge(x, 1), Ne(1, x)], Gt(2 * x, 2)),
        ([real(x), real(y), Gt(x + y, 0)], Gt(2 * x + 2 * y, 0)),
    ],
    "an order fact makes its sides real": [
        ([Gt(x, 1)], real(x)),
        ([Le(x * y, 2)], real(x * y)),
        ([Ge(x, 0)], Ge(x * x, 0)),
    ],
    "nonzero of a term not known to be real, linearly": [
        ([Ne(x, 0)], Ne(2 * x, 0)),
        ([Ne(x, 0)], Ne(-x / 3, 0)),
        ([Eq(x, y + 1), Ne(y, 0)], Ne(x - 1, 0)),
    ],
    "nonzero of a term not known to be real, by implications": [
        ([Ne(x, 0), Ne(y, 0)], Ne(x * y, 0)),
        ([Ne(x, 0)], Ne(I * x, 0)),
        ([Ne(x, 0), Ne(y, 0)], Ne(x ** z, 0)),
        ([], Ne(exp(x), 0)),
    ],
    "implications and linear reasoning together": [
        ([Gt(x, 0), Gt(y, 0), Gt(z, 1)], Gt(x * y + z, 1)),
        ([Gt(x, 0), Gt(y, 0), Gt(z, 1)], Gt(x * y * z, 0)),
        ([Gt(x, 0), Gt(y, 0), Gt(z, 1)], Gt(Mul(x, y, z, x) + exp(x), 0)),
        ([Gt(x, 0), Gt(y, 0), Gt(z, 1)], Ne(Mul(x, z, y), 0)),
        ([real(x)], Gt(sin(x) + 2, 0)),
        ([Gt(x, 0), Lt(x, 3)], Gt(sin(x), 0)),
        ([Gt(x, 1)], Gt(log(x) + exp(x), 1)),
        ([Gt(x, 0), Lt(x, 1)], Lt(log(x), 0)),
        ([Gt(x, 0)], Ne(log(x + 1), 0)),
    ],
    "constants": [
        ([], Gt(pi, 3)),
        ([], Gt(pi + E, 5)),
        ([], Ne(I, 0)),
        ([], Gt(exp(pi), 1)),
    ],
    "having a value": [
        ([Gt(x, 0)], has_value(log(x))),
        ([], has_value(Pow(2, -1))),
        ([real(x), Gt(cos(x), 0)], real(tan(x))),
    ],
    "re": [
        ([], Gt(re(2), 0)),
        ([Gt(x, 0)], Gt(re(x), 0)),
    ],
    "and, or": [
        ([Gt(x, 0)], Or(Lt(x, 0), Ne(x, 0))),
    ],
}

MUST_NOT_PROVE = {
    "an order of a term not shown to be real": [
        ([Ne(x, 0)], Gt(x, 0)),
        ([Ne(x, 0)], Ge(x * x, 0)),
        ([Ne(x, 0), Ne(y, 0)], Gt(x * y, 0)),
        ([], Gt(I, 0)),
        ([], Le(I, 0)),
        ([Ne(I * x, 0)], Gt(I * x, 0)),
        ([], Gt(re(x), 0)),
    ],
    "realness not entailed": [
        ([Le(x * y, 2)], real(x)),
        ([], real(I)),
        ([Ne(x, 0)], real(x)),
    ],
    "a term that may have no value": [
        ([], has_value(log(x))),
        ([], has_value(Mul(0, log(x)))),
        ([], has_value(Pow(0, 0))),
        ([], has_value(tan(1))),
        ([], Ne(exp(log(x)), 0)),
        ([Ne(x, 0)], Ne(Pow(y, -1), 0)),
        ([], Eq(Mul(0, Pow(x, -1)), 0)),
        ([], Gt(log(x) - log(x) + 1, 0)),
        ([], Ne(Pow(x, -1) - Pow(x, -1) + 1, 0)),
    ],
    "not entailed": [
        ([Ne(x, 0), Ne(y, 0)], Ne(x - y, 0)),
        ([Ne(x, 0)], Ne(x + 1, 0)),
        ([Gt(x, y), Gt(z, 0)], Gt(x, 0)),
        ([Ge(x, 1), Ne(x, 2)], Gt(x, 1)),
        ([Gt(x, 0), Gt(y, 0), Gt(z, 1)], Gt(x * y + z, 2)),
        ([real(x)], Gt(sin(x) + 1, 0)),
        ([Gt(x, 0), Lt(x, 4)], Gt(sin(x), 0)),
        ([], Gt(re(-1), 0)),
        ([Gt(x, 0)], Or(Lt(x, 0), Gt(y, 0))),
        ([Gt(x, 2**80)], Lt(x, 0)),
    ],
}


def cases(groups):
    return [
        pytest.param(facts, condition, id=f"{name}: {condition}")
        for name, pairs in groups.items() for facts, condition in pairs
    ]


@pytest.mark.parametrize("facts, condition", cases(MUST_PROVE))
def test_must_prove(facts, condition):
    assert Facts(facts)(condition) is True


@pytest.mark.parametrize("facts, condition", cases(MUST_NOT_PROVE))
def test_must_not_prove(facts, condition):
    assert Facts(facts)(condition) is False


SYMBOLS = [NumberKind(f"s{i}") for i in range(4)]
HEADS = {"Gt": Gt, "Ge": Ge, "Lt": Lt, "Le": Le, "Eq": Eq, "Ne": Ne}


def rational(text):
    q = Fraction(text)
    return NumberKind(q.numerator) if q.denominator == 1 else Mul(q.numerator, Pow(q.denominator, -1))


def relation(head, coefficients, constant):
    terms = [Mul(rational(c), s) for c, s in zip(coefficients, SYMBOLS) if Fraction(c)]
    return HEADS[head](Add(*terms, rational(constant)), 0)


RECORDED = [json.loads(line) for line in (Path(__file__).parent / "deciding_cases.jsonl").open()]


@pytest.mark.parametrize("numbers, case", RECORDED)
def test_agrees_with_recorded_answers_of_an_oracle(numbers, case):
    reals = [real(s) for s in SYMBOLS[:case["symbols"]]] if numbers == "real" else []
    known = Facts(reals + [relation(*f) for f in case["facts"]])
    assert [known(relation(*g)) for g in case["proved"]] == [True] * len(case["proved"])
    assert [known(relation(*g)) for g in case["not proved"]] == [False] * len(case["not proved"])


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


def test_a_long_product_is_answered_without_an_error():
    xs = [NumberKind(f"x{i}") for i in range(200)]
    assert Facts([Gt(a, 0) for a in xs])(Gt(Mul(*xs) + exp(xs[0]), 0)) in (True, False)

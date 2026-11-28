import ast
import random
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from nary import (
    Add,
    BoolKind,
    E,
    Eq,
    Ge,
    Gt,
    I,
    Lambda,
    Le,
    Lt,
    Mul,
    Ne,
    NumberKind,
    Pow,
    declare_function,
    declare_kind,
    log,
    pi,
    re,
    sin,
)
from nary._numbers import MAX_POWER_BITS, evaluate, is_number
from nary.logic import false, true
from nary.normalising import normalise

N = NumberKind
x = N("x")
half, third = Pow(2, -1), Pow(3, -1)
PYTHON = Path(__file__).resolve().parent.parent / "python" / "nary"
COMPARISONS = {
    Eq: Fraction.__eq__, Ne: Fraction.__ne__, Lt: Fraction.__lt__,
    Gt: Fraction.__gt__, Le: Fraction.__le__, Ge: Fraction.__ge__,
}


def number(q):
    q = Fraction(q)
    if q.denominator == 1:
        return N(q.numerator)
    if q.numerator == 1:
        return Pow(q.denominator, -1)
    return Mul(q.numerator, Pow(q.denominator, -1))


def assert_settled(result):
    assert is_number(result)
    assert normalise(result) == result
    assert repr(normalise(result)) == repr(result)
    if not result.is_literal:
        assert evaluate(result.head, result.args) == result


def random_rational(rng):
    pick = rng.random()
    if pick < 0.2:
        return Fraction(rng.choice([0, 1, -1, 2, -2]))
    if pick < 0.5:
        return Fraction(rng.randint(-50, 50))
    if pick < 0.9:
        return Fraction(rng.randint(-50, 50), rng.randint(1, 30))
    return Fraction(rng.randint(-(10**30), 10**30), rng.randint(1, 10**30))


def random_tree(rng, depth):
    if depth == 0 or rng.random() < 0.3:
        q = random_rational(rng)
        return number(q), q
    head = rng.choice([Add, Mul, Pow])
    if head is Pow:
        base, value = random_tree(rng, depth - 1)
        k = rng.randint(-4, 4)
        args, expected = (base, N(k)), (None if value is None else _fraction_power(value, k))
    else:
        children = [random_tree(rng, depth - 1) for _ in range(rng.randint(0, 4))]
        args = tuple(arg for arg, _ in children)
        values = [value for _, value in children]
        if None in values:
            expected = None
        elif head is Add:
            expected = sum(values, Fraction(0))
        else:
            expected = Fraction(1)
            for value in values:
                expected *= value
    if expected is None:
        assert any(arg is None for arg in args) or evaluate(head, args) is None
        return None, None
    if any(arg is None for arg in args):
        return None, None
    result = evaluate(head, args)
    assert result == number(expected), (head, args)
    return result, expected


def _fraction_power(value, k):
    if value == 0 and k <= 0:
        return None
    return value**k


def test_nested_arithmetic_agrees_with_fraction():
    rng = random.Random(63)
    results = 0
    for _ in range(3000):
        result, _ = random_tree(rng, 3)
        if result is not None:
            assert_settled(result)
            results += 1
    assert results > 2000


def close_pairs(rng):
    for _ in range(300):
        a, b = random_rational(rng), random_rational(rng)
        yield a, b
        yield a, a
        m = rng.randint(10**20, 10**25)
        yield a, (a * m + rng.choice([-1, 1])) / m


@pytest.mark.parametrize("head", list(COMPARISONS))
def test_comparisons_agree_with_fraction(head):
    rng = random.Random(64)
    for a, b in close_pairs(rng):
        expected = true if COMPARISONS[head](a, b) else false
        assert evaluate(head, (number(a), number(b))) == expected, (a, b)


@pytest.mark.parametrize("head, args, expected", [
    (Eq, (evaluate(Add, (third, Pow(6, -1))), evaluate(Mul, (N(3), Pow(6, -1)))), true),
    (Eq, (evaluate(Add, (half, half)), N(1)), true),
    (Ne, (evaluate(Pow, (half, N(-2))), N(4)), false),
    (Le, (evaluate(Mul, (N(2), half)), N(1)), true),
    (Lt, (Mul(10**30, Pow(10**30 + 1, -1)), Mul(10**30 + 1, Pow(10**30 + 2, -1))), true),
    (Gt, (Mul(-1, Pow(10**30, -1)), N(0)), false),
])
def test_equal_values_reached_differently_and_close_values(head, args, expected):
    assert evaluate(head, args) == expected


@pytest.mark.parametrize("head, args", [
    (Pow, (N(0), N(0))),
    (Pow, (N(0), N(-1))),
    (Pow, (N(0), N(-(10**100)))),
    (Pow, (evaluate(Add, (half, Mul(-1, half))), N(-3))),
])
def test_no_value_stays_without_one(head, args):
    assert evaluate(head, args) is None


@pytest.mark.parametrize("head, args, expected", [
    (Add, (), N(0)),
    (Mul, (), N(1)),
    (Add, (N(5),), N(5)),
    (Mul, (half,), half),
    (Add, (half, Mul(-1, half)), N(0)),
    (Mul, (N(0), half), N(0)),
    (Mul, (N(2), half), N(1)),
    (Mul, (N(-4), half), N(-2)),
    (Mul, (N(-1), half), Mul(-1, half)),
    (Mul, (N(6), Pow(4, -1)), Mul(3, half)),
    (Mul, (N(-6), Pow(4, -1)), Mul(-3, half)),
    (Mul, (N(2), Pow(6, -1)), third),
    (Mul, (N(-2), Pow(6, -1)), Mul(-1, third)),
    (Add, (third, third, third), N(1)),
    (Pow, (N(2), N(-1)), half),
    (Pow, (N(-2), N(-1)), Mul(-1, half)),
    (Pow, (Mul(-1, half), N(-1)), N(-2)),
    (Pow, (Mul(2, third), N(-2)), Mul(9, Pow(4, -1))),
    (Pow, (N(7), N(0)), N(1)),
    (Pow, (N(0), N(3)), N(0)),
    (re, (Mul(-3, half),), Mul(-3, half)),
])
def test_written_form(head, args, expected):
    result = evaluate(head, args)
    assert result == expected and repr(result) == repr(expected)
    assert_settled(result)


def deep(n, head):
    e = x
    for _ in range(n):
        e = head(e, x)
    return e


def frames():
    depth, frame = 0, sys._getframe()
    while frame is not None:
        depth, frame = depth + 1, frame.f_back
    return depth


@pytest.mark.parametrize("e", [
    x, BoolKind("p"), true, pi, E, I, Add(1, 2), sin(1), log(2),
    Pow(2, 2), Pow(2, -2), Pow(1, -1), Pow(0, -1), Pow(-2, -1), Pow(x, -1), Pow(2, N(-1) * 1),
    Mul(0, half), Mul(1, half), Mul(2, Pow(4, -1)), Mul(half, 3), Mul(3, half, 1),
    Mul(3, Pow(x, -1)),
    Mul(3), Mul(), Add(), Pow(2, half), Mul(3, Pow(2, half)), Lambda(x, x),
    deep(100_000, Mul), deep(100_000, Pow), deep(100_000, Add),
    Mul(*[x] * 100_000), Mul(3, Pow(2, -1), *[x] * 100_000), Add(*[half] * 100_000),
    3, Fraction(1, 2), 1.5, None, "x",
])
def test_is_number_refuses_without_recursing(e):
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(frames() + 20)
    try:
        assert is_number(e) is False
    finally:
        sys.setrecursionlimit(limit)


@pytest.mark.parametrize("literals, value", [
    (float, 0.5), (Fraction, Fraction(1, 2)), (complex, 1j),
])
def test_literals_of_other_kinds_are_refused(literals, value):
    kind = declare_kind(f"Number{literals.__name__.title()}Kind", literals=literals)
    assert not is_number(kind(value))
    assert evaluate(Add, (kind(value), N(1))) is None


Twice = declare_function("Twice", NumberKind, returns=NumberKind, domain=true)


@pytest.mark.parametrize("head, args", [
    (Pow, (N(2), half)),
    (Pow, (N(4), half)),
    (Pow, (N(-1), half)),
    (Mul, (Pow(2, half), Pow(2, half))),
    (Add, (N(1), I)),
    (Mul, (I, I)),
    (re, (I,)),
    (Eq, (I, I)),
    (Gt, (I, N(0))),
    (Mul, (N(2), x)),
    (Pow, (N(2), x)),
    (Add, (N(1), 2)),
    (sin, (N(0),)),
    (Twice, (N(1),)),
    (Lambda(x, x), (N(1),)),
    (x, (N(1),)),
    (I, ()),
    ("Add", (N(1),)),
    (None, ()),
    ([Add], ()),
    (Pow, (N(2),)),
    (Pow, (N(2), N(3), N(4))),
    (re, ()),
    (re, (N(1), N(2))),
    (Eq, (N(1),)),
    (Eq, (N(1), N(1), N(2))),
    (Lt, ()),
    (Ge, (N(1), N(2), N(3))),
])
def test_what_is_refused(head, args):
    assert evaluate(head, args) is None


@pytest.mark.parametrize("base, k", [
    (Fraction(2), MAX_POWER_BITS // 2),
    (Fraction(1, 2), -(MAX_POWER_BITS // 2)),
    (Fraction(-3, 2), MAX_POWER_BITS // 2),
    (Fraction(2**64 - 1, 2), MAX_POWER_BITS // 64),
])
def test_largest_power_that_is_computed(base, k):
    result = evaluate(Pow, (number(base), N(k)))
    assert result == number(base**k)
    assert_settled(result)
    assert evaluate(Pow, (number(base), N(k + (1 if k > 0 else -1)))) is None


@pytest.mark.parametrize("base, expected", [(N(1), N(1)), (N(-1), N(-1)), (N(0), N(0))])
def test_a_power_of_zero_or_one_is_not_limited(base, expected):
    assert evaluate(Pow, (base, N(10**100 + 1))) == expected
    assert evaluate(Pow, (base, N(-(10**100) - 1))) == (None if base == N(0) else expected)


def imported_modules(path):
    tree = ast.parse(path.read_text())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
            if node.level and node.module is None:
                found.update("." + alias.name for alias in node.names)
    return found


def test_nothing_imports_numbers_yet():
    for path in PYTHON.glob("*.py"):
        if path.name != "_numbers.py":
            assert not any("_numbers" in name for name in imported_modules(path)), path.name
    assert imported_modules(PYTHON / "_numbers.py") == {
        "fractions", "math", "._core", ".arithmetic", ".kinds", ".logic", ".relational",
    }


def test_combining_the_numbers_of_a_sum():
    args = Add(x, half, N(3), Mul(-1, third)).args
    numbers = [a for a in args if is_number(a)]
    assert evaluate(Add, numbers) == Mul(19, Pow(6, -1))

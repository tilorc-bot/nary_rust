import pytest

from nary import Add, BoolKind, Eq, Ge, Gt, I, Le, Lt, Mul, Ne, NumberKind, Pow, re, sin
from nary._numbers import evaluate, is_number
from nary.logic import false, true

x = NumberKind("x")
half, third = Pow(2, -1), Pow(3, -1)
N = NumberKind


@pytest.mark.parametrize("head, args, expected", [
    (Add, (half, half), N(1)),
    (Add, (N(1), Mul(-1, half)), half),
    (Mul, (N(3), half), Mul(3, half)),
    (Mul, (N(6), Pow(4, -1)), Mul(3, half)),
    (Pow, (N(2), N(10)), N(1024)),
    (Pow, (Mul(2, Pow(3, -1)), N(-2)), Mul(9, Pow(4, -1))),
    (Pow, (N(12), half), Mul(2, Pow(3, half))),
    (Pow, (N(8), third), N(2)),
    (Mul, (Pow(2, half), Pow(3, half)), Pow(6, half)),
    (Mul, (Pow(2, half), Pow(2, half)), N(2)),
    (Add, (Pow(2, half), Pow(2, half)), Mul(2, Pow(2, half))),
    (Mul, (I, I), N(-1)),
    (Pow, (I, N(4)), N(1)),
    (Pow, (N(-1), half), I),
    (Pow, (N(-4), half), Mul(2, I)),
    (Pow, (N(-8), Mul(2, third)), Mul(4, Pow(-1, Mul(2, third)))),
    (Pow, (N(0), half), N(0)),
    (re, (Mul(2, I),), N(0)),
    (re, (half,), half),
])
def test_arithmetic(head, args, expected):
    assert evaluate(head, args) == expected


@pytest.mark.parametrize("head, args, expected", [
    (Lt, (half, Pow(2, half)), true),
    (Gt, (Pow(3, half), Pow(2, half)), true),
    (Le, (N(-2), Pow(2, half)), true),
    (Ge, (Mul(-1, Pow(2, half)), N(-1)), false),
    (Eq, (Pow(4, half), N(2)), true),
    (Ne, (Pow(4, half), N(2)), false),
    (Eq, (I, N(1)), false),
])
def test_comparisons(head, args, expected):
    assert evaluate(head, args) == expected


@pytest.mark.parametrize("head, args", [
    (Pow, (N(0), N(-1))),
    (Pow, (N(0), N(0))),
    (Pow, (N(2), Pow(10, 6))),
    (Add, (N(1), I)),
    (Add, (Pow(2, half), N(1))),
    (Gt, (I, N(0))),
    (Mul, (N(2), x)),
    (Pow, (N(2), x)),
    (sin, (N(0),)),
])
def test_what_is_left_alone(head, args):
    assert evaluate(head, args) is None


@pytest.mark.parametrize("e, expected", [
    (N(3), True),
    (Mul(3, half), True),
    (Pow(2, half), True),
    (Mul(2, I), True),
    (Pow(-1, third), True),
    (Add(1, I), False),
    (Pow(x, 2), False),
    (x, False),
    (BoolKind("p"), False),
    (3, False),
])
def test_is_number(e, expected):
    assert is_number(e) is expected


@pytest.mark.parametrize("head, args", [
    (Add, (half, third)),
    (Pow, (N(72), Mul(2, Pow(3, -1)))),
    (Mul, (Pow(-1, third), Pow(-1, half))),
    (Pow, (Mul(-3, I), Mul(-1, half))),
])
def test_what_is_written_reads_back_as_itself(head, args):
    value = evaluate(head, args)
    assert is_number(value)
    assert evaluate(Mul, (value,)) == value
    assert evaluate(Add, (value, N(0))) == value

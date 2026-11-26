import cmath
import math
from fractions import Fraction as F

import pytest
from nary import Add, Eq, Ge, Gt, I, Le, Lt, Mul, Ne, NumberKind, Pow
from nary.logic import false, true
from nary.numbers import Number, compare, is_canonical_number, power, real_part, to_expr, value

x = NumberKind("x")
rationals = [F(n, d) for n in range(-12, 13) for d in (1, 2, 3, 4, 6, 9)]
exponents = sorted({F(n, d) for n in range(-9, 10) for d in (1, 2, 3, 4, 6)})


def _number(v):
    return v if isinstance(v, Number) else Number(v)


def number(e):
    if e.is_literal:
        return complex(e.value)
    if e == I:
        return 1j
    args = [number(a) for a in e.args]
    if e.head == Add:
        return sum(args)
    if e.head == Mul:
        return math.prod(args)
    return args[0] ** args[1]


def pows(e):
    if e.head == Pow:
        yield e
    for a in e.args:
        yield from pows(a)


def test_value_of_literal_arithmetic():
    assert value(Add(1, Mul(2, I), Pow(I, 2))) == Number(0, 2)
    assert value(Pow(Add(1, I), -2)) == Number(0, F(-1, 2))
    assert value(Pow(I, 7)) == Number(0, -1) and value(Pow(I, -1)) == Number(0, -1)
    assert value(Mul()) == 1 and value(Add()) == 0
    assert value(Pow(Mul(2, Pow(3, -1)), -3)) == F(27, 8)
    for e in (Pow(0, -1), Pow(0, 0), Pow(2, Pow(2, -1)), Add(x, 1), Pow(Add(1, Mul(-1, 1)), -1)):
        assert value(e) is None


def test_number_arithmetic():
    a, b = Number(1, 2), Number(F(1, 3), -1)
    assert a + b == Number(F(4, 3), 1) and a - b == Number(F(2, 3), 3) and a * b == Number(F(7, 3), F(-1, 3))
    assert a ** -1 == Number(F(1, 5), F(-2, 5)) and a**0 == 1 and 2 - a == Number(1, -2)
    assert len({Number(2), Number(F(4, 2)), Number(2, 1)}) == 2 and Number(2) == 2
    assert real_part(b) == F(1, 3)


def test_to_expr_shapes_and_round_trip():
    assert to_expr(Number(5)) == NumberKind(5)
    assert to_expr(Number(F(1, 3))) == Pow(3, -1)
    assert to_expr(Number(F(-2, 3))) == Mul(-2, Pow(3, -1))
    assert to_expr(Number(0, 1)) == I and to_expr(Number(0, -1)) == Mul(-1, I)
    assert to_expr(Number(1, F(2, 3))) == Add(1, Mul(2, Pow(3, -1), I))
    assert to_expr(Number(F(1, 2), F(1, 2))) == Add(Pow(2, -1), Mul(Pow(2, -1), I))
    for re in rationals[::7]:
        for im in rationals[::5]:
            e = to_expr(Number(re, im))
            assert value(e) == Number(re, im) and is_canonical_number(e)
    assert not is_canonical_number(Mul(I, 2))


@pytest.mark.parametrize("b, e, expected", [
    (F(1, 5), F(1, 2), Mul(Pow(5, -1), Pow(5, Pow(2, -1)))),
    (F(1, 5), F(3, 2), Mul(Pow(25, -1), Pow(5, Pow(2, -1)))),
    (25, F(1, 3), Pow(5, Mul(2, Pow(3, -1)))),
    (8, F(2, 3), NumberKind(4)),
    (F(2, 3), F(3, 2), Mul(2, Pow(9, -1), Pow(6, Pow(2, -1)))),
    (F(1, 6), F(9, 4), Mul(Pow(216, -1), Pow(6, Mul(3, Pow(4, -1))))),
    (F(3, 7), F(7, 3), Mul(9, Pow(343, -1), Pow(3, Pow(3, -1)), Pow(7, Mul(2, Pow(3, -1))))),
    (2, 3, NumberKind(8)),
    (-2, -5, Mul(-1, Pow(32, -1))),
    (5, F(-1, 2), Mul(Pow(5, -1), Pow(5, Pow(2, -1)))),
    (F(2, 3), F(1, 2), Mul(Pow(3, -1), Pow(6, Pow(2, -1)))),
    (-4, F(1, 2), Mul(2, I)),
    (-3, F(1, 2), Mul(I, Pow(3, Pow(2, -1)))),
    (-8, F(1, 3), Mul(2, Pow(-1, Pow(3, -1)))),
    (-1, F(4, 3), Mul(-1, Pow(-1, Pow(3, -1)))),
    (-1, F(3, 2), Mul(-1, I)),
    (Number(3, 4), F(1, 2), Add(2, I)),
    (Number(-3, -4), F(1, 2), Add(1, Mul(-2, I))),
    (Number(0, 2), F(1, 2), Add(1, I)),
    (Number(0, 1), 5, I),
    (Number(1, 1), -2, Mul(-1, Pow(2, -1), I)),
    (0, F(1, 2), NumberKind(0)),
    (65537**2 * 4, F(1, 2), NumberKind(131074)),
    (65537**3 * 3, F(1, 3), Mul(65537, Pow(3, Pow(3, -1)))),
])
def test_power_examples(b, e, expected):
    assert power(_number(b), _number(e)) == expected


@pytest.mark.parametrize("b, e", [(5, F(1, 2)), (12, F(1, 3)), (-2, F(1, 3)), (-1, F(1, 3)), (0, -1),
                                  (0, 0), (0, F(-1, 2)), (Number(1, 1), F(1, 2)), (2, Number(0, 1))])
def test_power_leaves_these_alone(b, e):
    assert power(_number(b), _number(e)) is None


def test_power_is_exact_and_idempotent():
    bases = [Number(r) for r in rationals] + [Number(a, b) for a in range(-4, 5) for b in (-4, -2, 1, 3)]
    for b in bases:
        for e in exponents:
            result = power(b, Number(e))
            if result is None:
                continue
            want = 0 if b == 0 else complex(b.re, b.im) ** float(e)
            assert abs(number(result) - want) < 1e-9 * max(1, abs(want)), (b, e, result)
            for p in pows(result):
                assert power(value(p.args[0]), value(p.args[1])) in (None, p), (b, e, result)


def test_compare():
    one, two, i = Number(1), Number(2), Number(0, 1)
    assert compare(Eq, i, i) == true and compare(Ne, i, i) == false and compare(Eq, one, two) == false
    assert compare(Lt, one, two) == true and compare(Le, two, two) == true
    assert compare(Gt, one, two) == false and compare(Ge, two, one) == true
    assert compare(Lt, i, two) is None and compare(Ge, one, i) is None

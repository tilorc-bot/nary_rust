import pytest
from nary import Gt, I, Lt, Mul, NumberKind, Pow, cos, exp, pi, re, sin, tan
from nary.simplify import simplify
from test_soundness import needs_mpmath

x, y = NumberKind("x"), NumberKind("y")
half = Pow(2, -1)


def same(a, b, known=()):
    return simplify(a, list(known)) == simplify(b, list(known))


@pytest.mark.parametrize("e, known", [
    (sin(y), [Lt(y, 0)]),
    (cos(y), [Lt(y, 0)]),
    (tan(2 * y), [Lt(y, 0)]),
    (sin(x - y), [Gt(x, 0)]),
])
def test_unchanged(e, known):
    assert simplify(e, known) == e


@pytest.mark.parametrize("e, expected", [
    (sin(-3 * x), -sin(3 * x)),
    (cos(-x * half), cos(x * half)),
    pytest.param(sin(5 - y), -sin(y - 5), marks=needs_mpmath),
    (cos(-x - 2), cos(x + 2)),
    pytest.param(tan(half - y), -tan(y - half), marks=needs_mpmath),
    pytest.param(cos(pi / 6 - y), sin(y + pi / 3), marks=needs_mpmath),
    (cos(x + 5 * pi / 4), -cos(x + pi / 4)),
    (sin(Mul(5, pi, Pow(7, -1))), sin(Mul(2, pi, Pow(7, -1)))),
    (cos(Mul(9, pi, Pow(7, -1))), -cos(Mul(2, pi, Pow(7, -1)))),
    (tan(pi / 3), Pow(3, half)),
    (tan(2 * pi / 3), -Pow(3, half)),
    (cos(Mul(2, pi, Pow(5, -1))), Pow(5, half) / 4 - Pow(4, -1)),
    (sin(Mul(17, pi, Pow(12, -1))), -(Pow(2, half) + Pow(6, half)) / 4),
    (re(-2 * y * I + 3), 3 + 2 * re(-I * y)),
])
def test_evaluated(e, expected):
    assert same(e, expected)


def test_real_parts():
    assert simplify(re(-2 * y / 3), [Lt(y, 0)]) == simplify(-2 * y / 3)
    assert simplify(re(exp(y)), [Lt(y, 0)]) == exp(y)

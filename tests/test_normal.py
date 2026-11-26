import pytest

from nary import Add, Eq, Ge, I, Le, Lt, Mul, Ne, NumberKind, Pow, exp, log, re, sin
from nary.logic import false, true
from nary.normal import laws, normal

x, y, z, a = NumberKind("x"), NumberKind("y"), NumberKind("z"), NumberKind("a")
half, third = Pow(2, -1), Pow(3, -1)


def nonzero(*symbols):
    return lambda condition: condition in [Ne(s, 0) for s in symbols]


def bottom_up(e, known=None):
    if e.head is None:
        return e
    return normal(e.head(*(bottom_up(arg, known) for arg in e.args)), known)


def subexpressions(e):
    yield e
    if e.head is not None:
        for arg in e.args:
            yield from subexpressions(arg)


CASES = [
    (x + y, Add(x, y)),
    (y + x, Add(x, y)),
    (x + x + x, Mul(3, x)),
    (2 * x + 3 * x, Mul(5, x)),
    (x * x, Pow(x, 2)),
    (x**2 * x, Pow(x, 3)),
    (x * y - y * x, NumberKind(0)),
    (2 * (x + y), Add(Mul(2, x), Mul(2, y))),
    ((x * y) ** 2, Mul(Pow(x, 2), Pow(y, 2))),
    ((x**half) ** 2, x),
    (x**half * x**half, x),
    (2 * x * 3, Mul(6, x)),
    (-(-x), x),
    (2 * half, NumberKind(1)),
    (half + third, Mul(5, Pow(6, -1))),
    (Pow(4 * x, half), Mul(2, Pow(x, half))),
    (Pow(2, half) * Pow(2, half) * x, Mul(2, x)),
    (Pow(2, half) * x * Pow(2, half) * Pow(2, half), Mul(2, Pow(2, half), x)),
    (1 + 2 * x + x**2 + x - x, Add(1, Pow(x, 2), Mul(2, x))),
    (I * I + x, Add(-1, x)),
    (x + 1 + 2 * I + x, Add(1, Mul(2, I), Mul(2, x))),
    (sin(x) * 0 + y, y),
    (log(y) * 0 + y, Add(y, Mul(0, log(y)))),
    (x**3 / x, Mul(Pow(x, -1), Pow(x, 3))),
    (x * z * y * x / 2, Mul(half, Pow(x, 2), y, z)),
    (Pow(x * y, half) * Pow(x * y, half), Mul(x, y)),
    (x**z * x**y, Mul(Pow(x, y), Pow(x, z))),
    (x + I * x, Add(x, Mul(I, x))),
    (2 * I * x + I * x / 2, Mul(5, half, I, x)),
    ((1 + I) * (x + y), Mul(Add(1, I), Add(x, y))),
    ((1 + I) * (1 - I), Mul(Add(1, Mul(-1, I)), Add(1, I))),
    ((1 + I) * (1 + I) * 2, Mul(2, Pow(Add(1, I), 2))),
    (2 * (1 + I), Add(2, Mul(2, I))),
    (Pow(1 + I, -1), Add(half, Mul(-1, half, I))),
    (Pow(Pow(3 + 4 * I, half), 3), Pow(Add(2, I), 3)),
    (Pow(2 * I, 3 * half), Pow(Add(1, I), 3)),
    (Pow(5, -half), Mul(Pow(5, -1), Pow(5, half))),
    (Pow(5, half) ** 3, Mul(5, Pow(5, half))),
    (Pow(25, third) * Pow(5, third), NumberKind(5)),
    (Pow(-8, third) * x, Mul(2, Pow(-1, third), x)),
    (Pow(-4, half) + x, Add(Mul(2, I), x)),
    (x**a * x**a, Pow(x, Mul(2, a))),
    (x**a * x ** (2 * a) * x**-a, Mul(Pow(x, Mul(-1, a)), Pow(x, Mul(3, a)))),
    (x**-1 * x**-2, Pow(x, -3)),
    (Pow(2, half) * Pow(3, half) * x, Mul(Pow(6, half), x)),
    (Pow(2, third) * Pow(4, third), NumberKind(2)),
    (Pow(12, half) * Pow(3, half), NumberKind(6)),
    (Pow(2, half) * Pow(3, half) * Pow(6, third), Pow(6, Mul(5, Pow(6, -1)))),
    (Pow(2, -1 - x), Mul(half, Pow(2, Mul(-1, x)))),
    (Pow(2, x) * Pow(2, y), Pow(2, Add(x, y))),
    (2 * Pow(2, x), Mul(2, Pow(2, x))),
    (Pow(0, 2 * x), Pow(0, x)),
    (Pow(0, x / 2) * Pow(0, x), Pow(0, x)),
    (Pow(0, -x), Pow(0, Mul(-1, x))),
    (exp(x) ** 2, exp(Mul(2, x))),
    (exp(x + 1) ** -1, exp(Add(-1, Mul(-1, x)))),
    (exp(x) ** half, Pow(exp(x), half)),
]


@pytest.mark.parametrize("e, expected", CASES)
def test_normal_form(e, expected):
    assert bottom_up(e) == expected


@pytest.mark.parametrize("e", [e for e, _ in CASES] + [log(y) - log(y), x / x, x * y / (y * x)])
@pytest.mark.parametrize("known", [None, nonzero(x, y)])
def test_stable(e, known):
    result = bottom_up(e, known)
    assert normal(result, known) == result
    assert bottom_up(result, known) == result
    for sub in subexpressions(result):
        assert normal(sub, known) == sub


def test_order_does_not_matter():
    assert bottom_up(x * (y + z) + x) == bottom_up(x + (z + y) * x)
    assert bottom_up(sin(x) * y**2 * 3) == bottom_up(3 * y**2 * sin(x))


def test_no_value_is_kept():
    assert bottom_up(log(y) - log(y)) == Mul(0, log(y))
    assert bottom_up(Pow(0, -1) * 0) == Mul(0, Pow(0, -1))
    assert bottom_up(Pow(0, -1)) == Pow(0, -1)


def test_nonzero_base():
    assert bottom_up(x / x) == Mul(Pow(x, -1), x)
    assert bottom_up(x / x, nonzero(x)) == NumberKind(1)
    assert bottom_up(x**-1 * x**2) == Mul(Pow(x, -1), Pow(x, 2))
    assert bottom_up(x**-1 * x**2, nonzero(x)) == x
    assert bottom_up(Pow(x, 0)) == Pow(x, 0)
    assert bottom_up(Pow(x, 0), nonzero(x)) == NumberKind(1)
    assert bottom_up((x**2) ** -1) == Pow(Pow(x, 2), -1)
    assert bottom_up((x**2) ** -1, nonzero(x)) == Pow(x, -2)
    assert bottom_up(x * x * x**-1) == Mul(Pow(x, -1), Pow(x, 2))


def test_laws_are_named():
    assert all(law.name for law in laws)
    assert len({law.name for law in laws}) == len(laws)


def test_numbers_are_compared():
    assert bottom_up(Lt(1, 2)) == true
    assert bottom_up(Ge(half, 1)) == false
    assert bottom_up(Le(x - x, 0)) == true
    assert bottom_up(Eq(I * I, -1)) == true
    assert bottom_up(Ne(2 * half, 1)) == false
    assert bottom_up(Lt(I, 2)) == Lt(I, 2)
    assert bottom_up(Lt(x, 2)) == Lt(x, 2)


def test_real_part_of_a_number():
    assert bottom_up(re(3 + 2 * I)) == NumberKind(3)
    assert bottom_up(re(I / 2)) == NumberKind(0)
    assert bottom_up(re(x)) == re(x)

import pytest

from nary import E, Eq, Gt, I, Lt, Mul, Ne, NumberKind, Pow, exp, re
from nary.simplify import simplify

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
half = Pow(2, -1)
positive, negative, real = [Gt(y, 0)], [Lt(y, 0)], [Eq(re(x), x)]

CASES = [
    (Pow(3 * half, y), [], Pow(Mul(3, half), y)),
    (Pow(half, x), [], Pow(half, x)),
    (Pow(-1, 7 + 2 * x), [], Pow(-1, 7 + 2 * x)),
    (Pow(Mul(-1, Pow(4, -1), Pow(y, -1)), Pow(-3, x)), positive,
     Pow(Mul(-1, Pow(4, -1), Pow(y, -1)), Pow(-3, x))),
    (Pow(2 * y, x), positive, Pow(Mul(2, y), x)),
    (Pow(2, x) * Pow(3, x), [], Pow(6, x)),
    (exp(x) * exp(2), [], Mul(exp(2), exp(x))),
    (exp(x) * exp(x), [], exp(Mul(2, x))),
    (E * exp(-1) * y, [], y),
    (x * x**x, positive, Mul(x, Pow(x, x))),
    (x * Pow(x, -2), [], Pow(x, -1)),
    (Pow(Pow(x, 3), -1), [], Pow(x, -3)),
    (Pow(Pow(y, half), 3 * half), [], Pow(y, Mul(3, Pow(4, -1)))),
    (Pow(Pow(y, -half), -1), [], Pow(Pow(y, Mul(-1, half)), -1)),
    (Pow(Pow(y, -half), -1), [Ne(y, 0)], Pow(y, half)),
    (Pow(Mul(-9, y), 3 * half), negative, Mul(27, Pow(Mul(-1, y), 3 * half))),
    (Pow(Mul(-2, x), 3 * half), real, Mul(2, Pow(2, half), Pow(Mul(-1, x), 3 * half))),
    (Pow(Mul(E, Pow(y, -1)), half), [Ne(y, 0)], Mul(Pow(Pow(y, -1), half), exp(half))),
    (Pow(Mul(z, Pow(y, -1)), 3 * half), [*negative, Gt(z, 0)],
     Mul(-1, I, Pow(z, 3 * half), Pow(Mul(-1, y), Mul(-3, half)))),
    (2 * (x + 1), [], 2 * x + 2),
]


@pytest.mark.parametrize("e, known, expected", CASES)
def test_simplify_matches_automatic_evaluation(e, known, expected):
    assert simplify(e, known) == simplify(expected, known)

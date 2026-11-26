from nary import Eq, Lambda, Ne, NumberKind, Pow, cos, exp, log, re, sin
from nary.logic import And, BoolKind, Not, Or, false, true
from nary.simplify import simplify

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
p = BoolKind("p")


def test_numbers():
    assert simplify(NumberKind(2) + 3) == NumberKind(5)


def test_collecting():
    assert simplify(x + x + x) == 3 * x
    assert simplify(2 * x + 3 * x) == 5 * x
    assert simplify(x * x) == x**2
    assert simplify(x**2 * x) == x**3
    assert simplify(-(-x)) == x


def test_order():
    assert simplify(y + x) == simplify(x + y)
    assert simplify(z * y * x) == simplify(x * y * z)


def test_elementary():
    assert simplify(sin(0)) == NumberKind(0)
    assert simplify(log(exp(x))) == log(exp(x))
    assert simplify(log(exp(x)), [Eq(re(x), x)]) == x


def test_logic():
    assert simplify(And(p, true)) == p
    assert simplify(Not(Not(p))) == p
    assert simplify(Eq(x, x)) == true


def test_cancelling_needs_a_nonzero_value():
    assert simplify(x / x) != NumberKind(1)
    assert simplify(x / x, [Ne(x, 0)]) == NumberKind(1)
    assert simplify(x / x, lambda c: c == Ne(x, 0)) == NumberKind(1)


def test_beta_reduction():
    assert simplify(Lambda(y, y + y)(x)) == 2 * x


def test_a_long_sum():
    terms = [NumberKind(f"x{i}") for i in range(10)]
    e = sum(terms[1:], terms[0])
    assert simplify(e + e) == simplify(2 * e)

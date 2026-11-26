import pytest

import nary as nr
from nary import I, Many, Ne, NumberKind, Pow, declare_function, exp, log, sin
from nary._identities import associative, commutative, declare_identities, idempotent, identity, repeats
from nary.logic import And, Not, Or, false, true
from nary.normalising import normalise

x, y, a, n, b, k = (NumberKind(name) for name in "xyanbk")
p, q = nr.BoolKind("p"), nr.BoolKind("q")
half = Pow(2, -1)


def same(e, expected):
    return normalise(e) == (expected if isinstance(expected, nr.Expr) else NumberKind(expected))


Max = declare_function("Max", Many(NumberKind), returns=NumberKind, domain=true)
declare_identities(Max, [associative, commutative, idempotent])
Rep = declare_function("Rep", b, k, returns=NumberKind, domain=true)
Cat = declare_function("Cat", Many(NumberKind), returns=NumberKind, domain=true)
declare_identities(Cat, [associative, identity(0), repeats(Rep(a, n), n)])
Part = declare_function("Part", b, k, returns=NumberKind, domain=Ne(k, 0))
Seq = declare_function("Seq", Many(NumberKind), returns=NumberKind, domain=true)
declare_identities(Seq, [associative, identity(0), repeats(Part(a, n), n)])


@pytest.mark.parametrize("e, expected", [
    (x + (y + x) + 0, y + 2 * x),
    (x * (y * 1) * x, nr.Mul(y, x ** 2)),
    (3 * x + 2 * x - 5 * x, 0),
    (x * x ** 2 * x ** half, x ** nr.Mul(7, half)),
    (nr.Add(), 0),
    (nr.Mul(x), x),
    (And(q, Or(p, false), q, true), And(p, q)),
    (Or(p, true, q), true),
    (And(p, false), false),
    (Not(Not(Not(p))), Not(p)),
    (Max(x, y, x, Max(y, 3)), Max(3, x, y)),
    (Cat(x, Rep(x, 2), y, x), Cat(Rep(x, 3), y, x)),
    (Cat(Cat(x, 0), Rep(x, -1)), 0),
    (Cat(y, Rep(x, 1)), Cat(y, x)),
])
def test_the_declared_laws(e, expected):
    assert same(e, expected)


@pytest.mark.parametrize("e, expected", [
    (sin(x) * 0, 0),
    (log(x) * 0, nr.Mul(0, log(x))),
    (x / x, x ** 0),
    (x ** 2 / x, nr.Mul(x ** -1, x ** 2)),
    (x ** -1 * x ** -1, x ** -2),
    (exp(x) * 0 + log(y) - log(y), nr.Mul(0, log(y))),
    (Seq(x, Part(x, -1)), Seq(x, Part(x, -1))),
    (Seq(Part(x, 2), Part(x, 3)), Part(x, 5)),
])
def test_nothing_without_a_value_is_erased_or_created(e, expected):
    assert same(e, expected)


def test_known_conditions_allow_more():
    nonzero = {Ne(x, 0)}
    assert same(normalise(x / x, known=lambda c: c in nonzero), 1)
    assert normalise(x ** 2 / x, known=lambda c: c in nonzero) == x
    assert same(normalise(log(x) * 0, known=lambda c: c in nonzero), 0)


@pytest.mark.parametrize("e, expected", [
    (half + half, 1),
    (Pow(12, half), 2 * Pow(3, half)),
    (Pow(2, half) * Pow(3, half), Pow(6, half)),
    (I * I, -1),
    (Pow(-1, half), I),
    (Pow(-8, nr.Mul(2, Pow(3, -1))) * 0 + 1, 1),
    (Pow(0, -1), Pow(0, -1)),
    (Pow(0, 0), Pow(0, 0)),
    (nr.Lt(half, Pow(2, half)), true),
    (Ne(Pow(4, half), 2), false),
])
def test_numbers(e, expected):
    assert same(e, expected)


def test_a_normal_form_is_its_own_normal_form():
    cases = [
        (x + y) * (x + y) * 2 / (x + y) + x * 0,
        Pow(x, y) * Pow(x, y) * Pow(x, -y),
        sin(x + x) * sin(2 * x) + log(Pow(12, half) * x),
        And(Or(p, q), Or(q, p), Not(Not(Or(p, q)))),
        Cat(x, Cat(Rep(x, -1), x), Rep(y, 0)),
    ]
    for e in cases:
        assert normalise(normalise(e)) == normalise(e)


def test_lambdas_are_left_alone():
    f = nr.Lambda(x, x + 0)
    assert normalise(f) == f


def test_only_expressions_are_normalised():
    with pytest.raises(TypeError):
        normalise(3)

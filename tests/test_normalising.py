import pytest

import nary as nr
from nary import Many, Ne, NumberKind, Pow, declare_function, exp, log, sin, tan
from nary._identities import associative, commutative, declare_identities, idempotent
from nary.logic import And, Not, Or, false, true
from nary.normalising import normalise

x, y, z = (NumberKind(name) for name in "xyz")
p, q = nr.BoolKind("p"), nr.BoolKind("q")

Max = declare_function("Max", Many(NumberKind), returns=NumberKind, domain=true)
declare_identities(Max, [associative, commutative, idempotent])


def same(e, expected, known=None):
    expected = expected if isinstance(expected, nr.Expr) else NumberKind(expected)
    return normalise(e, known) == expected


@pytest.mark.parametrize("e, expected", [
    (x + (y + x) + 0, nr.Add(x, x, y)),
    (z * (y * 1) * x, nr.Mul(x, y, z)),
    (nr.Add(3, 2), nr.Add(2, 3)),
    (nr.Add(), 0),
    (nr.Mul(x), x),
    (nr.Mul(1, 1), 1),
    (x * 0 * y, 0),
    (nr.Mul(0, 2), 0),
    (And(q, Or(p, false), q, true), And(p, q)),
    (Or(p, true, q), true),
    (And(p, false), false),
    (Or(p, Or(q, p)), Or(p, q)),
    (Max(x, y, x, Max(y, 3)), Max(3, x, y)),
    (Max(x, x), x),
    (Max(), Max()),
    (Max(Max(y), x, y), Max(x, y)),
])
def test_the_declared_laws(e, expected):
    assert same(e, expected)


@pytest.mark.parametrize("e, expected", [
    (sin(x) * 0, 0),
    (exp(sin(x)) * 0, 0),
    (log(x) * 0, nr.Mul(0, log(x))),
    (tan(x) * y * 0, nr.Mul(0, y, tan(x))),
    (x / x, nr.Mul(x, x ** -1)),
])
def test_nothing_without_a_value_is_erased(e, expected):
    assert same(e, expected)


def test_known_conditions_allow_more():
    assert same(log(x) * 0, 0, known=lambda c: c == Ne(x, 0))
    assert same(log(x) * 0, nr.Mul(0, log(x)), known=lambda c: 1)


@pytest.mark.parametrize("e, expected", [
    (Pow(x, 1), Pow(x, 1)),
    (Pow(x * 1, 0 + nr.Mul(1)), Pow(x, 1)),
    (Pow(1, x + y), Pow(1, nr.Add(x, y))),
    (Not(Not(p)), Not(Not(p))),
    (Not(And(q, p, true)), Not(And(p, q))),
    (exp(log(y + 0)), exp(log(y))),
])
def test_other_heads_only_get_normal_arguments(e, expected):
    assert normalise(e) == expected


def test_a_normal_form_is_its_own_normal_form():
    cases = [
        (x + y) * (y + x) * 1 + x * 0,
        sin(x + 0) * sin(0 + x) + log(x * 1 * y),
        And(Or(p, q), Or(q, p), Not(Not(Or(p, q)))),
        Or(And(p, false), And(q, q), p),
        Pow(x * 0 + 1, Max(x, x)),
        Max(Max(x, 0), Max(y, x), sin(x)),
    ]
    for e in cases:
        assert normalise(normalise(e)) == normalise(e)


def test_lambdas_are_left_alone():
    f = nr.Lambda(x, x + 0)
    assert normalise(f) == f


def test_only_expressions_are_normalised():
    with pytest.raises(TypeError):
        normalise(3)

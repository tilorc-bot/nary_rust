import pytest
from nary import Eq, Gt, Lambda, NumberKind, Pow, cos, exp, log, re, sin, tan
from nary.calculus import Derivative, NumberFunction
from nary.simplify import simplify

t, x = NumberKind("t"), NumberKind("x")
half = Pow(2, -1)


@pytest.mark.parametrize("f, known, expected", [
    (Lambda(t, t**2), [], 2 * x),
    (Lambda(t, sin(t) * exp(t)), [], exp(x) * sin(x) + exp(x) * cos(x)),
    (Lambda(t, sin(t**2)), [], 2 * x * cos(x**2)),
    (Lambda(t, t**3 + 2 * t), [], 3 * x**2 + 2),
    (tan, [], tan(x) ** 2 + 1),
    (log, [Gt(x, 0)], Pow(x, -1)),
    (Lambda(t, Pow(t, half)), [Gt(x, 0)], half * Pow(x, -half)),
])
def test_derivative(f, known, expected):
    assert simplify(Derivative(f)(x), known) == simplify(expected)


@pytest.mark.parametrize("f, point", [
    (log, x),
    (log, NumberKind(-2)),
    (Lambda(t, Pow(t, half)), x),
    (Lambda(t, NumberFunction("f")(t)), x),
])
def test_no_derivative_where_it_may_not_exist(f, point):
    assert simplify(Derivative(f)(point)) == Derivative(f)(point)

import pytest
from nary import Lambda, NumberKind, sin
from nary.calculus import (
    Antiderivative, Derivative, Integral, Limit, NumberFunction, Product, Sum,
)

x, y, a, b = (NumberKind(n) for n in "xyab")
f = NumberFunction("f")


def test_each_function_and_its_result_kind():
    for expr, text, result in (
        (Integral(f, a, b), "Integral(f, a, b)", NumberKind),
        (Sum(f, a, b), "Sum(f, a, b)", NumberKind),
        (Product(f, a, b), "Product(f, a, b)", NumberKind),
        (Limit(f, a), "Limit(f, a)", NumberKind),
        (Derivative(f), "Derivative(f)", NumberFunction),
        (Antiderivative(f), "Antiderivative(f)", NumberFunction),
    ):
        assert repr(expr) == text
        assert expr.kind is result


def test_integral_of_a_lambda_a_declared_and_an_unknown_function():
    square = Lambda(x, x * x)
    for integrand in (square, sin, f):
        integral = Integral(integrand, a, b)
        assert integral.function == integrand
        assert (integral.lower, integral.upper) == (a, b)
    assert repr(Integral(square, a, b)) == "Integral(Lambda(x, Mul(x, x)), a, b)"


def test_derivative_at_a_point_and_second_derivative():
    at_a = Derivative(f)(a)
    assert repr(at_a) == "Derivative(f)(a)"
    assert at_a.head == Derivative(f) and at_a.kind is NumberKind
    second = Derivative(Derivative(f))
    assert second.arg == Derivative(f)
    assert second.kind is NumberFunction


def test_only_a_function_of_one_number_is_accepted():
    with pytest.raises(TypeError, match=r"^Integral expects FunctionKind\(\(NumberKind,\), NumberKind\), got NumberKind: Mul\(x, x\)$"):
        Integral(x * x, a, b)
    with pytest.raises(TypeError, match=r"^Derivative expects .* got FunctionKind\(\(NumberKind, NumberKind\), NumberKind\)"):
        Derivative(Lambda((x, y), x * y))

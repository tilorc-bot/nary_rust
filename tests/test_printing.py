import pytest
from nary import (
    Add, BoolKind, E, Eq, I, Lambda, Mul, Ne, NumberKind, Pow, exp, log, pi, sin,
)
from nary.calculus import Derivative, Integral, Limit, NumberFunction
from nary.logic import And, Not, Or, true
from nary.matrices import Determinant, MatMul, Matrix, Transpose

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
p, q = BoolKind("p"), BoolKind("q")
f = NumberFunction("f")
A, B = Matrix("A"), Matrix("B")
half = Pow(2, -1)


@pytest.mark.parametrize("e, text", [
    (x + y * z**2 < 1, "x + y*z**2 < 1"),
    (Add(Add(x, y), z), "x + y + z"),
    (Mul(x, Mul(y, z)), "x*y*z"),
    (x - y, "x - y"),
    (x - 1, "x - 1"),
    (x + -1, "x - 1"),
    (x - 3 * y, "x - 3*y"),
    (x - (y + z), "x - (y + z)"),
    (-x + y, "-x + y"),
    (Add(-1, I), "-1 + I"),
    (Add(x), "Add(x)"),
    (Add(), "Add()"),
])
def test_sums(e, text):
    assert str(e) == text


@pytest.mark.parametrize("e, text", [
    (Mul(3, half), "3/2"),
    (half, "1/2"),
    (Mul(-1, half), "-1/2"),
    (x / y, "x/y"),
    (Pow(x, -1), "1/x"),
    (Pow(x, -2), "1/x**2"),
    (Pow(x, Mul(-1, y)), "1/x**y"),
    (x / (y * z), "x/(y*z)"),
    (x / (y + 1), "x/(y + 1)"),
    (Mul(Mul(x, Pow(y, -1)), z), "x*z/y"),
    (Mul(half, I, pi), "I*pi/2"),
    (Pow(Pow(x, -1), -1), "1/(1/x)"),
])
def test_fractions(e, text):
    assert str(e) == text


@pytest.mark.parametrize("e, text", [
    (-x, "-x"),
    (-(x**2), "-x**2"),
    ((-x) ** 2, "(-x)**2"),
    (-(x + y), "-(x + y)"),
    (Mul(-2, I), "-2*I"),
    (-x / y, "-x/y"),
    (Mul(x, -2), "x*(-2)"),
    (x * -y, "x*(-1)*y"),
    (Mul(-1, Mul(-1, x)), "-(-1)*x"),
    (Pow(-2, x), "(-2)**x"),
])
def test_signs(e, text):
    assert str(e) == text


@pytest.mark.parametrize("e, text", [
    (x**y**z, "x**y**z"),
    ((x**y) ** z, "(x**y)**z"),
    ((x * y) ** 2, "(x*y)**2"),
    (x ** (y - 1), "x**(y - 1)"),
    (Pow(x, Mul(3, half)), "x**(3/2)"),
    (Pow(2, Pow(3, -1)), "2**(1/3)"),
    (Pow(x, half), "sqrt(x)"),
    (Pow(x, Mul(-1, half)), "1/sqrt(x)"),
    (Mul(2, Pow(3, half)), "2*sqrt(3)"),
    (Pow(Pow(I, half), Mul(9, half)), "sqrt(I)**(9/2)"),
    (sin(x) ** 2, "sin(x)**2"),
])
def test_powers(e, text):
    assert str(e) == text


@pytest.mark.parametrize("e, text", [
    (Eq(x, y), "x == y"),
    (Ne(x + 1, 0), "x + 1 != 0"),
    (x >= y, "x >= y"),
    (And(x < y, Not(Eq(x, y)), true), "x < y and not x == y and true"),
    (And(Or(p, q), p), "(p or q) and p"),
    (Or(And(p, q), Not(Or(p, q))), "(p and q) or not (p or q)"),
    (And(And(p, q), p), "p and q and p"),
    (Not(Not(p)), "not not p"),
])
def test_relations_and_logic(e, text):
    assert str(e) == text


@pytest.mark.parametrize("e, text", [
    (log(exp(x) + E), "log(exp(x) + E)"),
    (f(x) + Derivative(f)(y), "f(x) + Derivative(f)(y)"),
    (Derivative(Derivative(sin)), "Derivative(Derivative(sin))"),
    (Lambda((x, y), x < y), "lambda x, y: x < y"),
    (Lambda(x, sin(x))(y + 1), "(lambda x: sin(x))(y + 1)"),
    (Lambda(x, Lambda(y, x + y)), "lambda x: lambda y: x + y"),
    (And(Lambda(x, x < 1)(y), p), "(lambda x: x < 1)(y) and p"),
    (Integral(Lambda(x, x * x), 0, y), "Integral(lambda x: x*x, 0, y)"),
    (Limit(Lambda(x, sin(x) * x), 0), "Limit(lambda x: sin(x)*x, 0)"),
    (Transpose(A + B) * A, "Transpose(A + B)*A"),
    (MatMul(MatMul(A, B), A), "A*B*A"),
    (Determinant(A * B) + x, "Determinant(A*B) + x"),
])
def test_calls_lambdas_and_matrices(e, text):
    assert str(e) == text


def test_repr_is_still_structural():
    e = x / (y + 1) - y
    assert repr(e) == "Add(Mul(x, Pow(Add(y, 1), -1)), Mul(-1, y))"
    assert str(e) == f"{e}" == "x/(y + 1) - y"

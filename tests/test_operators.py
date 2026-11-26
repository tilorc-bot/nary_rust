import pytest

import nary as nr

x, y, z = (nr.NumberKind(n) for n in "xyz")
p, q = nr.BoolKind("p"), nr.BoolKind("q")


def test_new_operators_build_their_functions():
    assert x ** y == nr.Pow(x, y)
    assert (x > y) == nr.Gt(x, y)
    assert (x <= y) == nr.Le(x, y)
    assert (x >= y) == nr.Ge(x, y)
    assert (x > y).kind is nr.BoolKind


def test_a_kind_without_the_operators_does_not_support_them():
    with pytest.raises(TypeError):
        p ** q
    with pytest.raises(TypeError, match="'>=' not supported between instances"):
        p >= q


def test_pow_with_a_modulus_is_a_type_error():
    with pytest.raises(TypeError, match="modulus"):
        pow(x, y, z)


def test_subtraction_division_and_negation_are_built_from_add_mul_and_pow():
    assert repr(x - y) == "Add(x, Mul(-1, y))"
    assert x - y == nr.Add(x, nr.Mul(nr.NegativeOne, y))
    assert repr(x / y) == "Mul(x, Pow(y, -1))"
    assert repr(-x) == "Mul(-1, x)"
    assert (x - y).kind is (x / y).kind is (-x).kind is nr.NumberKind


def test_negative_one_is_a_literal():
    assert nr.NegativeOne == nr.NumberKind(-1) and nr.NegativeOne.is_literal
    assert repr(nr.NegativeOne) == "-1" and nr.NegativeOne.kind is nr.NumberKind


def test_a_kind_without_minus_or_divide_does_not_support_them():
    with pytest.raises(TypeError, match="unsupported operand"):
        p - q
    with pytest.raises(TypeError, match="unsupported operand"):
        p / q
    with pytest.raises(TypeError, match="bad operand type for unary -"):
        -p


def test_a_python_operator_must_return_an_expression():
    Point = nr.declare_kind("Point")
    nr.set_operator(Point, "-", lambda a, b: (a, b))
    nr.set_operator(Point, "neg", lambda a: nr.ManyAlike)
    P, Q = Point("P"), Point("Q")
    with pytest.raises(TypeError, match=r"^the - operator for Point must return an expression, got tuple: \(P, Q\)$"):
        P - Q
    with pytest.raises(TypeError, match="^the neg operator for Point must return an expression"):
        -P

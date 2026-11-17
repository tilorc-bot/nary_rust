"""The operators, which are set for each kind."""

import nary as nr
import pytest
from nary import BoolKind, MatrixKind, NumberKind

Matrix = MatrixKind(NumberKind)


def test_arithmetic(xyz):
    x, y, z = xyz
    assert repr(x + y) == "Add(x, y)"
    assert repr(x * y) == "Mul(x, y)"
    assert repr(x**y) == "Pow(x, y)"
    assert repr(x + y + z) == "Add(Add(x, y), z)"
    assert repr(x + y * z**2) == "Add(x, Mul(y, Pow(z, 2)))"
    assert x + y == nr.Add(x, y)
    assert (x**y).base == x


def test_int_on_the_right(xyz):
    x, y, z = xyz
    assert repr(x + 1) == "Add(x, 1)"
    assert repr(x * 2) == "Mul(x, 2)"
    assert repr(x**2) == "Pow(x, 2)"
    assert (x + 1).args[1] == nr.Integer(1)


def test_int_on_the_left(xyz):
    x, y, z = xyz
    assert repr(1 + x) == "Add(1, x)"
    assert repr(2 * x) == "Mul(2, x)"
    assert repr(2**x) == "Pow(2, x)"
    assert (1 + x).args[0] == nr.Integer(1)
    assert 1 + x != x + 1


def test_comparisons(xyz):
    x, y, z = xyz
    for expr, text in [
        (x < y, "Lt(x, y)"),
        (x > y, "Gt(x, y)"),
        (x <= y, "Le(x, y)"),
        (x >= y, "Ge(x, y)"),
        (x < 1, "Lt(x, 1)"),
        (x >= 0, "Ge(x, 0)"),
        (nr.sin(x) * y < z, "Lt(Mul(sin(x), y), z)"),
    ]:
        assert expr.kind is BoolKind
        assert repr(expr) == text
    assert (x <= y).lhs == x and (x <= y).rhs == y


def test_comparison_with_int_on_the_left_is_reflected(xyz):
    x, y, z = xyz
    assert repr(1 < x) == "Gt(x, 1)"
    assert repr(1 > x) == "Lt(x, 1)"
    assert repr(1 <= x) == "Ge(x, 1)"
    assert repr(1 >= x) == "Le(x, 1)"


def test_eq_and_ne_compare_structure(xyz):
    x, y, z = xyz
    assert (x == x) is True
    assert (x == y) is False
    assert (x != y) is True
    assert (x == 1) is False
    assert (x + 1 == x + 1) is True
    assert hash(x + 1) == hash(x + 1)
    assert {x + y: 1}[x + y] == 1


def test_operand_of_the_wrong_kind(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        x + (x < y)
    with pytest.raises(TypeError, match=r"^Mul expects NumberKind, got float: 1.5$"):
        x * 1.5
    with pytest.raises(TypeError, match=r"^Mul expects NumberKind, got float: 1.5$"):
        1.5 * x
    with pytest.raises(TypeError, match=r"^Lt expects NumberKind, got str: 'a'$"):
        x < "a"
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got MatrixKind\(NumberKind\): A$"):
        x + Matrix("A")
    with pytest.raises(TypeError, match=r"^Pow expects NumberKind, got bool: True$"):
        x**True


def test_no_subtraction_or_division(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError):
        x - y
    with pytest.raises(TypeError):
        x / y
    with pytest.raises(TypeError):
        -x


def test_pow_with_modulus(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match="modulus"):
        pow(x, y, z)


def test_a_kind_with_no_operators_does_not_support_them():
    p, q = BoolKind("p"), BoolKind("q")
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \+"):
        p + q
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \*\*"):
        p**q
    with pytest.raises(TypeError, match="'<' not supported between instances"):
        p < q
    with pytest.raises(TypeError, match="unsupported operand"):
        1 + p
    with pytest.raises(TypeError, match="unsupported operand"):
        pow(p, q, q)
    assert (p == p) is True


def test_matrix_operators_build_the_matrix_functions(xyz):
    x, y, z = xyz
    a, b = Matrix("A"), Matrix("B")
    assert repr(a + b) == "MatAdd(A, B)"
    assert repr(a * b) == "MatMul(A, B)"
    assert repr(x * y) == "Mul(x, y)"
    assert (a * b).head != (x * y).head
    assert (a * b).kind is Matrix and (x * y).kind is NumberKind
    assert repr(a * b + a) == "MatAdd(MatMul(A, B), A)"
    assert a * b == nr.MatMul(a, b)


def test_matrix_has_only_the_operators_set_for_it():
    a, b = Matrix("A"), Matrix("B")
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \*\*"):
        a**b
    with pytest.raises(TypeError, match="'<' not supported between instances"):
        a < b


def test_the_kind_of_an_operand_chooses_the_function(xyz):
    x, y, z = xyz
    a = Matrix("A")
    # The left operand chooses, and its function rejects the other kind.
    with pytest.raises(TypeError, match=r"^MatMul expects MatrixKind\(NumberKind\), got NumberKind: x$"):
        a * x
    with pytest.raises(TypeError, match=r"^Mul expects NumberKind, got MatrixKind\(NumberKind\): A$"):
        x * a
    # With an int on the left it is the right operand that chooses. An int is
    # a NumberKind, so it is not converted for a matrix function.
    with pytest.raises(TypeError, match=r"^MatMul expects MatrixKind\(NumberKind\), got int: 2$"):
        2 * a
    with pytest.raises(TypeError, match=r"^MatAdd expects MatrixKind\(NumberKind\), got int: 1$"):
        a + 1
    # A kind with no function for + defers to the other operand.
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got BoolKind: p$"):
        BoolKind("p") + x


def test_set_operator_once_for_each_kind_and_operator():
    with pytest.raises(ValueError, match=r"^the \+ operator is already set for NumberKind$"):
        nr.set_operator(NumberKind, "+", nr.Add)
    with pytest.raises(ValueError, match=r"^the >= operator is already set for NumberKind$"):
        nr.set_operator(NumberKind, ">=", nr.Ge)
    with pytest.raises(ValueError, match=r"^the \* operator is already set for MatrixKind\(NumberKind\)$"):
        nr.set_operator(MatrixKind(NumberKind), "*", nr.MatMul)
    with pytest.raises(ValueError, match='^unknown operator "-"$'):
        nr.set_operator(NumberKind, "-", nr.Add)
    with pytest.raises(ValueError, match='^unknown operator "/"$'):
        nr.set_operator(NumberKind, "/", nr.Mul)
    with pytest.raises(TypeError, match=r"^expected a kind, got '\+'$"):
        nr.set_operator("+", "*", nr.Add)


def test_a_long_chain_can_be_built_and_freed(xyz):
    x, y, z = xyz
    e = x
    for _ in range(2_000):
        e = e + y
    assert e.head == "Add"
    del e

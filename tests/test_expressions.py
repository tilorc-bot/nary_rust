"""Building expressions with the kinds and functions declared in nary."""

import nary as nr
import pytest
from nary import BoolKind, Expr, NumberKind
from nary.logic import true

x, y, z = (NumberKind(n) for n in "xyz")


def test_functions_and_operators():
    assert repr(nr.Add(x, y, z)) == "Add(x, y, z)"
    assert repr(x + y + z) == "Add(Add(x, y), z)"
    assert repr(x * y) == "Mul(x, y)"
    assert repr(nr.sin(x) * y < z) == "Lt(Mul(sin(x), y), z)"
    assert x + y == nr.Add(x, y)
    assert x + y + z != nr.Add(x, y, z)


def test_result_is_of_the_declared_kind():
    assert (x + y).kind is NumberKind
    assert nr.sin(x).kind is NumberKind
    assert (x < y).kind is BoolKind
    assert nr.Eq(x, y).kind is BoolKind
    # Every expression is an Expr, whatever its kind.
    assert type(x + y) is Expr and type(x < y) is Expr


def test_head_args_and_named_arguments():
    eq = nr.Eq(x + y, z)
    assert eq.head is nr.Eq
    assert eq.args == (x + y, z)
    assert (eq.lhs, eq.rhs) == (x + y, z)
    assert nr.Pow(x, y).base == x and nr.Pow(x, y).exp == y
    with pytest.raises(AttributeError, match="'Expr' object has no attribute 'base'"):
        eq.base


def test_wrong_kind_and_wrong_count():
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        nr.sin(x < y)
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got float: 1.5$"):
        nr.Add(x, 1.5)
    with pytest.raises(TypeError, match=r"^Pow takes 2 arguments, got 3$"):
        nr.Pow(x, y, z)
    with pytest.raises(TypeError, match=r"^sin takes 1 arguments, got 0$"):
        nr.sin()
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        x + (x < y)
    with pytest.raises(TypeError, match=r"^Lt expects NumberKind, got str: 'a'$"):
        x < "a"


def test_equality_and_hash_are_structural():
    assert (x == x) is True
    assert (x == y) is False
    assert (x != y) is True
    assert (x == 1) is False
    assert x == NumberKind("x") and x is not NumberKind("x")
    assert hash(x + y) == hash(x + y)
    assert hash(x + y) != hash(y + x)
    assert {x + y: 1}[nr.Add(x, y)] == 1


def test_equality_and_hash_distinguish_kinds():
    assert NumberKind("p") != BoolKind("p")
    assert hash(NumberKind("p")) != hash(BoolKind("p"))
    assert len({NumberKind("p"), BoolKind("p"), NumberKind("p")}) == 2
    f = nr.declare_function("f", NumberKind, returns=NumberKind, domain=true)
    g = nr.declare_function("f", NumberKind, returns=BoolKind, domain=true)
    assert f(x) == f(x)
    assert f(x) != g(x)


def test_a_kind_with_no_operators_does_not_support_them():
    p, q = BoolKind("p"), BoolKind("q")
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \+"):
        p + q
    with pytest.raises(TypeError, match="unsupported operand"):
        p * q
    with pytest.raises(TypeError, match="'<' not supported between instances"):
        p < q
    assert (p == p) is True


def test_operators_with_a_value_that_is_not_accepted():
    with pytest.raises(TypeError):
        x + 1.5
    with pytest.raises(TypeError):
        x > 1.5
    with pytest.raises(TypeError):
        1.5 + x


def test_a_long_chain_can_be_built_and_freed():
    e = x
    for _ in range(2_000):
        e = e + y
    assert e.head is nr.Add
    del e

import nary as nr
import pytest
from nary import BoolKind, NumberKind, Symbol, declare_function, declare_kind
from nary.logic import And, true

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")


def test_a_kind_declares_its_literal_types():
    assert NumberKind.literals == (int,) and BoolKind.literals == ()
    assert declare_kind("K", literals=(int, float)).literals == (int, float)
    assert nr.FunctionKind((NumberKind,), NumberKind).literals == ()
    assert nr.declare_kind_family("Box")(NumberKind).literals == ()
    with pytest.raises(ValueError, match="^S: str cannot be a literal type"):
        declare_kind("S", literals=(int, str))
    with pytest.raises(TypeError, match="^T: literals must be a type or a tuple of types, got 3$"):
        declare_kind("T", literals=3)


def test_calling_a_kind_with_a_value_makes_a_literal():
    three = NumberKind(3)
    assert three.is_literal and not three.is_symbol and not x.is_literal
    assert (three.value, three.kind, three.name, three.head, three.args) == (3, NumberKind, None, None, ())
    assert repr(three) == "3" and x.value is None and nr.sin(x).value is None
    with pytest.raises(TypeError, match=r"^NumberKind takes a name \(a str\) or a literal of type int, got bool: True$"):
        NumberKind(True)
    with pytest.raises(TypeError, match="^NumberKind takes .*, got float: 1.5$"):
        NumberKind(1.5)
    with pytest.raises(TypeError, match=r"^BoolKind takes a name \(a str\), got int: 1; it accepts no literals$"):
        BoolKind(1)


def test_literal_equality_and_hash():
    assert NumberKind(3) == NumberKind(3) and hash(NumberKind(3)) == hash(NumberKind(3))
    assert NumberKind(3) != NumberKind("3") and (NumberKind(3) == 3) is False
    assert NumberKind(10**30) == NumberKind(10**30)
    Other = declare_kind("Other", literals=(int, float))
    assert Other(3) != NumberKind(3)
    assert Other(1) != Other(1.0)
    assert len({NumberKind(1), NumberKind(1), Other(1), Other(1.0)}) == 3


def test_a_value_takes_the_kind_of_its_position():
    assert nr.sin(1) == nr.sin(NumberKind(1))
    assert nr.Add(x, 1, 2).args == (x, NumberKind(1), NumberKind(2))
    assert repr(nr.Pow(x, 2)) == "Pow(x, 2)"
    with pytest.raises(TypeError, match="^And expects BoolKind, got int: 1$"):
        And(p, 1)
    with pytest.raises(TypeError, match="^Add expects NumberKind, got bool: True$"):
        nr.Add(x, True)
    D = declare_function("D", NumberKind, Symbol(NumberKind), returns=NumberKind, domain=true)
    with pytest.raises(TypeError, match="^D expects a NumberKind symbol, got NumberKind: 1$"):
        D(x, 1)


def test_operators_with_an_int_build_inert_trees():
    assert x + 1 == nr.Add(x, 1)
    assert repr(x - 1) == "Add(x, Mul(-1, 1))"
    assert repr(x / 2) == "Mul(x, Pow(2, -1))"
    assert x ** 2 == nr.Pow(x, 2) and (x < 1) == nr.Lt(x, 1)
    assert (1 < x) == nr.Gt(x, 1)
    assert repr(NumberKind(2) + 3) == "Add(2, 3)"


def test_reflected_operators():
    assert 1 + x == nr.Add(1, x)
    assert repr(1 - x) == "Add(1, Mul(-1, x))"
    assert (2 * x, 2 ** x) == (nr.Mul(2, x), nr.Pow(2, x))
    assert repr(1 / x) == "Mul(1, Pow(x, -1))"
    for value in (1.5, True):
        with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \+"):
            value + x
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \*"):
        2 * p


def test_lambda_with_a_literal_body():
    assert repr(nr.Lambda(x, NumberKind(1))) == "Lambda(x, 1)"
    with pytest.raises(TypeError, match="^the body of a Lambda must be an expression, got 1$"):
        nr.Lambda(x, 1)

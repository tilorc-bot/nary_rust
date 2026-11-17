"""Symbols, integers and constants."""

import nary as nr
import pytest
from nary import BoolKind, Integer, NumberKind


def test_integer():
    n = Integer(5)
    assert type(n) is nr.Expr
    assert n.kind is NumberKind
    assert n.is_integer and not n.is_symbol
    assert n.value == 5 and type(n.value) is int
    assert n.head == "Integer"
    assert n.args == ()
    assert repr(n) == "5"
    assert repr(Integer(-3)) == "-3"


def test_integer_is_arbitrary_precision():
    assert Integer(2**200).value == 2**200
    assert repr(Integer(-(10**30))) == "-" + "1" + "0" * 30
    assert Integer(2**200) == Integer(2**200)
    assert Integer(2**200) != Integer(2**200 + 1)


def test_integer_equality_and_hash():
    assert Integer(1) == Integer(1)
    assert Integer(1) != Integer(2)
    assert hash(Integer(1)) == hash(Integer(1))
    assert Integer(1) != 1
    assert Integer(1) != NumberKind("1")
    assert Integer(1) != NumberKind("Integer")
    assert len({Integer(1), Integer(1), NumberKind("1")}) == 2


def test_integer_accepts_only_an_int():
    with pytest.raises(TypeError, match=r"^Integer expects an int, got float: 1.0$"):
        Integer(1.0)
    with pytest.raises(TypeError, match=r"^Integer expects an int, got bool: True$"):
        Integer(True)
    with pytest.raises(TypeError, match=r"^Integer expects an int, got str: '1'$"):
        Integer("1")


def test_int_is_converted_in_function_arguments(xyz):
    x, y, z = xyz
    e = nr.Add(1, x, 2)
    assert e.args == (Integer(1), x, Integer(2))
    assert all(arg.kind is NumberKind for arg in e.args)
    assert e == nr.Add(Integer(1), x, Integer(2))
    assert nr.sin(0).args == (Integer(0),)
    assert nr.Pow(x, -1).exp.value == -1


def test_int_is_converted_only_where_a_number_is_expected(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Not expects BoolKind, got int: 1$"):
        nr.Not(1)
    with pytest.raises(TypeError, match=r"^Union expects SetKind\(NumberKind\), got int: 0$"):
        nr.Union(0)
    with pytest.raises(TypeError, match=r"^Derivative expects a NumberKind symbol, got int: 1$"):
        nr.Derivative(x, 1)


def test_bool_and_float_are_not_converted(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got bool: True$"):
        nr.Add(x, True)
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got float: 0.5$"):
        nr.Add(x, 0.5)

    class MyInt(int):
        pass

    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got MyInt: 3$"):
        nr.Add(x, MyInt(3))


def test_constant_is_not_a_symbol():
    assert nr.pi.kind is NumberKind
    assert repr(nr.pi) == "pi"
    assert nr.pi.head == "pi" and nr.pi.args == ()
    assert not nr.pi.is_symbol
    assert not nr.pi.is_integer
    assert nr.pi.value is None
    symbol = NumberKind("pi")
    assert symbol.is_symbol
    assert symbol != nr.pi
    assert hash(symbol) != hash(nr.pi)
    assert nr.true.kind is BoolKind and not nr.true.is_symbol
    assert nr.true != nr.false


def test_symbol_equality_and_hash():
    assert NumberKind("x") == NumberKind("x")
    assert NumberKind("x") != NumberKind("y")
    assert hash(NumberKind("x")) == hash(NumberKind("x"))
    assert NumberKind("x").value is None
    assert not NumberKind("x").is_integer


def test_a_symbol_is_not_a_call_with_no_arguments():
    # Both have the head "Add" and no arguments, but one is a symbol and the
    # other an application of Add.
    leaf, call = NumberKind("Add"), nr.Add()
    assert (leaf.head, leaf.args) == (call.head, call.args) == ("Add", ())
    assert leaf.is_symbol and not call.is_symbol
    assert leaf != call
    assert hash(leaf) != hash(call)
    assert len({leaf, call, NumberKind("Add"), nr.Add()}) == 2
    # The same holds for a kind made by a family.
    assert nr.MatrixKind(NumberKind)("MatAdd") != nr.MatAdd()

"""Declaring and calling functions: counts, rest groups, names."""

import nary as nr
import pytest
from nary import BoolKind, NumberKind, SetKind, function


def test_inert(xyz):
    x, y, z = xyz
    assert repr(nr.Add(x, y, z)) == "Add(x, y, z)"
    assert repr(nr.Add(nr.Add(x, y), z)) == "Add(Add(x, y), z)"
    assert nr.Add(nr.Add(x, y), z) != nr.Add(x, y, z)
    assert nr.Add(x, y) != nr.Add(y, x)
    assert repr(nr.Add(x, x)) == "Add(x, x)"
    assert repr(nr.Mul(x, 1)) == "Mul(x, 1)"
    assert repr(nr.Add(2, 3)) == "Add(2, 3)"
    assert repr(nr.Add()) == "Add"
    assert nr.Add(x, y).head == "Add"
    assert nr.Add(x, y).args == (x, y)
    assert not nr.Add(x, y).is_symbol


def test_wrong_kind(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        nr.sin(x < y)
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        nr.Add(x, y, x < y)
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got str: 'a'$"):
        nr.sin("a")
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got float: 1.5$"):
        nr.Add(x, 1.5)


def test_wrong_count(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Pow takes 2 arguments, got 3$"):
        nr.Pow(x, y, z)
    with pytest.raises(TypeError, match=r"^Pow takes 2 arguments, got 1$"):
        nr.Pow(x)
    with pytest.raises(TypeError, match=r"^sin takes 1 argument, got 0$"):
        nr.sin()
    with pytest.raises(TypeError, match=r"^sin takes 1 argument, got 2$"):
        nr.sin(x, y)
    at_least = function("f", NumberKind, NumberKind, rest=NumberKind, returns=NumberKind)
    assert repr(at_least(x, y)) == "f(x, y)"
    assert repr(at_least(x, y, z, z)) == "f(x, y, z, z)"
    with pytest.raises(TypeError, match=r"^f takes at least 2 arguments, got 1$"):
        at_least(x)


def test_names(xyz):
    x, y, z = xyz
    eq = nr.Eq(x + y, z)
    assert eq.lhs == x + y
    assert eq.rhs == z
    assert nr.Eq.names == ("lhs", "rhs")
    assert nr.Add.names == ()
    assert nr.Pow(x, 2).base == x
    assert nr.Pow(x, 2).exp == nr.Integer(2)
    with pytest.raises(AttributeError, match="'Expr' object has no attribute 'middle'"):
        eq.middle
    with pytest.raises(AttributeError):
        x.lhs
    with pytest.raises(ValueError, match="f: more names than declared arguments"):
        function("f", NumberKind, returns=NumberKind, names=("a", "b"))


def test_names_cannot_hide_an_attribute():
    for taken in ("kind", "head", "args", "value", "is_symbol", "is_integer"):
        with pytest.raises(ValueError, match=f"f: an argument cannot be named '{taken}'"):
            function("f", NumberKind, returns=NumberKind, names=(taken,))
    with pytest.raises(TypeError, match="f: names must be strings, got 1"):
        function("f", NumberKind, returns=NumberKind, names=(1,))


def test_introspection():
    assert nr.Pow.name == "Pow"
    assert repr(nr.Pow) == "<function Pow>"
    assert nr.Pow.params == (NumberKind, NumberKind)
    assert nr.Pow.rest == ()
    assert nr.Add.params == ()
    assert nr.Add.rest == (NumberKind,)
    assert nr.Contains.params == (NumberKind, SetKind(NumberKind))
    assert nr.Contains.returns is BoolKind
    assert nr.Add.binds == {}


def test_rest_group(xyz):
    x, y, z = xyz
    assert nr.Piecewise.rest == (NumberKind, BoolKind)
    p = nr.Piecewise(x, x > 0, nr.Mul(-1, x), nr.true)
    assert p.kind is NumberKind
    assert repr(p) == "Piecewise(x, Gt(x, 0), Mul(-1, x), true)"
    assert p.args == (x, x > 0, nr.Mul(-1, x), nr.true)
    assert repr(nr.Piecewise(1, x < y)) == "Piecewise(1, Lt(x, y))"
    assert repr(nr.Piecewise()) == "Piecewise"


def test_rest_group_wrong_length(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Piecewise takes arguments in groups of 2, got 3$"):
        nr.Piecewise(x, x > 0, y)
    with pytest.raises(TypeError, match=r"^Piecewise takes arguments in groups of 2, got 1$"):
        nr.Piecewise(x)


def test_rest_group_wrong_kind(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Piecewise expects BoolKind, got NumberKind: y$"):
        nr.Piecewise(x, y)
    with pytest.raises(TypeError, match=r"^Piecewise expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        nr.Piecewise(x, x > 0, x < y, x < y)
    with pytest.raises(TypeError, match=r"^Piecewise expects BoolKind, got bool: True$"):
        nr.Piecewise(x, True)


def test_rest_group_after_leading_arguments(xyz):
    x, y, z = xyz
    f = function("f", SetKind(NumberKind), rest=(NumberKind, BoolKind, NumberKind), returns=NumberKind)
    s = SetKind(NumberKind)("S")
    assert repr(f(s)) == "f(S)"
    assert repr(f(s, x, x < y, 1, y, y < z, 2)) == "f(S, x, Lt(x, y), 1, y, Lt(y, z), 2)"
    with pytest.raises(TypeError, match=r"^f takes 1 argument and then arguments in groups of 3, got 3$"):
        f(s, x, x < y)
    with pytest.raises(TypeError, match=r"^f takes at least 1 argument, got 0$"):
        f()
    with pytest.raises(TypeError, match=r"^f expects NumberKind, got BoolKind"):
        f(s, x, x < y, y < z)


def test_rest_group_of_one_is_the_same_as_a_kind(xyz):
    x, y, z = xyz
    f = function("f", rest=(NumberKind,), returns=NumberKind)
    assert f.rest == (NumberKind,)
    assert repr(f(x, y, z)) == "f(x, y, z)"


def test_rest_cannot_be_empty():
    with pytest.raises(ValueError, match="f: rest cannot be an empty tuple"):
        function("f", rest=(), returns=NumberKind)


def test_undefined_function_applied(xyz):
    x, y, z = xyz
    f = function("f", NumberKind, returns=NumberKind)
    assert repr(nr.Derivative(f(x), x)) == "Derivative(f(x), x)"
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got Function: <function f>$"):
        nr.sin(f)

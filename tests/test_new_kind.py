"""A kind that the package does not have, declared in this file.

Nothing in Rust and nothing in the package knows about VectorKind. This is
what adding a kind takes.
"""

import nary as nr
import pytest
from nary import BoolKind, Expr, NumberKind, Symbol, function, kind, set_operator

VectorKind = kind("VectorKind")

VecAdd = function("VecAdd", rest=VectorKind, returns=VectorKind)
Cross = function("Cross", VectorKind, VectorKind, returns=VectorKind, names=("left", "right"))
Dot = function("Dot", VectorKind, VectorKind, returns=NumberKind)
Scale = function("Scale", NumberKind, VectorKind, returns=VectorKind)
# A linear combination: any number of (coefficient, vector) pairs.
Combination = function("Combination", rest=(NumberKind, VectorKind), returns=VectorKind)
# The directional derivative of a number along a vector symbol.
Along = function(
    "Along", NumberKind, Symbol(VectorKind), returns=NumberKind, binds={1: (0,)}
)

set_operator(VectorKind, "+", VecAdd)
set_operator(VectorKind, "*", Cross)

u, v, w = (VectorKind(name) for name in "uvw")
x, y = NumberKind("x"), NumberKind("y")


def test_symbols_of_the_new_kind():
    assert type(u) is Expr
    assert u.kind is VectorKind
    assert u.is_symbol and repr(u) == "u"
    assert repr(VectorKind) == "VectorKind"


def test_functions_of_the_new_kind():
    c = Cross(u, VecAdd(v, w))
    assert c.kind is VectorKind
    assert repr(c) == "Cross(u, VecAdd(v, w))"
    assert (c.left, c.right) == (u, VecAdd(v, w))
    d = Dot(u, c)
    assert d.kind is NumberKind
    # A number made from vectors is a number like any other.
    assert repr(nr.sin(d) + 1) == "Add(sin(Dot(u, Cross(u, VecAdd(v, w)))), 1)"
    assert repr(Scale(2, u)) == "Scale(2, u)"
    assert Cross.params == (VectorKind, VectorKind)
    assert Cross.returns is VectorKind


def test_kind_errors_against_the_other_kinds():
    with pytest.raises(TypeError, match=r"^Cross expects VectorKind, got NumberKind: x$"):
        Cross(u, x)
    with pytest.raises(TypeError, match=r"^Dot expects VectorKind, got BoolKind: Lt\(x, y\)$"):
        Dot(u, x < y)
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got VectorKind: u$"):
        nr.sin(u)
    with pytest.raises(TypeError, match=r"^Scale expects NumberKind, got VectorKind: u$"):
        Scale(u, u)
    with pytest.raises(TypeError, match=r"^Contains expects SetKind\(NumberKind\), got VectorKind: u$"):
        nr.Contains(x, u)
    # An int is a NumberKind, so it is not converted where a vector is expected.
    with pytest.raises(TypeError, match=r"^Cross expects VectorKind, got int: 0$"):
        Cross(u, 0)


def test_rest_group_with_the_new_kind():
    c = Combination(2, u, x, v)
    assert c.kind is VectorKind
    assert repr(c) == "Combination(2, u, x, v)"
    assert Combination.rest == (NumberKind, VectorKind)
    with pytest.raises(TypeError, match=r"^Combination takes arguments in groups of 2, got 3$"):
        Combination(2, u, x)
    with pytest.raises(TypeError, match=r"^Combination expects VectorKind, got NumberKind: x$"):
        Combination(2, x)
    with pytest.raises(TypeError, match=r"^Combination expects NumberKind, got VectorKind: u$"):
        Combination(u, u)


def test_symbol_slot_of_the_new_kind():
    a = Along(Dot(u, v), u)
    assert repr(a) == "Along(Dot(u, v), u)"
    assert Along.binds == {1: (0,)}
    assert repr(Along.params[1]) == "Symbol(VectorKind)"
    assert Along.params[1].kind is VectorKind
    with pytest.raises(TypeError, match=r"^Along expects a VectorKind symbol, got VectorKind: VecAdd\(u, v\)$"):
        Along(x, VecAdd(u, v))
    with pytest.raises(TypeError, match=r"^Along expects a VectorKind symbol, got NumberKind: x$"):
        Along(x, x)


def test_operators_of_the_new_kind():
    assert repr(u + v) == "VecAdd(u, v)"
    assert repr(u * v) == "Cross(u, v)"
    assert repr(u + v * w) == "VecAdd(u, Cross(v, w))"
    assert (u * v).kind is VectorKind
    # The same operators build other functions for numbers.
    assert repr(x + y) == "Add(x, y)" and repr(x * y) == "Mul(x, y)"
    with pytest.raises(TypeError, match=r"^Cross expects VectorKind, got NumberKind: x$"):
        u * x
    with pytest.raises(TypeError, match=r"^Mul expects NumberKind, got VectorKind: u$"):
        x * u
    with pytest.raises(TypeError, match=r"^Cross expects VectorKind, got int: 2$"):
        2 * u
    # Operators that were not set for the kind are not supported.
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \*\*"):
        u**v
    with pytest.raises(TypeError, match="'<' not supported between instances"):
        u < v
    with pytest.raises(ValueError, match=r"^the \+ operator is already set for VectorKind$"):
        set_operator(VectorKind, "+", VecAdd)


def test_equality_and_hash_against_the_other_kinds():
    assert VectorKind("p") == VectorKind("p")
    assert VectorKind("p") != NumberKind("p")
    assert VectorKind("p") != BoolKind("p")
    assert hash(VectorKind("p")) == hash(VectorKind("p"))
    assert hash(VectorKind("p")) != hash(NumberKind("p"))
    assert len({VectorKind("p"), NumberKind("p"), BoolKind("p"), VectorKind("p")}) == 3
    f = function("f", returns=VectorKind)
    g = function("f", returns=NumberKind)
    assert f() != g()


def test_two_kinds_with_the_same_name_are_different_kinds():
    first, second = kind("Twin"), kind("Twin")
    assert first is not second
    f = function("f", first, returns=first)
    assert f(first("t")).kind is first
    with pytest.raises(TypeError, match=r"^f expects Twin, got Twin: t$"):
        f(second("t"))
    assert first("t") != second("t")

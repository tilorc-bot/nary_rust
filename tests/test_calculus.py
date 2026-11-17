"""Symbols, Symbol(kind) positions and binds=, through nary.calculus."""

import nary
import pytest
from nary import NumberKind, Symbol, function, sin
from nary.calculus import (
    Antiderivative,
    Derivative,
    Integral,
    Limit,
    Product,
    Subs,
    Sum,
)

x, y, a, b = (NumberKind(n) for n in ("x", "y", "a", "b"))


def test_a_symbol_is_not_a_call_with_no_arguments():
    Add0 = nary.Add()
    assert x.is_symbol and not Add0.is_symbol and not sin(x).is_symbol
    assert NumberKind("Add") != Add0
    assert NumberKind("x") == x and hash(NumberKind("x")) == hash(x)
    assert "Symbol" in nary.__all__ and nary.Symbol is Symbol


def test_integral_sum_and_product_take_a_range():
    for F in (Integral, Sum, Product):
        e = F(sin(x), x, a, b)
        assert e.kind is NumberKind
        assert (e.body, e.var, e.lower, e.upper) == (sin(x), x, a, b)
    assert Integral(Integral(x, x, a, b), y, a, b).body == Integral(x, x, a, b)
    body, var, lower, upper = Integral.params
    assert body is lower is upper is NumberKind
    assert type(var) is Symbol and var.kind is NumberKind
    assert repr(var) == "Symbol(NumberKind)"


def test_derivatives_limits_and_substitutions():
    assert Derivative(sin(x), x).var == x
    assert Antiderivative(sin(x), x).body == sin(x)
    assert Limit(sin(x), x, a).point == a
    assert Subs(sin(x), x, a).value == a


def test_a_variable_must_be_a_symbol_of_the_declared_kind():
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got NumberKind: sin\(x\)$"):
        Integral(x, sin(x), a, b)
    with pytest.raises(TypeError, match=r"^Derivative expects a NumberKind symbol, got BoolKind: p$"):
        Derivative(x, nary.BoolKind("p"))


def test_binds_is_recorded():
    assert Integral.binds == {1: (0,)}
    assert Limit.binds == Subs.binds == {1: (0,)}
    assert Derivative.binds == {} and nary.Add.binds == {}


def test_an_invalid_binds_declaration_is_rejected():
    var = Symbol(NumberKind)
    with pytest.raises(ValueError, match=r"argument 0 is bound, so it must be declared as Symbol\(kind\)"):
        function("F", NumberKind, var, returns=NumberKind, binds={0: (1,)})
    with pytest.raises(ValueError, match=r"argument 1 cannot be bound in itself"):
        function("F", NumberKind, var, returns=NumberKind, binds={1: (1,)})
    with pytest.raises(ValueError, match=r"binds refers to argument 2, which is not one of the 2 declared"):
        function("F", NumberKind, var, returns=NumberKind, binds={1: (2,)})

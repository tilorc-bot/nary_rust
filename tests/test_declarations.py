"""Symbols, Symbol(kind) positions, rest groups, binds and names."""

import nary as nr
import pytest
from nary import BoolKind, NumberKind, Symbol, function, kind_family

x, y, z = (NumberKind(n) for n in "xyz")

Integral = function(
    "Integral", NumberKind, Symbol(NumberKind), NumberKind, NumberKind,
    returns=NumberKind, names=("body", "var", "lower", "upper"), binds={1: (0,)},
)
Cases = function("Cases", rest=(NumberKind, BoolKind), returns=NumberKind)


def test_a_symbol_is_not_a_call_with_no_arguments():
    symbol, call = NumberKind("Add"), nr.Add()
    assert (symbol.head, symbol.args) == (call.head, call.args) == ("Add", ())
    assert symbol.is_symbol and not call.is_symbol
    assert symbol != call and hash(symbol) != hash(call)
    assert len({symbol, call, NumberKind("Add"), nr.Add()}) == 2
    Matrix = kind_family("MatrixKind", params=1)(NumberKind)
    assert Matrix("M").is_symbol and Matrix("M") != function("M", returns=Matrix)()


def test_a_symbol_position():
    i = Integral(nr.sin(x), x, y, z)
    assert repr(i) == "Integral(sin(x), x, y, z)"
    assert i.var == x and i.var.is_symbol
    assert repr(Integral.params) == "(NumberKind, Symbol(NumberKind), NumberKind, NumberKind)"
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got NumberKind: Add\(x, y\)$"):
        Integral(x, x + y, y, z)
    c = function("c", returns=NumberKind)()      # a constant is not a symbol
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got NumberKind: c$"):
        Integral(x, c, y, z)
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got BoolKind: p$"):
        Integral(x, BoolKind("p"), y, z)


def test_the_symbol_marker():
    assert Symbol(BoolKind).kind is BoolKind
    assert repr(Symbol(BoolKind)) == "Symbol(BoolKind)"
    with pytest.raises(TypeError, match=r"^expected a kind, got 'x'$"):
        Symbol("x")


def test_a_rest_group_repeats():
    assert Cases.rest == (NumberKind, BoolKind)
    assert repr(Cases(x, x > y, y, x <= y)) == "Cases(x, Gt(x, y), y, Le(x, y))"
    assert repr(Cases()) == "Cases"
    with pytest.raises(TypeError, match=r"^Cases expects BoolKind, got NumberKind: z$"):
        Cases(x, x > y, y, z)


def test_a_rest_group_is_counted_in_whole_groups():
    with pytest.raises(TypeError, match=r"^Cases takes arguments in groups of 2, got 3$"):
        Cases(x, x > y, y)
    f = function("f", NumberKind, rest=(NumberKind, BoolKind), returns=NumberKind)
    assert f(x, y, x < y).args == (x, y, x < y)
    with pytest.raises(TypeError, match=r"^f takes 1 argument and then arguments in groups of 2, got 2$"):
        f(x, y)
    with pytest.raises(ValueError, match=r"^f: rest cannot be an empty tuple$"):
        function("f", rest=(), returns=NumberKind)


def test_binds_is_recorded():
    assert Integral.binds == {1: (0,)}
    assert nr.Add.binds == {}
    # Nothing reads it yet: the name of a bound variable still matters.
    assert Integral(x, x, y, z) != Integral(y, y, y, z)


def test_binds_is_checked():
    var = Symbol(NumberKind)
    for binds, error, message in [
        ({0: (1,)}, ValueError, r"argument 0 is bound, so it must be declared as Symbol\(kind\)"),
        ({2: (0,)}, ValueError, "binds refers to argument 2, which is not one of the 2 declared"),
        ({1: (1,)}, ValueError, "argument 1 cannot be bound in itself"),
        ({1: 0}, TypeError, "binds maps a position to a tuple of positions, got 0"),
    ]:
        with pytest.raises(error, match=f"^f: {message}$"):
            function("f", NumberKind, var, returns=NumberKind, binds=binds)


def test_names_cannot_hide_an_attribute():
    for taken in ("kind", "head", "args", "is_symbol"):
        with pytest.raises(ValueError, match=f"^f: an argument cannot be named '{taken}', which every expression already has$"):
            function("f", NumberKind, returns=NumberKind, names=(taken,))

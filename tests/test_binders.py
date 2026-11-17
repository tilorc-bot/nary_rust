"""Symbol positions and bound variables."""

import nary as nr
import pytest
from nary import BoolKind, MatrixKind, NumberKind, Symbol, function


def test_symbol_marker():
    marker = Symbol(NumberKind)
    assert repr(marker) == "Symbol(NumberKind)"
    assert marker.kind is NumberKind
    # Any kind, including one made by a family.
    assert Symbol(MatrixKind(NumberKind)).kind is MatrixKind(NumberKind)
    assert repr(Symbol(MatrixKind(BoolKind))) == "Symbol(MatrixKind(BoolKind))"


def test_symbol_marker_is_not_a_way_to_make_a_symbol():
    with pytest.raises(TypeError, match=r"to make a symbol call the kind, as in NumberKind\('x'\)"):
        Symbol("x")
    with pytest.raises(TypeError, match="^expected a kind, got <class 'int'>$"):
        Symbol(int)
    with pytest.raises(TypeError, match="^expected a kind, got <kind family MatrixKind>$"):
        Symbol(MatrixKind)
    with pytest.raises(TypeError, match="a signature is made of kinds"):
        function("f", Symbol, returns=NumberKind)


def test_integral(xyz):
    x, y, z = xyz
    i = nr.Integral(nr.sin(x), x, 0, 1)
    assert i.kind is NumberKind
    assert repr(i) == "Integral(sin(x), x, 0, 1)"
    assert (i.body, i.var, i.lower, i.upper) == (nr.sin(x), x, nr.Integer(0), nr.Integer(1))
    assert repr(nr.Integral(x * y, x, y, z)) == "Integral(Mul(x, y), x, y, z)"


def test_multiple_integral_by_nesting(xyz):
    x, y, z = xyz
    i = nr.Integral(nr.Integral(x * y, x, 0, 1), y, 0, 2)
    assert repr(i) == "Integral(Integral(Mul(x, y), x, 0, 1), y, 0, 2)"
    assert i.var == y and i.body.var == x


def test_non_symbol_in_a_symbol_position(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got NumberKind: Add\(x, y\)$"):
        nr.Integral(x, x + y, 0, 1)
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got NumberKind: pi$"):
        nr.Integral(x, nr.pi, 0, 1)
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got NumberKind: 1$"):
        nr.Integral(x, nr.Integer(1), 0, 1)
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got int: 1$"):
        nr.Integral(x, 1, 0, 1)
    with pytest.raises(TypeError, match=r"^Integral expects a NumberKind symbol, got BoolKind: p$"):
        nr.Integral(x, BoolKind("p"), 0, 1)
    with pytest.raises(TypeError, match=r"^Derivative expects a NumberKind symbol, got NumberKind: sin\(x\)$"):
        nr.Derivative(x, nr.sin(x))


def test_integral_counts_and_kinds(xyz):
    x, y, z = xyz
    with pytest.raises(TypeError, match=r"^Integral takes 4 arguments, got 2$"):
        nr.Integral(x, x)
    with pytest.raises(TypeError, match=r"^Integral expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        nr.Integral(x < y, x, 0, 1)
    with pytest.raises(TypeError, match=r"^Antiderivative takes 2 arguments, got 4$"):
        nr.Antiderivative(x, x, 0, 1)


def test_binds_are_recorded():
    for f in (nr.Integral, nr.Sum, nr.Product):
        assert f.binds == {1: (0,)}
        assert f.names == ("body", "var", "lower", "upper")
        assert f.params[0] is NumberKind
        assert repr(f.params[1]) == "Symbol(NumberKind)"
        assert f.params[2:] == (NumberKind, NumberKind)
    assert nr.Limit.binds == {1: (0,)}
    assert nr.Subs.binds == {1: (0,)}


def test_variable_of_a_derivative_is_not_bound(xyz):
    x, y, z = xyz
    assert nr.Derivative.binds == {}
    assert nr.Antiderivative.binds == {}
    d = nr.Derivative(nr.sin(x), x)
    assert repr(d) == "Derivative(sin(x), x)"
    assert (d.expr, d.var) == (nr.sin(x), x)
    a = nr.Antiderivative(nr.sin(x), x)
    assert repr(a) == "Antiderivative(sin(x), x)"
    assert (a.body, a.var) == (nr.sin(x), x)


def test_sum_product_limit_subs(xyz):
    x, y, z = xyz
    n, k = NumberKind("n"), NumberKind("k")
    assert repr(nr.Sum(k**2, k, 1, n)) == "Sum(Pow(k, 2), k, 1, n)"
    assert repr(nr.Product(k, k, 1, n)) == "Product(k, k, 1, n)"
    assert repr(nr.Limit(nr.sin(x), x, 0)) == "Limit(sin(x), x, 0)"
    s = nr.Subs(nr.Derivative(nr.sin(x), x), x, 0)
    assert repr(s) == "Subs(Derivative(sin(x), x), x, 0)"
    assert (s.var, s.point) == (x, nr.Integer(0))
    with pytest.raises(TypeError, match=r"^Sum expects a NumberKind symbol, got NumberKind: Add\(k, 1\)$"):
        nr.Sum(k, k + 1, 1, n)


def test_binds_do_not_change_what_is_built(xyz):
    x, y, z = xyz
    # Nothing renames bound variables: these differ only in the name of the
    # variable and are not equal.
    assert nr.Integral(x, x, 0, 1) != nr.Integral(y, y, 0, 1)
    assert nr.Integral(x, x, 0, 1) == nr.Integral(x, x, 0, 1)


def test_symbol_of_another_kind():
    Matrix = MatrixKind(NumberKind)
    f = function("f", Matrix, Symbol(Matrix), returns=Matrix, binds={1: (0,)})
    a, x = Matrix("A"), NumberKind("x")
    assert repr(f(a, a)) == "f(A, A)"
    assert f(a, MatrixKind(NumberKind)("B")).args[1].is_symbol
    with pytest.raises(TypeError, match=r"^f expects a MatrixKind\(NumberKind\) symbol, got MatrixKind\(NumberKind\): Transpose\(A\)$"):
        f(a, nr.Transpose(a))
    with pytest.raises(TypeError, match=r"^f expects a MatrixKind\(NumberKind\) symbol, got NumberKind: x$"):
        f(a, x)
    with pytest.raises(TypeError, match=r"^f expects a MatrixKind\(NumberKind\) symbol, got MatrixKind\(BoolKind\): P$"):
        f(a, MatrixKind(BoolKind)("P"))


def test_binds_validation():
    var = Symbol(NumberKind)
    with pytest.raises(ValueError, match=r"f: argument 0 is bound, so it must be declared as Symbol\(kind\)"):
        function("f", NumberKind, var, returns=NumberKind, binds={0: (1,)})
    with pytest.raises(ValueError, match="f: binds refers to argument 2, which is not one of the 2 declared"):
        function("f", NumberKind, var, returns=NumberKind, binds={2: (0,)})
    with pytest.raises(ValueError, match="f: binds refers to argument 5, which is not one of the 2 declared"):
        function("f", NumberKind, var, returns=NumberKind, binds={1: (5,)})
    with pytest.raises(ValueError, match="f: binds refers to argument -1"):
        function("f", NumberKind, var, returns=NumberKind, binds={1: (-1,)})
    with pytest.raises(ValueError, match="f: argument 1 cannot be bound in itself"):
        function("f", NumberKind, var, returns=NumberKind, binds={1: (1,)})
    with pytest.raises(TypeError, match="f: binds maps a position to a tuple of positions, got 0"):
        function("f", NumberKind, var, returns=NumberKind, binds={1: 0})
    with pytest.raises(TypeError):
        function("f", NumberKind, var, returns=NumberKind, binds=[(1, (0,))])


def test_several_bound_variables():
    var = Symbol(NumberKind)
    f = function(
        "f", NumberKind, var, var, NumberKind,
        returns=NumberKind, binds={1: (0,), 2: (0, 3)},
    )
    assert f.binds == {1: (0,), 2: (0, 3)}

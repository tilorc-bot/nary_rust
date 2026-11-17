"""The package layout, the kinds it declares, and its operators."""

import importlib

import nary as nr
import pytest
from nary import BoolKind, NumberKind

x, y, z = (NumberKind(n) for n in "xyz")


def test_the_package_wraps_a_private_compiled_module():
    core = importlib.import_module("nary._core")
    assert nr.Expr is core.Expr and nr.function is core.function
    assert nr.Expr.__module__ == nr.Kind.__module__ == "nary"
    for name in nr.__all__:
        assert hasattr(nr, name), name


def test_bool_is_named_bool_kind():
    assert BoolKind.name == repr(BoolKind) == "BoolKind"
    assert (x < y).kind is BoolKind
    assert not hasattr(nr, "Bool")


def test_pow_and_the_comparisons():
    for expr, text, kind in [
        (x**y, "Pow(x, y)", NumberKind),
        (x + y * z**y, "Add(x, Mul(y, Pow(z, y)))", NumberKind),
        (x > y, "Gt(x, y)", BoolKind),
        (x <= y, "Le(x, y)", BoolKind),
        (x >= y, "Ge(x, y)", BoolKind),
    ]:
        assert repr(expr) == text
        assert expr.kind is kind
    assert (x**y).base == x and (x > y) == nr.Gt(x, y)
    p, q = BoolKind("p"), BoolKind("q")
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \*\*"):
        p**q
    with pytest.raises(TypeError, match="'>=' not supported between instances"):
        p >= q


def test_operator_errors():
    with pytest.raises(TypeError, match=r"^Pow expects NumberKind, got int: 2$"):
        x**2
    with pytest.raises(TypeError, match=r"^Gt expects NumberKind, got BoolKind: Lt\(x, y\)$"):
        x > (x < y)
    with pytest.raises(TypeError, match="^pow\\(\\) with a modulus is not supported$"):
        pow(x, y, z)

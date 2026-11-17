import pytest

import nary as nr

x, y, z = (nr.NumberKind(n) for n in "xyz")
p, q = nr.BoolKind("p"), nr.BoolKind("q")


def test_new_operators_build_their_functions():
    assert x ** y == nr.Pow(x, y)
    assert (x > y) == nr.Gt(x, y)
    assert (x <= y) == nr.Le(x, y)
    assert (x >= y) == nr.Ge(x, y)
    assert (x > y).kind is nr.BoolKind


def test_a_kind_without_the_operators_does_not_support_them():
    with pytest.raises(TypeError):
        p ** q
    with pytest.raises(TypeError, match="'>=' not supported between instances"):
        p >= q


def test_pow_with_a_modulus_is_a_type_error():
    with pytest.raises(TypeError, match="modulus"):
        pow(x, y, z)

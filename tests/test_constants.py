import pytest
from nary import BoolKind, Lambda, NumberKind, declare_constant, pi, sin
from nary.logic import And, true

x = NumberKind("x")


def test_a_constant_is_a_leaf_with_a_name_and_a_kind():
    assert pi.kind is NumberKind and pi.name == "pi" and repr(pi) == "pi"
    assert pi.head is None and pi.args == () and pi.params is None
    assert true.kind is BoolKind and true.head is None and true.name == "true"


def test_a_constant_is_equal_only_to_itself():
    assert pi == pi and hash(pi) == hash(pi)
    assert pi != declare_constant("pi", NumberKind)
    assert pi != NumberKind("pi")


def test_a_constant_is_accepted_where_its_kind_is_expected():
    assert repr(sin(pi)) == "sin(pi)"
    assert repr(2 * pi) == "Mul(2, pi)"
    assert repr(And(x < pi, true)) == "And(Lt(x, pi), true)"
    with pytest.raises(TypeError, match=r"^pi is of kind NumberKind, which is not a function kind"):
        pi(x)


def test_a_constant_cannot_be_bound_by_lambda():
    with pytest.raises(TypeError, match=r"^Lambda expects a NumberKind symbol, got NumberKind: pi$"):
        Lambda(pi, x)


def test_is_constant_tells_the_leaf_forms_apart():
    literal = NumberKind(3)
    assert [e.is_constant for e in (pi, sin, x, literal)] == [True, True, False, False]
    assert [e.is_symbol for e in (pi, sin, x, literal)] == [False, False, True, False]
    assert [e.is_literal for e in (pi, sin, x, literal)] == [False, False, False, True]

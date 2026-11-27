import pytest

from nary import Add, Many, Mul, NumberKind, Pow, declare_function, exp, log
from nary.arithmetic_rules import rules
from nary.logic import true
from nary.properties import declare_properties, declare_property, properties, property_rules
from nary.relational import Ne
from nary.rules import is_flat, is_unordered, rule

a = NumberKind("a")


def test_the_rules_are_those_before_properties():
    before = [
        rule(a + 0, a, name="add_identity"),
        rule(a + a, 2 * a, name="add_self"),
        rule(a - a, 0, name="add_inverse"),
        rule(a * 1, a, name="mul_identity"),
        rule(a * 0, 0, name="mul_absorbing"),
        rule(a / a, 1, when=Ne(a, 0), name="mul_inverse"),
        rule(a ** 1, a, name="pow_one"),
        rule(a ** 0, 1, when=Ne(a, 0), name="pow_zero"),
        rule(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
    ]
    assert [repr(r) for r in rules] == [repr(r) for r in before]
    assert [r.erased for r in rules] == [r.erased for r in before]


def test_attribute_access():
    add, mul, pow_ = properties(Add), properties(Mul), properties(Pow)
    assert add.associative and add.commutative and mul.associative and mul.commutative
    assert add.identity == NumberKind(0) and add.absorbing is None
    assert mul.identity == NumberKind(1) and mul.absorbing == NumberKind(0)
    assert mul.identity.kind is NumberKind
    assert pow_.associative is False and pow_.commutative is False and pow_.identity is None
    assert repr(pow_) == "Properties()"
    assert all(is_flat(f) and is_unordered(f) for f in (Add, Mul))
    with pytest.raises(AttributeError, match="identiy is not a property"):
        mul.identiy
    with pytest.raises(AttributeError, match="cannot be changed"):
        mul.identity = 2


def test_refusals_record_nothing():
    P = declare_function("P", NumberKind, NumberKind, returns=NumberKind, domain=true)
    with pytest.raises(ValueError, match="properties of Add are already declared"):
        declare_properties(Add, absorbing=0)
    with pytest.raises(TypeError, match="asociative is not a property"):
        declare_properties(P, commutative=True, asociative=True)
    with pytest.raises(TypeError, match="P expects NumberKind, got BoolKind: true"):
        declare_properties(P, commutative=True, identity=true)
    assert properties(Add).absorbing is None
    assert repr(properties(P)) == "Properties()" and not is_unordered(P)
    declare_properties(P, commutative=True, identity=0)
    assert [repr(r) for r in property_rules(P)] == ["Rule(P(a, 0), a, name='p_identity')"]


def test_a_new_property_and_a_function_with_it():
    declare_property("torsion", default=1)
    declare_property("pivot", element=True)
    T = declare_function("T", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(T, associative=True, commutative=True, torsion=3, pivot=3)
    assert properties(T).torsion == 3 and type(properties(T).torsion) is int
    assert properties(T).pivot == NumberKind(3) and properties(T).pivot.kind is NumberKind
    assert properties(Add).torsion == 1 and properties(Add).pivot is None
    assert is_flat(T) and is_unordered(T) and property_rules(T) == []
    with pytest.raises(ValueError, match="torsion is already a property"):
        declare_property("torsion")

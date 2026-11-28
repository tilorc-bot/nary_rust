import subprocess
import sys

import pytest

from nary import Add, Lambda, Many, Mul, NumberKind, Pow, declare_function, exp, log, pi
from nary.arithmetic_rules import rules
from nary.calculus import Derivative, NumberFunction
from nary.logic import true
from nary.properties import (
    declare_properties,
    declare_property,
    declared_properties,
    property_rules,
)
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
    assert Add.is_associative is True and Add.is_commutative is True
    assert Mul.is_associative is True and Mul.is_commutative is True
    assert Add.identity_element == NumberKind(0) and Add.absorbing_element is None
    assert Mul.identity_element == NumberKind(1) and Mul.absorbing_element == NumberKind(0)
    assert Mul.identity_element.kind is NumberKind
    assert Pow.is_associative is False and Pow.is_commutative is False
    assert Pow.identity_element is None and Pow.absorbing_element is None
    assert all(is_flat(f) and is_unordered(f) for f in (Add, Mul))
    with pytest.raises(AttributeError, match="'Expr' object has no attribute 'is_asociative'"):
        Mul.is_asociative


def test_only_a_declared_function_has_properties():
    x = NumberKind("x")
    for e in (x, NumberKind(1), pi, Pow(x, 2), Add(x, 1)):
        with pytest.raises(AttributeError, match="no attribute 'identity_element'"):
            e.identity_element
        with pytest.raises(AttributeError, match="no attribute 'is_associative'"):
            e.is_associative


def test_argument_names_still_resolve():
    x = NumberKind("x")
    assert Pow(x, 2).base == x and Pow(x, 2).exp == NumberKind(2)
    assert Add(x, 1).terms == (x, NumberKind(1)) and Mul().factors == ()
    with pytest.raises(AttributeError, match="no attribute 'terms'"):
        Pow(x, 2).terms


def test_every_function_has_the_defaults():
    x = NumberKind("x")
    f = NumberFunction("f")
    for F in (f, Lambda(x, x * x), Derivative(f)):
        assert F.is_associative is False and F.is_commutative is False
        assert F.identity_element is None and F.absorbing_element is None
        with pytest.raises(AttributeError, match="'Expr' object has no attribute 'is_asociative'"):
            F.is_asociative
    assert Derivative(f).function == f
    for e in (x, NumberKind(1), x + NumberKind("y"), f(x)):
        with pytest.raises(AttributeError, match="no attribute 'is_commutative'"):
            e.is_commutative


def test_import_nary_alone_declares_add_and_mul():
    code = (
        "import sys, nary\n"
        "from nary.rules import is_flat, is_unordered\n"
        "assert 'nary.arithmetic_rules' not in sys.modules\n"
        "assert nary.Mul.is_associative is True\n"
        "zero = nary.Add.identity_element\n"
        "assert zero == nary.NumberKind(0) and zero.kind is nary.NumberKind\n"
        "assert all(is_flat(F) and is_unordered(F) for F in (nary.Add, nary.Mul))\n"
        "assert not is_flat(nary.Pow) and not is_unordered(nary.Pow)\n"
        "import nary.arithmetic_rules\n"
        "assert len(nary.arithmetic_rules.rules) == 9\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_declared_properties():
    assert declared_properties(Mul) == {
        "is_associative": True, "is_commutative": True,
        "identity_element": NumberKind(1), "absorbing_element": NumberKind(0),
    }
    assert declared_properties(Pow) == {} and declared_properties(NumberFunction("f")) == {}
    declared_properties(Mul).clear()
    assert len(declared_properties(Mul)) == 4 and Mul.identity_element == NumberKind(1)
    for e in (NumberKind("x"), NumberKind(1), Add(NumberKind("x"), 1), 1):
        with pytest.raises(TypeError, match="declared_properties expects a function"):
            declared_properties(e)


def test_refusals_record_nothing():
    P = declare_function("P", NumberKind, NumberKind, returns=NumberKind, domain=true)
    with pytest.raises(ValueError, match="properties of Add are already declared"):
        declare_properties(Add, absorbing_element=0)
    with pytest.raises(TypeError, match="is_asociative is not a property"):
        declare_properties(P, is_commutative=True, is_asociative=True)
    with pytest.raises(TypeError, match="P expects NumberKind, got BoolKind: true"):
        declare_properties(P, is_commutative=True, identity_element=true)
    with pytest.raises(TypeError, match="is_commutative must be True or False, got 1"):
        declare_properties(P, identity_element=0, is_commutative=1)
    for name in ("name", "kind", "args", "is_atom"):
        with pytest.raises(ValueError, match=f"{name} is already an attribute of Expr"):
            declare_property(name)
        with pytest.raises(TypeError, match=f"{name} is not a property"):
            declare_properties(P, **{name: 0})
    assert Add.absorbing_element is None
    assert P.is_commutative is False and P.identity_element is None and not is_unordered(P)
    declare_properties(P, is_commutative=True, identity_element=0)
    assert P.is_commutative is True and P.identity_element == NumberKind(0)
    assert [repr(r) for r in property_rules(P)] == ["Rule(P(a, 0), a, name='p_identity')"]


def test_a_new_property_and_a_function_with_it():
    declare_property("torsion")
    declare_property("pivot_element", element=True)
    T = declare_function("T", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(T, is_associative=True, is_idempotent=True, torsion=3, pivot_element=3)
    assert T.is_idempotent is True and T.torsion == 3 and type(T.torsion) is int
    assert T.pivot_element == NumberKind(3) and T.pivot_element.kind is NumberKind
    assert T.is_commutative is False and T.identity_element is None
    assert Add.is_idempotent is False and Add.torsion is None and Add.pivot_element is None
    assert is_flat(T) and not is_unordered(T)
    assert [repr(r) for r in property_rules(T)] == ["Rule(T(a, a), a, name='t_idempotent')"]
    with pytest.raises(ValueError, match="torsion is already a property"):
        declare_property("torsion")

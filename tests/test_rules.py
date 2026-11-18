"""Rules and the facts unordered and flat, from nary.rules."""

import doctest

import nary.arithmetic_rules
import nary.rules
import pytest
from nary import Add, BoolKind, Lambda, Mul, Ne, NumberKind, Pow, declare_function
from nary.logic import And, true
from nary.rules import flat, is_flat, is_unordered, rule, unordered

a, b = NumberKind("a"), NumberKind("b")


def test_docstring_examples():
    for module in (nary.rules, nary.arithmetic_rules):
        result = doctest.testmod(module)
        assert result.attempted > 0
        assert result.failed == 0


def test_stored_fields():
    r = rule(a * b / b, a, when=Ne(b, 0), name="example")
    assert (r.pattern, r.replacement, r.condition, r.name) == (
        Mul(Mul(a, b), Pow(b, -1)), a, Ne(b, 0), "example"
    )
    assert r.variables == (a, b) and r.erased == (b,)
    assert repr(r) == "Rule(Mul(Mul(a, b), Pow(b, -1)), a, when=Ne(b, 0), name='example')"


def test_arithmetic_rules():
    [mul_zero] = [r for r in nary.arithmetic_rules.rules if r.pattern == a * 0]
    assert mul_zero.replacement == NumberKind(0)
    assert mul_zero.condition is None
    assert mul_zero.erased == (a,)
    assert is_unordered(Add) and is_flat(Add) and is_unordered(Mul) and is_flat(Mul)
    assert not is_unordered(Pow) and not is_flat(Pow)


def test_rule_on_booleans():
    p = BoolKind("p")
    r = rule(And(p, true), p)
    assert r.replacement.kind is BoolKind and r.variables == (p,)


def test_refusals():
    with pytest.raises(ValueError, match="cannot be a bare symbol"):
        rule(a, a + 0)
    with pytest.raises(TypeError, match="pattern's kind NumberKind, got BoolKind"):
        rule(a + 0, a < b)
    with pytest.raises(ValueError, match="b is in the condition only"):
        rule(a + 0, a, when=Ne(b, 0))
    with pytest.raises(TypeError, match="must be a BoolKind expression, got True"):
        rule(a + 0, a, when=True)
    with pytest.raises(ValueError, match="two symbols named a of different kinds"):
        rule(Ne(a, 0), BoolKind("a"))
    with pytest.raises(ValueError, match="cannot contain a Lambda yet"):
        rule(Lambda(b, b)(a), a)
    with pytest.raises(ValueError, match="already recorded as unordered"):
        unordered(Add)
    with pytest.raises(ValueError, match="arguments all have one kind"):
        unordered(declare_function("Pair", NumberKind, BoolKind, returns=NumberKind))
    with pytest.raises(ValueError, match="flat needs a function taking any number"):
        flat(Pow)
    with pytest.raises(TypeError, match="expects a declared function, got a"):
        is_flat(a)

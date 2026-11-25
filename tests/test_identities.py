"""The blocks in nary.arithmetic_rules give the rules and facts of main."""

import doctest

import pytest

import nary.identities
from nary import Add, Mul, NumberKind, exp, log
from nary._core import declare_function
from nary.arithmetic_rules import rules
from nary.identities import Equal, declare_identities, identities, identity, inverse
from nary.relational import Ne
from nary.rules import is_flat, is_unordered, rule

a = NumberKind("a")


def test_doctests():
    assert doctest.testmod(nary.identities).failed == 0


def test_the_rules_are_those_listed_before_the_blocks():
    before = [
        rule(a + 0, a, name="add_zero"),
        rule(a * 1, a, name="mul_one"),
        rule(a * 0, 0, name="mul_zero"),
        rule(a + a, 2 * a, name="add_self"),
        rule(a - a, 0, name="sub_self"),
        rule(a / a, 1, when=Ne(a, 0), name="div_self"),
        rule(a ** 1, a, name="pow_one"),
        rule(a ** 0, 1, when=Ne(a, 0), name="pow_zero"),
        rule(exp(log(a)), a, when=Ne(a, 0), name="exp_log"),
    ]
    by_name = {r.name: r for r in rules}
    assert len(by_name) == len(rules) == len(before)
    for r in before:
        assert repr(by_name[r.name]) == repr(r)
        assert by_name[r.name].erased == r.erased


def test_the_facts():
    assert all(is_flat(f) and is_unordered(f) for f in (Add, Mul))


def test_one_block_per_function():
    with pytest.raises(ValueError, match="already declared"):
        declare_identities(Add, [])
    assert repr(identities(Add)[-1]) == "inverse(Mul(-1, a))"


def test_refused_blocks_record_nothing():
    P = declare_function("P", NumberKind, NumberKind, returns=NumberKind)
    with pytest.raises(ValueError, match="needs an identity"):
        declare_identities(P, [inverse(a, name="p_inverse")])
    with pytest.raises(ValueError, match="needs a name="):
        declare_identities(P, [identity(0)])
    with pytest.raises(ValueError, match="needs a name="):
        declare_identities(P, [Equal(P(a, 0), a)])
    assert identities(P) == []

import pytest

from nary import Add, Mul, NumberKind, exp, log
from nary._core import declare_function
from nary._identities import Equal, declare_identities, identities, identity, inverse
from nary.arithmetic_rules import rules
from nary.relational import Ne
from nary.rules import is_flat, is_unordered, rule

a = NumberKind("a")


def test_the_rules_are_those_listed_before_the_blocks():
    before = [
        rule(a + 0, a, name="add_identity"),
        rule(a * 1, a, name="mul_identity"),
        rule(a * 0, 0, name="mul_absorbing"),
        rule(a + a, 2 * a, name="add_self"),
        rule(a - a, 0, name="add_inverse"),
        rule(a / a, 1, when=Ne(a, 0), name="mul_inverse"),
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
    with pytest.raises(ValueError, match="same name"):
        declare_identities(P, [identity(0), identity(1)])
    with pytest.raises(ValueError, match="same name"):
        declare_identities(P, [identity(0), Equal(P(a, 1), a, name="p_identity")])
    with pytest.raises(ValueError, match="needs a name="):
        declare_identities(P, [Equal(P(a, 0), a)])
    assert identities(P) == []


def test_generated_names_and_override():
    Q = declare_function("Q", NumberKind, NumberKind, returns=NumberKind)
    made = declare_identities(Q, [identity(0), inverse(Q(a, a), name="q_self")])
    assert [r.name for r in made] == ["q_identity", "q_self"]

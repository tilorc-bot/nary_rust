"""Placeholders, generic identities and the blocks of nary.identities, and
the rules the blocks give nary.rewriting."""

import doctest

import nary
import nary.identities
import pytest
from nary import (
    Add,
    BoolKind,
    Lt,
    Mul,
    Ne,
    NumberKind,
    Pow,
    exp,
    log,
    sin,
)
from nary._core import declare_function
from nary.arithmetic_rules import rules
from nary.identities import (
    Equal,
    IdentityKind,
    PatternKind,
    absorbing,
    associative,
    commutative,
    declare_identities,
    declare_identity,
    distributive,
    f as f_,
    idempotent,
    identities,
    identity,
    inverse,
    lists,
    repeated,
    singleton,
)
from nary.lean import to_lean_identity
from nary.logic import And, Or, false, true
from nary.rewriting import rewrite
from nary.rules import identity_rules, is_flat, is_unordered, specific_rule, unordered

x, y = NumberKind("x"), NumberKind("y")
a_, b_, s__ = PatternKind("a_"), PatternKind("b_"), PatternKind("s__")


def test_docstring_examples():
    result = doctest.testmod(nary.identities)
    assert result.attempted > 0 and result.failed == 0


# Placeholders and the kinds of nary.identities.

def test_placeholders_are_symbols_of_an_ordinary_kind():
    # PatternKind and IdentityKind are kinds declared in Python, not part of
    # the core, and not exported from nary.
    assert not hasattr(nary, "PatternKind") and not hasattr(nary, "IdentityKind")
    assert PatternKind is not IdentityKind
    assert a_.is_symbol and a_.kind is PatternKind and repr(a_) == "a_"
    assert repr(f_(s__, a_)) == "f_(s__, a_)" and f_(s__, a_).kind is PatternKind
    # The core accepts a PatternKind expression only at a PatternKind
    # position, so one never ends up inside an expression of another kind.
    with pytest.raises(TypeError):
        Add(a_, x)
    with pytest.raises(TypeError):
        f_(x)


def test_multi_argument_placeholders_follow_the_convention():
    # A placeholder whose name ends in two underscores stands for a run of
    # arguments; it fits only a position that takes any number of them.
    first = declare_identity("first", f_(a_, s__), a_)
    assert [m.name for m in first.multi] == ["s__"]
    Q = declare_function("Q5", NumberKind, NumberKind, returns=NumberKind)
    with pytest.raises(TypeError, match="multi-argument placeholder s__ at position 1"):
        declare_identities(Q, [first])
    R = declare_function("R5", NumberKind, rest=NumberKind, returns=NumberKind)
    declare_identities(R, [first])
    assert repr(identities(R)[0].lhs) == "R5(a_, s__)"


def test_symbols_in_specific_identities_are_placeholders():
    F = declare_function("S3", NumberKind, returns=NumberKind)
    declare_identities(F, [Equal(F(x), 0, name="s3_zero"), Equal(F(F(NumberKind("a_"))), 0)])
    zero, twice = identities(F)
    # Without name=, the name is derived from the left side.
    assert (zero.name, twice.name) == ("s3_zero", "s3_s3_a")
    assert (zero.lhs, zero.rhs, zero.item.kind) == (F(x), NumberKind(0), IdentityKind)
    # As a rule, a placeholder loses the trailing underscores of the
    # convention; a plain name is kept.
    a = NumberKind("a")
    assert specific_rule(zero).pattern == F(x)
    assert specific_rule(twice).pattern == F(F(a))
    with pytest.raises(TypeError):
        Equal(1, 2)


# Generic identities.

def test_generic_identity_records():
    assert associative.name == "associative" and associative.params == ()
    assert associative.normal is None and [m.name for m in associative.multi] == ["s__", "t__", "u__"]
    assert repr(associative.definition) == "Equal(f_(s__, f_(t__), u__), f_(s__, t__, u__))"
    assert associative.definition.kind is IdentityKind
    assert commutative.normal == "Sorted"
    assert [p.name for p in identity.params] == ["e_"]
    assert [p.name for p in distributive.params] == ["g_"]
    assert singleton.multi == () and distributive.multi == ()
    # Called with its parameter, a generic identity is waiting for the
    # function, whose kind gives the parameter's kind.
    assert repr(identity(0)) == "identity(0)" and repr(identity(true)) == "identity(true)"
    with pytest.raises(TypeError, match="takes no parameters"):
        associative()
    with pytest.raises(TypeError, match="takes 1 parameter"):
        identity()
    assert repr(associative) == "associative"


def test_listed_items_are_expressions_of_identity_kind():
    add_identity = identities(Add)[3]
    mul_identity, mul_absorbing = identities(Mul)[3:5]
    and_identity = identities(And)[4]
    assert repr(add_identity.item) == "identity(0)" and add_identity.item.kind is IdentityKind
    assert add_identity.item.e == NumberKind(0)
    # One version of identity for each combination of kinds, declared once.
    assert add_identity.item.head is mul_identity.item.head
    assert add_identity.item.head is not and_identity.item.head
    assert and_identity.item.head.kind.inputs == (BoolKind,)
    assert mul_absorbing.item.head is not mul_identity.item.head
    assert identities(Add)[0].item.kind is IdentityKind and repr(identities(Add)[0].item) == "associative"


def test_declare_identity_refusals():
    with pytest.raises(ValueError, match="function placeholder"):
        declare_identity("bad1", f_(a_).args[0], a_)
    with pytest.raises(TypeError, match="PatternKind"):
        declare_identity("bad1b", x + 1, x)
    with pytest.raises(ValueError, match="must be in its left side"):
        declare_identity("bad2", f_(a_), b_)
    with pytest.raises(ValueError, match="parameter"):
        declare_identity("bad3", f_(a_), a_, params=(b_,))
    with pytest.raises(ValueError, match="parameter"):
        declare_identity("bad4", f_(s__, a_), a_, params=(s__,))
    with pytest.raises(ValueError, match="identifier"):
        declare_identity("not a name", f_(a_), a_)


def test_a_generic_identity_with_parameters_must_be_called():
    F = declare_function("F6", rest=NumberKind, returns=NumberKind)
    with pytest.raises(TypeError, match=r"identity cannot be listed for F6: .*identity\(\.\.\.\)"):
        declare_identities(F, [identity])
    with pytest.raises(TypeError, match="not an expression"):
        declare_identities(F, [identity("x")])


# Blocks.

def test_identities_of_a_function():
    names = {F: [i.name for i in identities(F)] for F in (Add, Mul, Pow, exp, sin, And, Or)}
    # singleton is added after associative; it is not written in the blocks.
    assert names[Add] == ["add_associative", "add_singleton", "add_commutative",
                          "add_identity", "add_inverse", "add_repeated"]
    assert names[Mul] == ["mul_associative", "mul_singleton", "mul_commutative",
                          "mul_identity", "mul_absorbing", "mul_inverse", "mul_repeated",
                          "mul_distributive"]
    assert names[Pow] == ["pow_one", "pow_zero"]
    assert names[exp] == ["exp_log"]
    assert names[sin] == ["sin_0", "sin_mul_neg1_a", "sin_add_a_mul_2_pi"]
    assert names[And] == ["and_associative", "and_singleton", "and_commutative",
                          "and_idempotent", "and_identity", "and_absorbing"]
    assert names[Or] == ["or_associative", "or_singleton", "or_commutative",
                         "or_idempotent", "or_identity", "or_absorbing"]


def test_instances_are_filled_and_typed():
    by_name = {i.name: i for i in identities(Mul)}
    i = by_name["mul_absorbing"]
    assert (repr(i.item), i.generic, i.function) == ("absorbing(0)", absorbing, Mul)
    assert repr(i.lhs) == "Mul(s__, 0, t__)" and i.rhs == NumberKind(0) and i.when is None
    assert i.lhs.kind is NumberKind
    d = by_name["mul_distributive"]
    assert repr(d.lhs) == "Mul(a_, Add(b_, c_))"
    assert repr(d.rhs) == "Add(Mul(a_, b_), Mul(a_, c_))"
    a = NumberKind("a_")
    # The a in the parameter of inverse and repeated is the identity's a;
    # the element of inverse comes from the identity(1) of the block.
    s = by_name["mul_inverse"]
    assert (s.generic, s.lhs, s.rhs, s.when) == (inverse, a / a, NumberKind(1), Ne(a, 0))
    assert repr(s.item) == "inverse(Pow(a_, -1))"
    r = by_name["mul_repeated"]
    assert (r.generic, r.lhs, r.rhs, r.when) == (repeated, a * a, a ** 2, None)
    add_inverse = identities(Add)[4]
    assert (add_inverse.lhs, add_inverse.rhs) == (a - a, NumberKind(0))
    assert repr(identities(And)[5].lhs) == "And(s__, false, t__)"
    with pytest.raises(AttributeError):
        i.name = "other"


def test_lists():
    assert lists(Add, associative) and lists(Add, commutative) and not lists(Add, absorbing)
    assert lists(Mul, distributive) and not lists(Pow, associative)
    assert lists(And, idempotent) and lists(Or, identity) and not lists(sin, singleton)


def test_refused_listings():
    P = declare_function("Pow2", NumberKind, NumberKind, returns=NumberKind)
    with pytest.raises(TypeError, match="associative cannot be listed for Pow2"):
        declare_identities(P, [associative])
    with pytest.raises(TypeError, match="commutative cannot be listed for Pow2"):
        declare_identities(P, [commutative])
    S = declare_function("sin2", NumberKind, returns=NumberKind)
    with pytest.raises(TypeError, match="associative cannot be listed for sin2"):
        declare_identities(S, [associative])
    with pytest.raises(TypeError, match="commutative cannot be listed for sin2"):
        declare_identities(S, [commutative])
    A = declare_function("Add2", rest=NumberKind, returns=NumberKind)
    with pytest.raises(TypeError, match=r"identity\(true\) cannot be listed for Add2"):
        declare_identities(A, [identity(true)])
    with pytest.raises(TypeError, match=r"absorbing\(false\) cannot be listed for Add2"):
        declare_identities(A, [associative, absorbing(false)])
    O = declare_function("Or2", rest=BoolKind, returns=BoolKind)
    with pytest.raises(TypeError, match=r"identity\(0\) cannot be listed for Or2"):
        declare_identities(O, [identity(0)])
    with pytest.raises(TypeError, match="distributive"):
        declare_identities(O, [distributive(Add)])
    # A refused block records nothing, so a correct one can follow.
    assert identities(A) == [] and not is_flat(A)
    declare_identities(A, [associative, identity(0)])
    assert is_flat(A) and not is_unordered(A)


def test_refused_items():
    F = declare_function("F3", NumberKind, returns=NumberKind)
    a = NumberKind("a_")
    with pytest.raises(ValueError, match="function at the top of its left side"):
        declare_identities(F, [Equal(sin(a), 0)])
    with pytest.raises(TypeError, match="a generic identity, or Equal"):
        declare_identities(F, [("zero", Equal(F(a), 0))])
    with pytest.raises(ValueError, match="must be in its left side"):
        declare_identities(F, [Equal(F(a), NumberKind("b_"))])
    with pytest.raises(ValueError, match="two identities of F3 are named f3_a"):
        declare_identities(F, [Equal(F(a), 0), Equal(F(a), 1)])
    with pytest.raises(ValueError, match="already named"):
        Equal(F(a), 2, name="one"), Equal(F(a), 2, name="other")
    with pytest.raises(TypeError, match="declared function"):
        declare_identities(x, [])
    with pytest.raises(TypeError, match="NumberKind"):
        Equal(F(a), true)


def test_one_block_per_function():
    for F in (Add, Mul, Pow, exp, And, Or):
        with pytest.raises(ValueError, match="already declared"):
            declare_identities(F, [])
    F = declare_function("F4", rest=NumberKind, returns=NumberKind)
    declare_identities(F, [])
    with pytest.raises(ValueError, match="the identities of F4 are already declared"):
        declare_identities(F, [commutative])
    assert identities(F) == []


def test_blocks_replace_the_recorded_facts():
    for F in (Add, Mul, And, Or):
        assert is_unordered(F) and is_flat(F)
        with pytest.raises(ValueError, match="already recorded"):
            unordered(F)
    assert not is_unordered(Pow) and not is_flat(Pow)


# The rules the blocks give the engine.

def test_rules_come_from_the_blocks():
    a = NumberKind("a")
    assert [(r.name, r.pattern, r.replacement, r.condition) for r in rules] == [
        ("add_identity", a + 0, a, None),
        ("add_inverse", a - a, NumberKind(0), None),
        ("add_repeated", a + a, 2 * a, None),
        ("mul_identity", a * 1, a, None),
        ("mul_absorbing", a * 0, NumberKind(0), None),
        ("mul_inverse", a / a, NumberKind(1), Ne(a, 0)),
        ("pow_one", a ** 1, a, None),
        ("pow_zero", a ** 0, NumberKind(1), Ne(a, 0)),
        ("exp_log", exp(log(a)), a, Ne(a, 0)),
    ]
    def fields(r):
        return r.name, r.pattern, r.replacement, r.condition

    rebuilt = [r for F in (Add, Mul, Pow, exp) for r in identity_rules(F)]
    # mul_repeated is given by the block of Mul but left out of the
    # default rules: with it, x*x - x*x would no longer rewrite to 0.
    [mul_repeated] = [r for r in rebuilt if r.name == "mul_repeated"]
    assert fields(mul_repeated) == ("mul_repeated", a * a, a ** 2, None)
    assert list(map(fields, rules)) == [fields(r) for r in rebuilt if r is not mul_repeated]
    x2 = Mul(x, x)
    assert rewrite(Add(x2, Mul(-1, x2)), rules) == NumberKind(0)
    assert rewrite(Add(x2, Mul(-1, x2)), rules + [mul_repeated]) != NumberKind(0)
    # The rules of sin are available, but not in the default rules.
    assert [r.name for r in identity_rules(sin)] == ["sin_0", "sin_mul_neg1_a", "sin_add_a_mul_2_pi"]
    assert not any(r.name.startswith("sin_") for r in rules)


def test_rewrite_results_unchanged():
    # The same inputs and results as before the blocks (see test_rewriting).
    assert rewrite(Add(x, 0, y), rules) == Add(x, y)
    assert rewrite(Add(x, y, x), rules) == Add(Mul(2, x), y)
    assert rewrite(x * 0, rules) == NumberKind(0)
    assert rewrite(log(x) * 0, rules) == log(x) * 0
    assert rewrite(x / x, rules) == x / x
    assert rewrite(Mul(x, Add(y, 1)), rules) == Mul(x, Add(y, 1))  # distributive is not applied
    assert rewrite(sin(x + 0) < y, rules) == (sin(x) < y)


def test_and_or_rules():
    p = BoolKind("p")
    and_rules, or_rules = identity_rules(And), identity_rules(Or)
    assert [r.name for r in and_rules] == ["and_idempotent", "and_identity", "and_absorbing"]
    assert rewrite(And(p, true, p), and_rules) == p
    assert rewrite(Or(p, false), or_rules) == p
    # A symbol has a value, so the absorbing rule applies.
    assert rewrite(And(p, false), and_rules) == false
    assert rewrite(Or(true, p), or_rules) == true
    # The erased argument must be known to have a value, as for every rule
    # today: Lt(x, 1) is not known to, so this stays blocked.
    assert rewrite(And(Lt(x, 1), false), and_rules) == And(Lt(x, 1), false)
    # The engine's default rules about numbers do not include these.
    assert rewrite(And(p, true), rules) == And(p, true)


def test_to_lean_identity():
    by_name = {i.name: i for F in (Add, Mul, Pow, And) for i in identities(F)}
    assert to_lean_identity(by_name["add_associative"]) == (
        "abbrev add_associative : Prop :=\n  Nary.Flat Nary.Add"
    )
    assert to_lean_identity(by_name["add_commutative"]) == (
        "abbrev add_commutative : Prop :=\n  Nary.Unordered Nary.Add"
    )
    assert to_lean_identity(by_name["mul_absorbing"]).endswith("Nary.Absorbing Nary.Mul (Nary.lit 0)")
    assert to_lean_identity(by_name["mul_distributive"]).endswith(
        "Nary.Distributive Nary.Mul Nary.Add"
    )
    # A specific identity is stated as the rule it gives.
    assert to_lean_identity(by_name["pow_one"]).split()[1] == "pow_one"
    with pytest.raises(TypeError):
        to_lean_identity(rules[0])

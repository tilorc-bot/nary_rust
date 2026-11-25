"""Holes, generic identities and the blocks of nary.identities, and the rules
the blocks give nary.rewriting."""

import doctest

import nary.identities
import pytest
from nary import (
    Add,
    AnyKind,
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
    absorbing,
    associative,
    commutative,
    declare_identities,
    declare_identity,
    distributive,
    generic,
    hole,
    idempotent,
    identities,
    identity,
    lists,
    singleton,
)
from nary.lean import to_lean, to_lean_identity
from nary.logic import And, Or, false, true
from nary.rewriting import rewrite
from nary.rules import identity_rules, is_flat, is_unordered, rule, unordered

x, y = NumberKind("x"), NumberKind("y")
hx, hy = hole(NumberKind, "x"), hole(NumberKind, "y")


def test_docstring_examples():
    result = doctest.testmod(nary.identities)
    assert result.attempted > 0 and result.failed == 0


# Holes versus symbols.

def test_a_hole_is_not_a_symbol():
    assert hx.is_hole and not hx.is_symbol and not hx.is_multi_hole
    assert x.is_symbol and not x.is_hole
    assert hx != x and hash(hx) != hash(x)
    assert hx == hole(NumberKind, "x") and hash(hx) == hash(hole(NumberKind, "x"))
    assert hx != hole(BoolKind, "x")
    assert (hx.name, hx.kind, repr(hx)) == ("x", NumberKind, "?x")


def test_multi_argument_holes():
    s = hole(NumberKind, "s", multi=True)
    assert s.is_hole and s.is_multi_hole and repr(s) == "?s*"
    assert s != hole(NumberKind, "s") and s == hole(NumberKind, "s", multi=True)
    assert repr(Add(s, x)) == "Add(?s*, x)"
    # A run of arguments fits only a position that takes any number of them.
    with pytest.raises(TypeError, match="multi-argument hole"):
        sin(s)


def test_holes_in_rules_and_matching():
    # In a rule every symbol is a variable; a hole is refused there.
    with pytest.raises(ValueError, match="cannot contain the hole"):
        rule(hx + 0, hx)
    # In an expression being rewritten a hole is an ordinary leaf, which a
    # variable of its kind matches.
    assert rewrite(Add(hx, 0), rules) == hx
    assert rewrite(Add(x, 0), [rule(Add(x, 0), x)]) == x
    assert rewrite(Add(hx, 0), [rule(Add(x, 0), x)]) == hx


def test_symbols_in_identities_are_refused():
    F = declare_function("S3", NumberKind, returns=NumberKind)
    with pytest.raises(ValueError, match="write x in .* as a hole"):
        declare_identities(F, [("zero", Equal(F(x), 0))])
    f = hole(nary.identities.AnyFunction, "f")
    with pytest.raises(ValueError, match="holes only"):
        declare_identity("bad", f(x), x)
    with pytest.raises(TypeError):
        Equal(1, 2)


def test_to_lean_refuses_holes():
    with pytest.raises(ValueError, match="to_lean_identity"):
        to_lean(hx + 1)


# Generic identities.

def test_generic_identity_records():
    g = generic(associative)
    assert g.name == "associative" and g.params == () and g.normal is None
    assert repr(g.definition) == "Equal(?f(?s*, ?f(?t*), ?u*), ?f(?s*, ?t*, ?u*))"
    assert generic(commutative).normal == "Sorted"
    assert [p.name for p in generic(identity).params] == ["e"]
    assert [p.name for p in generic(distributive).params] == ["g"]
    assert generic(x) is None
    # Applied to its parameter, a generic identity is an expression of the
    # generic kind, not a rule.
    assert identity(NumberKind(0)).kind is AnyKind and repr(identity(true)) == "identity(true)"
    with pytest.raises(TypeError, match="NumberKind"):
        identity(0)


def test_declare_identity_refusals():
    f = hole(nary.identities.AnyFunction, "f")
    a, b = hole(AnyKind, "a"), hole(AnyKind, "b")
    with pytest.raises(ValueError, match="function hole"):
        declare_identity("bad1", a, a)
    with pytest.raises(ValueError, match="must be in its left side"):
        declare_identity("bad2", f(a), b)
    with pytest.raises(ValueError, match="parameter"):
        declare_identity("bad3", f(a), a, params=(b,))
    with pytest.raises(ValueError, match="identifier"):
        declare_identity("not a name", f(a), a)


# Blocks.

def test_identities_of_a_function():
    names = {F: [i.name for i in identities(F)] for F in (Add, Mul, Pow, exp, And, Or)}
    assert names[Add] == ["add_associative", "add_commutative", "add_singleton",
                          "add_identity", "add_self", "add_neg_self"]
    assert names[Mul] == ["mul_associative", "mul_commutative", "mul_singleton",
                          "mul_identity", "mul_absorbing", "mul_distributive", "mul_inv_self"]
    assert names[Pow] == ["pow_one", "pow_zero"]
    assert names[exp] == ["exp_log"]
    assert names[And] == ["and_associative", "and_commutative", "and_singleton",
                          "and_idempotent", "and_identity", "and_absorbing"]
    assert names[Or] == ["or_associative", "or_commutative", "or_singleton",
                         "or_idempotent", "or_identity", "or_absorbing"]
    assert identities(sin) == []


def test_instances_are_filled_and_typed():
    by_name = {i.name: i for i in identities(Mul)}
    i = by_name["mul_absorbing"]
    assert (i.item, i.generic, i.function) == (absorbing(NumberKind(0)), absorbing, Mul)
    assert repr(i.lhs) == "Mul(?s*, 0, ?t*)" and i.rhs == NumberKind(0) and i.when is None
    assert i.lhs.kind is NumberKind
    d = by_name["mul_distributive"]
    assert repr(d.lhs) == "Mul(?a, Add(?b, ?c))"
    assert repr(d.rhs) == "Add(Mul(?a, ?b), Mul(?a, ?c))"
    s = by_name["mul_inv_self"]
    a = hole(NumberKind, "a")
    assert (s.generic, s.lhs, s.rhs, s.when) == (None, a / a, NumberKind(1), Ne(a, 0))
    assert repr(identities(And)[5].lhs) == "And(?s*, false, ?t*)"
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
        declare_identities(O, [identity(NumberKind(0))])
    with pytest.raises(TypeError, match="distributive"):
        declare_identities(O, [distributive(Add)])
    # A refused block records nothing, so a correct one can follow.
    assert identities(A) == [] and not is_flat(A)
    declare_identities(A, [associative, identity(NumberKind(0))])
    assert is_flat(A) and not is_unordered(A)


def test_refused_items():
    F = declare_function("F3", NumberKind, returns=NumberKind)
    a = hole(NumberKind, "a")
    with pytest.raises(ValueError, match="function at the top of its left side"):
        declare_identities(F, [("zero", Equal(sin(a), 0))])
    with pytest.raises(TypeError, match="a pair"):
        declare_identities(F, [Equal(F(a), 0)])
    with pytest.raises(ValueError, match="must be in its left side"):
        declare_identities(F, [("other", Equal(F(a), hole(NumberKind, "b")))])
    with pytest.raises(ValueError, match="two identities of F3 are named f3_zero"):
        declare_identities(F, [("zero", Equal(F(a), 0)), ("zero", Equal(F(F(a)), 0))])
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
        ("add_self", a + a, 2 * a, None),
        ("add_neg_self", a - a, NumberKind(0), None),
        ("mul_identity", a * 1, a, None),
        ("mul_absorbing", a * 0, NumberKind(0), None),
        ("mul_inv_self", a / a, NumberKind(1), Ne(a, 0)),
        ("pow_one", a ** 1, a, None),
        ("pow_zero", a ** 0, NumberKind(1), Ne(a, 0)),
        ("exp_log", exp(log(a)), a, Ne(a, 0)),
    ]
    def fields(r):
        return r.name, r.pattern, r.replacement, r.condition

    rebuilt = [r for F in (Add, Mul, Pow, exp) for r in identity_rules(F)]
    assert list(map(fields, rules)) == list(map(fields, rebuilt))
    assert identity_rules(sin) == []


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

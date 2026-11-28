from collections import Counter
from fractions import Fraction

import pytest

from nary import BoolKind, Eq, Many, NumberKind, declare_constant, declare_function, declare_kind, re
from nary.logic import And, Or, false, true
from nary.matrices import Matrix, MatMul, Transpose
from nary.normalising import normalise
from nary.properties import declare_properties

x, y = NumberKind("x"), NumberKind("y")
p, q = BoolKind("p"), BoolKind("q")


def test_a_new_kind_with_constants_for_its_elements():
    Lattice = declare_kind("Lattice")
    top = declare_constant("top", Lattice)
    bottom = declare_constant("bottom", Lattice)
    Meet = declare_function("Meet", Many(Lattice), returns=Lattice, domain=true)
    declare_properties(
        Meet, is_associative=True, is_commutative=True,
        identity_element=top, absorbing_element=bottom, is_idempotent=True,
    )
    a, b = Lattice("a"), Lattice("b")

    assert normalise(Meet(b, top, a)) == normalise(Meet(a, b))
    assert normalise(Meet(b, Meet(a, top), a)) == normalise(Meet(a, b))
    assert normalise(Meet(a, bottom, b)) == bottom
    assert normalise(Meet()) == top
    assert normalise(Meet(top, top)) == top
    assert normalise(Meet(a)) == a
    assert normalise(Meet(a, top)).kind is Lattice


def test_a_sequence_on_a_new_kind_keeps_its_order():
    Word = declare_kind("Word")
    eps = declare_constant("eps", Word)
    Concat = declare_function("Concat", Many(Word), returns=Word, domain=true)
    declare_properties(Concat, is_associative=True, identity_element=eps, is_idempotent=True)
    a, b = Word("a"), Word("b")

    assert normalise(Concat(b, eps, a, Concat(eps, a), eps)) == Concat(b, a)
    assert normalise(Concat(a, b, a)) == Concat(a, b, a)
    assert normalise(Concat(b, a)) == Concat(b, a)
    assert normalise(Concat(eps, eps)) == eps
    assert normalise(Concat()) == eps


def test_a_kind_with_bytes_literals_drops_the_empty_literal():
    Text = declare_kind("Text", literals=bytes)
    Join = declare_function("Join", Many(Text), returns=Text, domain=true)
    declare_properties(Join, is_associative=True, identity_element=b"")
    t = Text("t")

    assert Join.identity_element == Text(b"")
    assert normalise(Join(b"ab", b"", t, Join(b"", b"cd"))) == Join(b"ab", t, b"cd")
    assert normalise(Join(b"", b"")) == Text(b"")


def test_an_identity_literal_matches_only_its_own_type():
    Real = declare_kind("Real", literals=(int, float, Fraction))
    Plus = declare_function("Plus", Many(Real), returns=Real, domain=true)
    declare_properties(Plus, is_associative=True, is_commutative=True, identity_element=0.0)
    r = Real("r")

    assert normalise(Plus(r, 0.0)) == r
    assert Counter(normalise(Plus(r, 0)).args) == Counter([r, Real(0)])
    assert Counter(normalise(Plus(r, Fraction(0))).args) == Counter([r, Real(Fraction(0))])


def test_heads_over_a_member_of_a_kind_family():
    zero_m = declare_constant("Zm", Matrix)
    one_m = declare_constant("Im", Matrix)
    MSum = declare_function("MSum", Many(Matrix), returns=Matrix, domain=true)
    declare_properties(MSum, is_associative=True, is_commutative=True, identity_element=zero_m)
    MProd = declare_function("MProd", Many(Matrix), returns=Matrix, domain=true)
    declare_properties(MProd, is_associative=True, identity_element=one_m)
    A, B = Matrix("A"), Matrix("B")

    assert normalise(MSum(B, zero_m, MSum(A, zero_m))) == normalise(MSum(A, B))
    assert normalise(MProd(B, one_m, A, MProd(one_m, B))) == MProd(B, A, B)
    assert normalise(MSum(MProd(A, one_m), zero_m)) == A
    assert normalise(MProd()).kind is Matrix


def test_absorbing_needs_a_value_and_a_function_without_a_domain_gives_none():
    inf_m = declare_constant("Inf", Matrix)
    MAbsorb = declare_function("MAbsorb", Many(Matrix), returns=Matrix, domain=true)
    declare_properties(MAbsorb, is_associative=True, is_commutative=True, absorbing_element=inf_m)
    A, B = Matrix("A"), Matrix("B")

    assert normalise(MAbsorb(A, inf_m, B)) == inf_m
    assert Counter(normalise(MAbsorb(Transpose(A), inf_m)).args) == Counter([Transpose(A), inf_m])
    assert Counter(normalise(MAbsorb(MatMul(A, B), inf_m)).args) == Counter(
        [MatMul(A, B), inf_m]
    )


def test_a_function_declared_without_a_domain_needs_a_reserved_name():
    with pytest.raises(TypeError, match="the domain of Floating must be a BoolKind expression"):
        declare_function("Floating", Many(Matrix), returns=Matrix, domain=None)


def test_boolean_arguments_that_become_equal_once_their_numbers_are_normal():
    assert normalise(And(x + 0 < y, x < y)) == (x < y)
    assert normalise(Or(Eq(x + y, 1), Eq(y + x, x * 0 + 1), false)) == Eq(normalise(x + y), 1)
    assert Counter(normalise(And(Eq(x, y), Eq(y, x))).args) == Counter([Eq(x, y), Eq(y, x)])


def test_nested_and_or_mixtures():
    assert normalise(Or(And(p, Or(q, false)), And(Or(false, q), p))) == normalise(And(p, q))
    assert normalise(And(Or(p, true), Or(q, And(q, true)))) == q
    assert normalise(And(p, Or(q, And(p, false)), true)) == normalise(And(p, q))


def test_a_value_that_needs_a_domain_is_not_absorbed():
    assert normalise(And(false, Eq(x, y))) == false
    assert Counter(normalise(And(false, x < y)).args) == Counter([false, x < y])
    both_real = normalise(And(Eq(re(x), x), Eq(re(y), y)))
    assert normalise(And(false, x < y), lambda c: c == both_real) == false


def test_a_head_whose_output_kind_differs_from_its_inputs_is_only_ordered():
    Near = declare_function("Near", NumberKind, NumberKind, returns=BoolKind, domain=true)
    declare_properties(Near, is_commutative=True)

    assert normalise(Near(y, x)) == normalise(Near(x, y))
    assert normalise(Near(x, x)) == Near(x, x)
    assert normalise(Near(y + 0, x * 1)) == normalise(Near(x, y))


def test_an_element_cannot_be_declared_where_the_output_kind_differs():
    Close = declare_function("Close", NumberKind, NumberKind, returns=BoolKind, domain=true)
    with pytest.raises(TypeError, match="Close expects NumberKind, got BoolKind: a"):
        declare_properties(Close, is_commutative=True, identity_element=0)
    with pytest.raises(TypeError, match="Close expects NumberKind, got BoolKind: a"):
        declare_properties(Close, absorbing_element=true)
    with pytest.raises(ValueError, match="flat needs a function"):
        declare_properties(Close, is_associative=True)
    assert Close.identity_element is None and Close.is_commutative is False


@pytest.mark.xfail(strict=True, reason="is_idempotent is accepted on a head with a different output kind")
def test_idempotence_keeps_the_output_kind():
    Apart = declare_function("Apart", NumberKind, NumberKind, returns=BoolKind, domain=true)
    declare_properties(Apart, is_commutative=True, is_idempotent=True)
    assert normalise(Apart(x, x)).kind is BoolKind


def test_each_head_in_a_mixed_expression_uses_its_own_elements():
    assert normalise(And(Eq(x + 0, y), Or(p, false), true)) == normalise(And(Eq(x, y), p))
    assert normalise(Or(Eq(x * 0, 0), false)) == Eq(0, 0)


def test_a_constant_that_prints_like_an_identity_is_not_one():
    fake_false = declare_constant("false", BoolKind)
    fake_zero = declare_constant("0", NumberKind)

    assert Counter(normalise(Or(p, fake_false)).args) == Counter([p, fake_false])
    assert Counter(normalise(x + fake_zero).args) == Counter([x, fake_zero])
    assert normalise(Or(p, false, fake_false)) != p


def test_two_constants_with_one_name_are_different_elements():
    Tag = declare_kind("Tag")
    unit = declare_constant("unit", Tag)
    other_unit = declare_constant("unit", Tag)
    Tags = declare_function("Tags", Many(Tag), returns=Tag, domain=true)
    declare_properties(Tags, is_associative=True, identity_element=unit)
    t = Tag("t")

    assert normalise(Tags(t, unit)) == t
    assert normalise(Tags(t, other_unit)) == Tags(t, other_unit)


@pytest.mark.xfail(strict=True, reason="arguments are sorted by repr, which ties for same-named constants")
def test_the_order_of_same_named_constants_does_not_change_the_result():
    Badge = declare_kind("Badge")
    first, second = declare_constant("twin", Badge), declare_constant("twin", Badge)
    Badges = declare_function("Badges", Many(Badge), returns=Badge, domain=true)
    declare_properties(Badges, is_associative=True, is_commutative=True)
    assert normalise(Badges(first, second)) == normalise(Badges(second, first))

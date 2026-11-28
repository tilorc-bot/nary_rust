from fractions import Fraction
from itertools import permutations
from math import prod

import pytest

from nary import (
    Add, BoolKind, Many, Mul, Ne, NumberKind, Pow, declare_constant, declare_function,
    Rational, declare_kind, log, sin,
)
from nary.logic import And, Or, true
from nary.normalising import normalise
from nary.properties import declare_properties

x, y, z = (NumberKind(name) for name in "xyz")
p, q, r = (BoolKind(name) for name in "pqr")


def number_head(name, **properties):
    head = declare_function(name, Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(head, **properties)
    return head


Top = number_head("CollectTop", is_associative=True, is_commutative=True, is_idempotent=True)
Plus = number_head(
    "CollectPlus", is_associative=True, is_commutative=True, identity_element=0,
    distributes_over=Top,
)
Sum = number_head("CollectSum", is_associative=True, is_commutative=True, identity_element=0)
Scaled = number_head(
    "CollectScaled", is_associative=True, is_commutative=True, distributes_over=Sum,
)
Then = declare_function("CollectThen", NumberKind, NumberKind, returns=NumberKind, domain=true)
declare_properties(Then, distributes_over=Sum)


def value(e, at):
    if e.is_literal:
        return Fraction(e.value)
    if e.is_symbol:
        return at[e]
    args = [value(arg, at) for arg in e.args]
    if e.head in (Add, Plus):
        return sum(args, Fraction(0))
    if e.head == Mul:
        return prod(args, start=Fraction(1))
    if e.head == Top:
        return max(args)
    if e.head == Pow:
        return args[0] ** int(args[1])
    raise ValueError(e)


POINTS = [
    {x: Fraction(a), y: Fraction(b), z: Fraction(c)} for a, b, c in [(2, -3, 5), (-1, 7, 1), (4, 4, -2)]
]


def test_mul_distributes_over_add():
    assert Mul.distributes_over == Add


def test_and_and_or_distribute_over_each_other():
    assert (And.distributes_over, Or.distributes_over) == (Or, And)


def test_add_and_pow_distribute_over_nothing():
    assert (Add.distributes_over, Pow.distributes_over) == (None, None)


def test_a_term_added_to_itself_is_twice_the_term():
    assert normalise(x + x) == Mul(2, x)


def test_coefficients_of_equal_terms_are_added():
    assert normalise(2 * x + 3 * x) == Mul(5, x)


def test_a_product_and_a_multiple_of_it_are_added():
    assert normalise(x * y + 2 * x * y) == Mul(3, x, y)


def test_a_term_and_its_negation_add_up_to_zero():
    assert normalise(x + (-1) * x) == NumberKind(0)


def test_a_term_that_may_have_no_value_and_its_negation_do_not_add_up_to_zero():
    assert normalise(log(x) + (-1) * log(x)) == Mul(0, log(x))


def test_a_term_and_its_negation_add_up_to_zero_where_known_says_the_term_has_a_value():
    assert normalise(log(x) + (-1) * log(x), lambda c: c == Ne(x, 0)) == NumberKind(0)


def test_a_term_that_may_have_no_value_added_to_itself_is_twice_the_term():
    assert normalise(log(x) + log(x)) == Mul(2, log(x))


def test_only_terms_with_the_same_rest_are_collected():
    assert normalise(x + 2 * x + y + x * y) == Add(Mul(3, x), Mul(x, y), y)


def test_several_groups_are_collected_at_once():
    assert normalise(x + y + 3 * y + Rational(1, 2) * x) == Add(Mul(4, y), Mul(Rational(3, 2), x))


def test_terms_from_different_levels_of_a_nested_sum_are_collected():
    assert normalise(Add(x, Add(y, Add(sin(x), 2 * x)))) == Add(Mul(3, x), sin(x), y)


def test_a_product_of_a_number_and_a_sum_is_not_expanded():
    assert normalise(2 * (x + 1)) == Mul(2, Add(1, x))


def test_a_common_factor_that_is_not_a_number_is_not_taken_out():
    assert normalise(x * y + x * z) == Add(Mul(x, y), Mul(x, z))


def test_a_common_number_factor_is_not_taken_out():
    assert normalise(2 * x + 2 * y) == Add(Mul(2, x), Mul(2, y))


def test_a_number_is_not_collected_with_a_multiple_of_a_symbol():
    assert normalise(2 + 2 * x) == Add(2, Mul(2, x))


def test_or_of_ands_that_share_an_argument_is_not_rewritten():
    assert normalise(Or(And(p, q), And(p, r))) == Or(And(p, q), And(p, r))


def test_an_argument_or_ed_with_an_and_containing_it_is_not_rewritten():
    assert normalise(Or(p, And(p, q))) == Or(And(p, q), p)


def test_or_of_equal_ands_is_one_and():
    assert normalise(Or(And(p, q), And(q, p))) == And(p, q)


def test_an_idempotent_head_over_which_a_head_with_an_identity_distributes():
    assert normalise(Top(x, Plus(2, x))) == Plus(Top(0, 2), x)


def test_coefficients_are_evaluated_where_the_head_distributed_over_declares_evaluate_literals():
    Max = number_head(
        "DistMax", is_associative=True, is_commutative=True, is_idempotent=True,
        evaluate_literals=max,
    )
    Plus = number_head(
        "DistPlus", is_associative=True, is_commutative=True, identity_element=0, distributes_over=Max,
    )
    assert normalise(Max(Plus(2, x), Plus(3, x))) == Plus(3, x)


def test_coefficients_are_combined_by_the_head_distributed_over_when_there_is_no_identity():
    assert normalise(Sum(Scaled(2, x), Scaled(3, x))) == Scaled(Sum(2, 3), x)


def test_a_bare_term_is_not_collected_by_a_head_without_an_identity():
    assert normalise(Sum(x, Scaled(2, x))) == Sum(Scaled(2, x), x)


def test_a_head_that_distributes_over_nothing_collects_nothing():
    assert normalise(Sum(x, x)) == Sum(x, x)


def test_a_two_argument_head_collects_coefficients_in_the_same_position():
    assert normalise(Sum(Then(2, x), Then(3, x))) == Then(Sum(2, 3), x)


def test_a_two_argument_head_does_not_collect_coefficients_in_different_positions():
    assert normalise(Sum(Then(x, 2), Then(3, x))) == Sum(Then(3, x), Then(x, 2))


def test_coefficients_of_two_terms_of_another_kind_are_not_added_by_vector_addition():
    Vector = declare_kind("CollectVector")
    zero = declare_constant("collect_zero", Vector)
    VAdd = declare_function("CollectVAdd", Many(Vector), returns=Vector, domain=true)
    declare_properties(VAdd, is_associative=True, is_commutative=True, identity_element=zero)
    Scale = declare_function("CollectScale", NumberKind, Vector, returns=Vector, domain=true)
    declare_properties(Scale, distributes_over=VAdd)
    v = Vector("v")

    assert normalise(VAdd(Scale(2, v), Scale(3, v))) == VAdd(Scale(2, v), Scale(3, v))


def test_a_vector_scaled_by_the_same_number_is_not_factored():
    Vector = declare_kind("FactorVector")
    VAdd = declare_function("FactorVAdd", Many(Vector), returns=Vector, domain=true)
    declare_properties(VAdd, is_associative=True, is_commutative=True)
    Scale = declare_function("FactorScale", NumberKind, Vector, returns=Vector, domain=true)
    declare_properties(Scale, distributes_over=VAdd)
    u, v = Vector("u"), Vector("v")

    assert normalise(VAdd(Scale(2, u), Scale(2, v))) == VAdd(Scale(2, u), Scale(2, v))


@pytest.mark.xfail(
    strict=True, reason="(a + b)*v = a*v + b*v relates Scale to Add and VAdd, which distributes_over cannot say",
)
def test_multiples_of_one_vector_are_added():
    Vector = declare_kind("SumVector")
    VAdd = declare_function("SumVAdd", Many(Vector), returns=Vector, domain=true)
    declare_properties(VAdd, is_associative=True, is_commutative=True)
    Scale = declare_function("SumScale", NumberKind, Vector, returns=Vector, domain=true)
    declare_properties(Scale, distributes_over=VAdd)
    v = Vector("v")

    assert normalise(VAdd(Scale(2, v), Scale(3, v))) == Scale(5, v)


@pytest.mark.xfail(strict=True, reason="collecting is done only where the head distributed over is commutative")
def test_neighbouring_equal_terms_of_a_sequence_are_collected():
    Chain = number_head("CollectChain", is_associative=True, identity_element=0)
    Repeat = number_head(
        "CollectRepeat", is_associative=True, is_commutative=True, identity_element=1,
        distributes_over=Chain,
    )
    assert normalise(Chain(y, x, x)) == Chain(y, Repeat(Chain(1, 1), x))


@pytest.mark.parametrize("args", list(permutations([x, Mul(2, x), y, Mul(-1, y), Mul(3, x, y), 1])))
def test_the_order_of_the_arguments_does_not_change_the_result(args):
    assert normalise(Add(*args)) == Add(1, Mul(3, x), Mul(3, x, y))


@pytest.mark.parametrize("e", [
    x + x + 2 * x * y + y * x,
    Mul(2, x + x) + 3 * (y + y),
    Top(x, Plus(2, x), Plus(x, 5)),
    log(x) + log(x),
])
def test_normalising_twice_is_normalising_once(e):
    assert normalise(normalise(e)) == normalise(e)


@pytest.mark.parametrize("e", [
    x + x,
    2 * x + 3 * x + y,
    x * y + 2 * x * y + Fraction(1, 2) * y * x + x,
    x + (-1) * x + z,
    (x + x) * (y + 2 * y),
    Top(x, Plus(2, x), Plus(y, 1), y),
])
def test_collecting_keeps_the_value(e):
    for at in POINTS:
        assert value(normalise(e), at) == value(e, at)

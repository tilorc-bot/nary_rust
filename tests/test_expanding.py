from fractions import Fraction
from itertools import permutations
from math import prod

import pytest

from nary import (
    Add, BoolKind, Many, Mul, Ne, NumberKind, Pow, Rational, declare_function, declare_kind, log,
    sin,
)
from nary.expanding import expand
from nary.logic import And, Or, true
from nary.normalising import normalise
from nary.properties import declare_properties

x, y, z = (NumberKind(name) for name in "xyz")


def number_head(name, **properties):
    head = declare_function(name, Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(head, **properties)
    return head


def value(e, at):
    if e.is_literal:
        return Fraction(e.value)
    if e.is_symbol:
        return at[e]
    args = [value(arg, at) for arg in e.args]
    if e.head == Add:
        return sum(args, Fraction(0))
    if e.head == Mul:
        return prod(args, start=Fraction(1))
    if e.head == Pow:
        return args[0] ** int(args[1])
    raise ValueError(e)


POINTS = [
    {x: Fraction(a), y: Fraction(b), z: Fraction(c)} for a, b, c in [(2, -3, 5), (-1, 7, 3), (4, 1, -2)]
]


def test_a_number_times_a_sum_is_multiplied_out():
    assert expand(2 * (x + 1)) == Add(2, Mul(2, x))


def test_a_sum_times_itself_is_multiplied_out_and_collected():
    assert expand((x + 1) * (x + 1)) == Add(1, Mul(2, x), Pow(x, 2))


def test_a_sum_times_a_difference_is_a_difference_of_squares():
    assert expand((x + y) * (x - y)) == Add(Mul(-1, Pow(y, 2)), Pow(x, 2))


def test_a_square_of_a_sum_is_multiplied_out():
    assert expand(Pow(x + 1, 2)) == Add(1, Mul(2, x), Pow(x, 2))


def test_a_cube_of_a_sum_is_multiplied_out():
    assert expand(Pow(x + y, 3)) == Add(
        Mul(3, Pow(x, 2), y), Mul(3, Pow(y, 2), x), Pow(x, 3), Pow(y, 3)
    )


def test_a_negative_power_of_a_sum_is_left():
    assert expand(Pow(x + 1, -1)) == Pow(Add(1, x), -1)


def test_a_square_root_of_a_sum_is_left():
    assert expand(Pow(x + 1, Rational(1, 2))) == Pow(Add(1, x), Rational(1, 2))


def test_a_power_of_a_sum_with_a_symbol_as_exponent_is_left():
    assert expand(Pow(x + 1, y)) == Pow(Add(1, x), y)


def test_a_product_inside_a_product_inside_a_sum_is_multiplied_out():
    assert expand(x * (y * (z + 1) + 1)) == Add(Mul(x, y), Mul(x, y, z), x)


def test_a_product_inside_a_function_is_multiplied_out():
    assert expand(sin(x * (y + 1))) == sin(Add(Mul(x, y), x))


def test_both_sides_of_the_distributive_law_expand_to_the_same():
    assert expand(x * (y + z)) == expand(x * y + x * z)


def test_a_product_without_a_sum_is_only_normalised():
    assert expand(x * y * x) == Mul(Pow(x, 2), y)


def test_and_and_or_are_left_because_each_distributes_over_the_other():
    p, q, r = (BoolKind(name) for name in "pqr")
    assert expand(And(p, Or(q, r))) == And(Or(q, r), p)


def test_a_factor_that_may_have_no_value_is_copied_into_each_term():
    assert expand(log(x) * (y + 1)) == Add(Mul(log(x), y), log(x))


def test_a_factor_that_may_have_no_value_times_zero_is_left():
    assert expand(log(x) * 0 * (y + 1)) == Mul(0, log(x))


def test_known_is_passed_to_normalise():
    assert expand(log(x) * 0 * (y + 1), lambda c: c == Ne(x, 0)) == NumberKind(0)


def test_a_head_that_is_not_commutative_keeps_the_order_of_its_arguments():
    Chain = number_head("ExpandChain", is_associative=True, distributes_over=Add)
    assert expand(Chain(x, Add(y, z), x)) == Add(Chain(x, y, x), Chain(x, z, x))


def test_a_two_argument_head_distributes_from_the_left():
    Then = declare_function("ExpandThen", NumberKind, NumberKind, returns=NumberKind, domain=true)
    declare_properties(Then, distributes_over=Add)
    assert expand(Then(Add(x, y), z)) == Add(Then(x, z), Then(y, z))


def test_scaling_distributes_over_vector_addition():
    Vector = declare_kind("ExpandVector")
    VAdd = declare_function("ExpandVAdd", Many(Vector), returns=Vector, domain=true)
    declare_properties(VAdd, is_associative=True, is_commutative=True)
    Scale = declare_function("ExpandScale", NumberKind, Vector, returns=Vector, domain=true)
    declare_properties(Scale, distributes_over=VAdd)
    u, v = Vector("u"), Vector("v")

    assert expand(Scale(2, VAdd(u, v))) == VAdd(Scale(2, u), Scale(2, v))


def test_a_head_that_distributes_over_nothing_is_left():
    Sum = number_head("ExpandSum", is_associative=True, is_commutative=True)
    Bag = number_head("ExpandBag", is_associative=True, is_commutative=True)
    assert expand(Bag(x, Sum(y, z))) == Bag(Sum(y, z), x)


@pytest.mark.xfail(
    strict=True,
    reason="the last normalise collects Top(x, Plus(2, x)) into Plus(Top(0, 2), x), "
    "and nothing evaluates Top(0, 2)",
)
def test_expanding_does_not_collect_coefficients_that_cannot_be_combined():
    Top = number_head("ExpandTop", is_associative=True, is_commutative=True, is_idempotent=True)
    Plus = number_head(
        "ExpandPlus", is_associative=True, is_commutative=True, identity_element=0,
        distributes_over=Top,
    )
    assert expand(Plus(x, Top(0, 2))) == Top(x, Plus(2, x))


@pytest.mark.parametrize("args", list(permutations([x + 1, y, x - 1, 2])))
def test_the_order_of_the_arguments_does_not_change_the_result(args):
    assert expand(Mul(*args)) == Add(Mul(-2, y), Mul(2, Pow(x, 2), y))


@pytest.mark.parametrize("e", [
    (x + 1) * (y + 1) * (z + 1),
    Pow(x - y, 3) + x * (x + y),
    2 * (x + Pow(y + 1, 2)),
])
def test_expanding_twice_is_expanding_once(e):
    assert expand(expand(e)) == expand(e)


@pytest.mark.parametrize("e", [
    (x + 1) * (y + 1) * (z + 1),
    Pow(x - y, 3) + x * (x + y),
    2 * (x + Pow(y + 1, 2)),
])
def test_normalising_an_expanded_expression_changes_nothing(e):
    assert normalise(expand(e)) == expand(e)


@pytest.mark.parametrize("e", [
    2 * (x + 1),
    (x + y) * (x - y),
    Pow(x + y, 3) * (z - 1),
    x * (y * (z + 1) + 1),
    Pow(Rational(1, 2) * x + y, 2),
    (x + 1) * Pow(x, -1),
])
def test_expanding_keeps_the_value(e):
    for at in POINTS:
        assert value(expand(e), at) == value(e, at)

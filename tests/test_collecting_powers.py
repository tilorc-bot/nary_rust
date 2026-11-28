from fractions import Fraction
from itertools import permutations
from math import prod

import pytest

from nary import (
    Add, Many, Mul, Ne, NumberKind, Pow, Rational, declare_function, declare_kind, log,
)
from nary.logic import true
from nary.normalising import normalise
from nary.properties import declare_properties

x, y, z = (NumberKind(name) for name in "xyz")
zero = NumberKind(0)


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


def test_mul_has_pow_as_its_power_function():
    assert Mul.power_function == Pow


def test_add_has_no_power_function():
    assert Add.power_function is None


def test_a_factor_times_itself_is_its_square():
    assert normalise(x * x) == Pow(x, 2)


def test_three_equal_factors_are_a_cube():
    assert normalise(x * x * x) == Pow(x, 3)


def test_powers_of_one_base_add_their_exponents():
    assert normalise(Pow(x, 2) * Pow(x, 3)) == Pow(x, 5)


def test_a_factor_times_its_square_is_its_cube():
    assert normalise(x * Pow(x, 2)) == Pow(x, 3)


def test_a_power_with_exponent_one_is_its_base():
    assert normalise(Pow(x, 1)) == x


def test_negative_exponents_are_added():
    assert normalise(Pow(x, -1) * Pow(x, -2)) == Pow(x, -3)


def test_a_factor_times_its_reciprocal_is_its_power_zero():
    assert normalise(x * Pow(x, -1)) == Pow(x, 0)


@pytest.mark.xfail(strict=True, reason="x**0 is 1 only where Ne(x, 0), and a step cannot ask whether that holds")
def test_a_power_zero_is_one_where_known_says_its_base_is_not_zero():
    assert normalise(x * Pow(x, -1), lambda c: c == Ne(x, 0)) == NumberKind(1)


def test_a_square_times_a_reciprocal_is_left_because_only_the_result_has_a_value_at_zero():
    assert normalise(Pow(x, 2) * Pow(x, -1)) == Mul(Pow(x, -1), Pow(x, 2))


def test_a_square_times_a_reciprocal_is_the_base_where_known_says_the_base_is_not_zero():
    assert normalise(Pow(x, 2) * Pow(x, -1), lambda c: c == Ne(x, 0)) == x


def test_zero_does_not_absorb_a_power_of_zero_that_has_no_value():
    assert normalise(Mul(0, Pow(0, -1))) == Mul(0, Pow(0, -1))


def test_powers_of_zero_without_a_value_merge_into_one_without_a_value():
    assert normalise(Pow(0, -1) * Pow(0, -1)) == Pow(0, -2)


def test_square_roots_of_one_base_multiply_to_the_base():
    half = Rational(1, 2)
    assert normalise(Pow(x, half) * Pow(x, half)) == x


def test_a_square_root_times_its_reciprocal_is_its_power_zero():
    assert normalise(Pow(x, Rational(1, 2)) * Pow(x, Rational(-1, 2))) == Pow(x, 0)


def test_powers_with_a_symbol_as_exponent_are_left():
    assert normalise(Pow(x, y) * Pow(x, y)) == Mul(Pow(x, y), Pow(x, y))


@pytest.mark.xfail(
    strict=True,
    reason="the domain of Pow(2, x) normalises to Or(Gt(re(x), 0), true), and true does not "
    "absorb a comparison that may have no value",
)
def test_powers_of_a_number_add_their_exponents():
    assert normalise(Pow(2, x) * Pow(2, y)) == Pow(2, Add(x, y))


def test_a_number_is_not_merged_with_a_power_of_that_number():
    assert normalise(2 * Pow(2, x)) == Mul(2, Pow(2, x))


def test_a_factor_that_may_have_no_value_times_itself_is_its_square():
    assert normalise(log(x) * log(x)) == Pow(log(x), 2)


def test_one_base_that_may_not_be_merged_does_not_stop_another():
    assert normalise(x * x * Pow(y, 2) * Pow(y, -1)) == Mul(Pow(x, 2), Pow(y, -1), Pow(y, 2))


def test_a_sum_times_itself_is_its_square_and_is_not_expanded():
    assert normalise((x + 1) * (x + 1)) == Pow(Add(1, x), 2)


def test_a_factor_times_a_sum_containing_it_is_not_expanded():
    assert normalise(x * (x + 1)) == Mul(Add(1, x), x)


def test_squares_are_collected_as_terms():
    assert normalise(x * x + 2 * x * x) == Mul(3, Pow(x, 2))


def test_numbers_and_powers_are_combined_in_one_product():
    assert normalise(Mul(2, x, 3, x, y)) == Mul(6, Pow(x, 2), y)


def test_a_freshly_declared_head_over_another_kind_repeats_an_argument():
    Turn = declare_kind("PowerTurn")
    Repeat = declare_function("PowerRepeat", Turn, NumberKind, returns=Turn, domain=true)
    Compose = declare_function("PowerCompose", Many(Turn), returns=Turn, domain=true)
    declare_properties(Compose, is_associative=True, is_commutative=True, power_function=Repeat)
    a, b = Turn("a"), Turn("b")

    assert normalise(Compose(a, b, a, Repeat(a, 3))) == Compose(Repeat(a, 5), b)


def test_a_freshly_declared_power_function_with_exponent_one_is_its_base():
    Turn = declare_kind("OneTurn")
    Repeat = declare_function("OneRepeat", Turn, NumberKind, returns=Turn, domain=true)
    Compose = declare_function("OneCompose", Many(Turn), returns=Turn, domain=true)
    declare_properties(Compose, is_associative=True, is_commutative=True, power_function=Repeat)

    assert normalise(Repeat(Turn("a"), 1)) == Turn("a")


def test_an_idempotent_head_keeps_one_copy_rather_than_a_power():
    Repeat = declare_function("IdemRepeat", NumberKind, NumberKind, returns=NumberKind, domain=true)
    Join = declare_function("IdemJoin", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Join, is_associative=True, is_commutative=True, is_idempotent=True, power_function=Repeat,
    )
    assert normalise(Join(x, x, y)) == Join(x, y)


@pytest.mark.xfail(strict=True, reason="powers are merged only where the head is commutative")
def test_neighbouring_copies_in_a_sequence_are_a_power():
    Repeat = declare_function("SeqRepeat", NumberKind, NumberKind, returns=NumberKind, domain=true)
    Chain = declare_function("SeqChain", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Chain, is_associative=True, power_function=Repeat)
    assert normalise(Chain(y, x, x)) == Chain(y, Repeat(x, 2))


@pytest.mark.parametrize("args", list(permutations([x, Pow(x, 2), y, Pow(y, -1), 3, z])))
def test_the_order_of_the_arguments_does_not_change_the_result(args):
    assert normalise(Mul(*args)) == Mul(3, Pow(x, 3), Pow(y, 0), z)


@pytest.mark.parametrize("e", [
    x * x * Pow(x, -1),
    Pow(x, 2) * Pow(x, -1) * y * y,
    (x * x + x * x) * x,
    Pow(Pow(x, 2) * x, 2) * Pow(x, 3),
])
def test_normalising_twice_is_normalising_once(e):
    assert normalise(normalise(e)) == normalise(e)


@pytest.mark.parametrize("e", [
    x * x * x,
    Pow(x, 2) * Pow(x, 3) * y,
    Pow(x, -1) * Pow(x, -2) * z,
    x * Pow(x, -1) * y,
    x * x + 2 * x * x + Pow(y, 2) * y,
    Mul(2, x, 3, x, Pow(z, 2), z),
])
def test_merging_powers_keeps_the_value(e):
    for at in POINTS:
        assert value(normalise(e), at) == value(e, at)

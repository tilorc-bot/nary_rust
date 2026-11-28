import pytest

from nary import (
    Add, E, Eq, Expr, Ge, Gt, Le, Lt, Mul, Ne, NumberKind, Pow, Rational, declare_kind, log, re, sin,
)
from nary._numbers import MAX_BITS, evaluate
from nary.logic import false, true
from nary.normalising import normalise


def numbers(*values):
    return [value if isinstance(value, Expr) else NumberKind(value) for value in values]


def test_a_sum_of_integers():
    assert evaluate(Add, numbers(2, 3, -7)) == NumberKind(-2)


def test_a_sum_of_rationals():
    assert evaluate(Add, numbers(Rational(1, 2), Rational(1, 3))) == Rational(5, 6)


def test_a_sum_of_an_integer_and_a_rational():
    assert evaluate(Add, numbers(3, Rational(-1, 2))) == Rational(5, 2)


def test_a_sum_of_rationals_that_is_an_integer_is_the_integer_literal():
    result = evaluate(Add, numbers(Rational(1, 2), Rational(1, 2)))
    assert repr(result) == "1" and type(result.value) is int


def test_a_sum_of_no_arguments_is_zero():
    assert evaluate(Add, []) == NumberKind(0)


def test_a_sum_of_one_argument_is_that_argument():
    assert evaluate(Add, numbers(Rational(1, 2))) == Rational(1, 2)


def test_a_product_of_integers():
    assert evaluate(Mul, numbers(2, -3, 4)) == NumberKind(-24)


def test_a_product_of_rationals():
    assert evaluate(Mul, numbers(Rational(2, 3), Rational(3, 4))) == Rational(1, 2)


def test_a_product_of_an_integer_and_a_rational():
    assert evaluate(Mul, numbers(3, Rational(1, 2))) == Rational(3, 2)


def test_a_product_of_rationals_that_is_an_integer_is_the_integer_literal():
    result = evaluate(Mul, numbers(4, Rational(1, 2)))
    assert repr(result) == "2" and type(result.value) is int


def test_a_product_of_no_arguments_is_one():
    assert evaluate(Mul, []) == NumberKind(1)


def test_a_product_with_zero_is_zero():
    assert evaluate(Mul, numbers(0, Rational(1, 2))) == NumberKind(0)


def test_an_integer_to_a_positive_integer_power():
    assert evaluate(Pow, numbers(2, 10)) == NumberKind(1024)


def test_an_integer_to_a_negative_integer_power_is_a_rational():
    assert evaluate(Pow, numbers(2, -1)) == Rational(1, 2)


def test_a_negative_integer_to_a_negative_integer_power_has_its_sign_on_the_numerator():
    assert repr(evaluate(Pow, numbers(-2, -1))) == "Rational(-1, 2)"


def test_a_rational_to_a_positive_integer_power():
    assert evaluate(Pow, numbers(Rational(-2, 3), 3)) == Rational(-8, 27)


def test_a_rational_to_a_negative_integer_power():
    assert evaluate(Pow, numbers(Rational(-2, 3), -3)) == Rational(-27, 8)


def test_a_rational_to_a_negative_integer_power_that_is_an_integer_is_the_integer_literal():
    result = evaluate(Pow, numbers(Rational(1, 2), -2))
    assert repr(result) == "4" and type(result.value) is int


def test_a_nonzero_number_to_the_power_zero_is_one():
    assert evaluate(Pow, numbers(Rational(7, 2), 0)) == NumberKind(1)


def test_zero_to_a_positive_integer_power_is_zero():
    assert evaluate(Pow, numbers(0, 3)) == NumberKind(0)


def test_zero_to_the_power_zero_has_no_value():
    assert evaluate(Pow, numbers(0, 0)) is None


def test_zero_to_a_negative_integer_power_has_no_value():
    assert evaluate(Pow, numbers(0, -1)) is None


def test_zero_to_a_negative_rational_power_has_no_value():
    assert evaluate(Pow, numbers(0, Rational(-1, 2))) is None


def test_a_square_root_that_is_not_rational_is_left_alone():
    assert evaluate(Pow, numbers(2, Rational(1, 2))) is None


def test_a_square_root_that_is_rational_is_left_alone_too():
    assert evaluate(Pow, numbers(4, Rational(1, 2))) is None


def test_a_rational_power_of_a_rational_is_left_alone():
    assert evaluate(Pow, numbers(Rational(4, 9), Rational(-3, 2))) is None


def test_the_real_part_of_an_integer():
    assert evaluate(re, numbers(-3)) == NumberKind(-3)


def test_the_real_part_of_a_rational():
    assert evaluate(re, numbers(Rational(1, 2))) == Rational(1, 2)


def test_equal_numbers_are_equal():
    assert evaluate(Eq, numbers(Rational(1, 2), Rational(1, 2))) == true


def test_different_numbers_are_not_equal():
    assert evaluate(Eq, numbers(Rational(1, 2), Rational(1, 3))) == false


def test_ne_of_different_numbers():
    assert evaluate(Ne, numbers(1, Rational(1, 2))) == true


def test_ne_of_equal_numbers():
    assert evaluate(Ne, numbers(2, 2)) == false


def test_lt_between_rationals_with_different_denominators():
    assert evaluate(Lt, numbers(Rational(1, 3), Rational(1, 2))) == true


def test_lt_of_equal_numbers():
    assert evaluate(Lt, numbers(2, 2)) == false


def test_gt_between_a_negative_rational_and_zero():
    assert evaluate(Gt, numbers(Rational(-1, 2), 0)) == false


def test_le_of_equal_numbers():
    assert evaluate(Le, numbers(Rational(1, 2), Rational(1, 2))) == true


def test_ge_between_an_integer_and_a_larger_rational():
    assert evaluate(Ge, numbers(1, Rational(3, 2))) == false


def test_rationals_that_differ_only_far_from_the_leading_digits_are_compared_exactly():
    assert evaluate(Lt, numbers(Rational(10**30, 10**30 + 1), Rational(10**30 + 1, 10**30 + 2))) == true


def test_a_symbol_among_the_arguments_gives_none():
    assert evaluate(Add, [NumberKind(1), NumberKind("x")]) is None


def test_a_constant_among_the_arguments_gives_none():
    assert evaluate(Mul, [NumberKind(2), E]) is None


def test_an_argument_that_is_not_yet_a_literal_gives_none():
    assert evaluate(Add, [NumberKind(1), Mul(2, 3)]) is None


def test_a_literal_of_another_kind_gives_none():
    Float = declare_kind("FloatForEvaluation", literals=float)
    assert evaluate(Add, [Float(0.5), Float(0.5)]) is None


def test_a_head_that_is_not_evaluated_gives_none():
    assert evaluate(sin, numbers(0)) is None


def test_a_power_of_three_arguments_gives_none():
    assert evaluate(Pow, numbers(2, 3, 4)) is None


def test_a_real_part_of_two_arguments_gives_none():
    assert evaluate(re, numbers(1, 2)) is None


def test_a_comparison_of_three_arguments_gives_none():
    assert evaluate(Eq, numbers(1, 1, 1)) is None


def test_the_largest_power_of_two_that_is_computed():
    assert evaluate(Pow, numbers(2, MAX_BITS)) == NumberKind(2**MAX_BITS)


def test_a_power_above_the_size_limit_is_left_alone():
    assert evaluate(Pow, numbers(2, MAX_BITS + 1)) is None


def test_a_power_with_a_denominator_above_the_size_limit_is_left_alone():
    assert evaluate(Pow, numbers(2, -MAX_BITS - 1)) is None


def test_a_power_of_a_rational_above_the_size_limit_is_left_alone():
    assert evaluate(Pow, numbers(Rational(3, 2), MAX_BITS)) is None


def test_a_power_with_an_enormous_exponent_is_left_alone_without_being_computed():
    assert evaluate(Pow, numbers(3, 10**100)) is None


def test_one_to_an_enormous_power_is_one():
    assert evaluate(Pow, numbers(1, 10**100)) == NumberKind(1)


def test_minus_one_to_an_enormous_odd_power_is_minus_one():
    assert evaluate(Pow, numbers(-1, -(10**100) - 1)) == NumberKind(-1)


def test_zero_to_an_enormous_power_is_zero():
    assert evaluate(Pow, numbers(0, 10**100)) == NumberKind(0)


def test_the_largest_product_of_two_powers_of_two_that_is_computed():
    half = MAX_BITS // 2
    assert evaluate(Mul, numbers(2**half, 2**half)) == NumberKind(2**MAX_BITS)


def test_a_product_above_the_size_limit_is_left_alone():
    half = MAX_BITS // 2
    assert evaluate(Mul, numbers(2**half, 2 ** (half + 1))) is None


def test_a_product_with_a_denominator_above_the_size_limit_is_left_alone():
    half = MAX_BITS // 2
    assert evaluate(Mul, numbers(Rational(1, 2**half), Rational(1, 2 ** (half + 1)))) is None


def test_a_product_of_many_copies_of_a_large_literal_is_left_alone():
    assert evaluate(Mul, numbers(2**13_000) * 4096) is None


def test_the_largest_sum_of_two_powers_of_two_that_is_computed():
    assert evaluate(Add, numbers(2 ** (MAX_BITS - 1), 2 ** (MAX_BITS - 1))) == NumberKind(2**MAX_BITS)


def test_a_sum_above_the_size_limit_is_left_alone():
    assert evaluate(Add, numbers(2**MAX_BITS, 1)) is None


def test_a_sum_with_a_denominator_above_the_size_limit_is_left_alone():
    half = MAX_BITS // 2
    assert evaluate(Add, numbers(Rational(1, 2**half + 1), Rational(1, 2**half + 3))) is None


def test_a_sum_of_more_integers_than_the_size_limit_is_computed():
    assert evaluate(Add, numbers(1) * (MAX_BITS + 1)) == NumberKind(MAX_BITS + 1)


def test_a_result_at_the_size_limit_still_has_a_repr():
    assert len(repr(evaluate(Pow, numbers(2, MAX_BITS)))) == 4215


def test_normalise_adds_integers():
    assert normalise(Add(2, 3)) == NumberKind(5)


def test_normalise_multiplies_integers():
    assert normalise(Mul(2, 3)) == NumberKind(6)


def test_normalise_turns_a_division_of_integers_into_a_rational_literal():
    assert normalise(Mul(3, Pow(2, -1))) == Rational(3, 2)


def test_normalise_turns_a_reciprocal_into_a_rational_literal():
    assert normalise(Pow(2, -1)) == Rational(1, 2)


def test_normalise_evaluates_operators_between_literals():
    assert normalise((NumberKind(1) / 2 - NumberKind(1) / 3) ** 2) == Rational(1, 36)


def test_normalise_evaluates_from_the_innermost_arguments_outwards():
    assert normalise(Add(Mul(2, 3), Pow(2, 3), Rational(1, 2))) == Rational(29, 2)


def test_normalise_evaluates_nested_sums_as_one_sum():
    assert normalise(Add(Add(1, 2), Add(3, 4))) == NumberKind(10)


def test_normalise_evaluates_the_numbers_inside_an_expression_with_a_symbol():
    x = NumberKind("x")
    assert normalise(sin(Add(x, Mul(2, 3)))) == sin(Add(6, x))


def test_normalise_decides_a_comparison_of_numbers():
    assert normalise(Lt(Rational(1, 3), Pow(2, -1))) == true


def test_normalise_decides_an_equation_of_numbers_reached_differently():
    assert normalise(Eq(Add(Rational(1, 3), Rational(1, 6)), Mul(3, Pow(6, -1)))) == true


def test_normalise_evaluates_the_real_part_of_a_number():
    assert normalise(Gt(re(2), 0)) == true


def test_normalise_leaves_zero_to_the_power_minus_one_as_written():
    assert normalise(Pow(0, -1)) == Pow(0, -1)


def test_normalise_does_not_let_zero_absorb_a_power_without_a_value():
    assert normalise(Mul(0, Pow(0, -1))) == Mul(0, Pow(0, -1))


def test_normalise_lets_zero_absorb_a_logarithm_of_a_nonzero_number():
    assert normalise(Mul(0, log(2))) == NumberKind(0)


def test_normalise_does_not_let_zero_absorb_the_logarithm_of_zero():
    assert normalise(Mul(0, log(Add(1, -1)))) == Mul(0, log(0))


def test_normalise_leaves_a_square_root_as_written():
    assert normalise(Pow(4, Rational(1, 2))) == Pow(4, Rational(1, 2))


def test_normalise_leaves_a_power_above_the_size_limit_as_written():
    assert normalise(Pow(2, MAX_BITS + 1)) == Pow(2, MAX_BITS + 1)


def test_normalise_leaves_a_product_above_the_size_limit_as_written():
    large = NumberKind(2**13_000)
    assert normalise(Mul(large, large)) == Mul(large, large)


def test_normalise_of_a_literal_result_changes_nothing():
    half = normalise(Pow(2, -1))
    assert normalise(half) == half


@pytest.mark.xfail(strict=True, reason="numbers are evaluated only where every argument is a number")
def test_normalise_adds_the_numbers_among_the_arguments_of_a_sum():
    x = NumberKind("x")
    assert normalise(Add(x, 1, 2)) == Add(3, x)


@pytest.mark.xfail(strict=True, reason="numbers are evaluated only where every argument is a number")
def test_normalise_multiplies_the_numbers_among_the_arguments_of_a_product():
    x = NumberKind("x")
    assert normalise(Mul(2, x, Rational(1, 2))) == x


@pytest.mark.xfail(strict=True, reason="no power with a rational exponent is evaluated")
def test_a_square_root_that_is_rational():
    assert evaluate(Pow, numbers(4, Rational(1, 2))) == NumberKind(2)


@pytest.mark.xfail(strict=True, reason="the size of a product is estimated from its factors before they cancel")
def test_a_small_product_of_large_factors_that_cancel():
    large = 2**MAX_BITS
    assert evaluate(Mul, numbers(large, large, Rational(1, large))) == NumberKind(large)


@pytest.mark.xfail(strict=True, reason="the size of a sum is estimated as if no denominator divided another")
def test_a_small_sum_of_rationals_with_one_large_denominator():
    large = 2**MAX_BITS
    assert evaluate(Add, numbers(Rational(1, large), Rational(1, large))) == Rational(2, large)

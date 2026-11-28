from fractions import Fraction

import pytest

from nary import (
    Add, BoolKind, E, Eq, Ge, Gt, Le, Lt, Many, Mul, Ne, NumberKind, Pow, Rational,
    declare_function, declare_kind, log, re, sin,
)
from nary.calculus import NumberFunction
from nary.properties import declare_properties, declare_property, is_property
from nary._numbers import MAX_BITS
from nary.logic import false, true
from nary.normalising import normalise


Max = declare_function(
    "EvalMax", Many(NumberKind), returns=NumberKind, domain=true, evaluate_literals=max,
)
declare_properties(Max, is_associative=True, is_commutative=True)
First = declare_function(
    "EvalFirst", Many(NumberKind), returns=NumberKind, domain=true,
    evaluate_literals=lambda first, *rest: first,
)
declare_properties(First, is_associative=True)


def test_a_sum_of_integers():
    assert normalise(Add(2, 3, -7)) == NumberKind(-2)


def test_a_sum_of_rationals():
    assert normalise(Add(Rational(1, 2), Rational(1, 3))) == Rational(5, 6)


def test_a_sum_of_an_integer_and_a_rational():
    assert normalise(Add(3, Rational(-1, 2))) == Rational(5, 2)


def test_a_sum_of_rationals_that_is_an_integer_is_the_integer_literal():
    result = normalise(Add(Rational(1, 2), Rational(1, 2)))
    assert repr(result) == "1" and type(result.value) is int


def test_a_sum_of_no_arguments_is_zero():
    assert normalise(Add()) == NumberKind(0)


def test_a_sum_of_one_argument_is_that_argument():
    assert normalise(Add(Rational(1, 2))) == Rational(1, 2)


def test_a_product_of_integers():
    assert normalise(Mul(2, -3, 4)) == NumberKind(-24)


def test_a_product_of_rationals():
    assert normalise(Mul(Rational(2, 3), Rational(3, 4))) == Rational(1, 2)


def test_a_product_of_an_integer_and_a_rational():
    assert normalise(Mul(3, Rational(1, 2))) == Rational(3, 2)


def test_a_product_of_rationals_that_is_an_integer_is_the_integer_literal():
    result = normalise(Mul(4, Rational(1, 2)))
    assert repr(result) == "2" and type(result.value) is int


def test_a_product_of_no_arguments_is_one():
    assert normalise(Mul()) == NumberKind(1)


def test_a_product_with_zero_is_zero():
    assert normalise(Mul(0, Rational(1, 2))) == NumberKind(0)


def test_an_integer_to_a_positive_integer_power():
    assert normalise(Pow(2, 10)) == NumberKind(1024)


def test_an_integer_to_a_negative_integer_power_is_a_rational():
    assert normalise(Pow(2, -1)) == Rational(1, 2)


def test_a_negative_integer_to_a_negative_integer_power_has_its_sign_on_the_numerator():
    assert repr(normalise(Pow(-2, -1))) == "Rational(-1, 2)"


def test_a_rational_to_a_positive_integer_power():
    assert normalise(Pow(Rational(-2, 3), 3)) == Rational(-8, 27)


def test_a_rational_to_a_negative_integer_power():
    assert normalise(Pow(Rational(-2, 3), -3)) == Rational(-27, 8)


def test_a_rational_to_a_negative_integer_power_that_is_an_integer_is_the_integer_literal():
    result = normalise(Pow(Rational(1, 2), -2))
    assert repr(result) == "4" and type(result.value) is int


def test_a_nonzero_number_to_the_power_zero_is_one():
    assert normalise(Pow(Rational(7, 2), 0)) == NumberKind(1)


def test_zero_to_a_positive_integer_power_is_zero():
    assert normalise(Pow(0, 3)) == NumberKind(0)


def test_zero_to_the_power_zero_has_no_value():
    assert normalise(Pow(0, 0)) == Pow(0, 0)


def test_zero_to_a_negative_integer_power_has_no_value():
    assert normalise(Pow(0, -1)) == Pow(0, -1)


def test_zero_to_a_negative_rational_power_has_no_value():
    assert normalise(Pow(0, Rational(-1, 2))) == Pow(0, Rational(-1, 2))


def test_a_square_root_that_is_not_rational_is_left_alone():
    assert normalise(Pow(2, Rational(1, 2))) == Pow(2, Rational(1, 2))


def test_a_square_root_that_is_rational_is_left_alone_too():
    assert normalise(Pow(4, Rational(1, 2))) == Pow(4, Rational(1, 2))


def test_a_rational_power_of_a_rational_is_left_alone():
    assert normalise(Pow(Rational(4, 9), Rational(-3, 2))) == Pow(Rational(4, 9), Rational(-3, 2))


def test_the_real_part_of_an_integer():
    assert normalise(re(-3)) == NumberKind(-3)


def test_the_real_part_of_a_rational():
    assert normalise(re(Rational(1, 2))) == Rational(1, 2)


def test_equal_numbers_are_equal():
    assert normalise(Eq(Rational(1, 2), Rational(1, 2))) == true


def test_different_numbers_are_not_equal():
    assert normalise(Eq(Rational(1, 2), Rational(1, 3))) == false


def test_ne_of_different_numbers():
    assert normalise(Ne(1, Rational(1, 2))) == true


def test_ne_of_equal_numbers():
    assert normalise(Ne(2, 2)) == false


def test_lt_between_rationals_with_different_denominators():
    assert normalise(Lt(Rational(1, 3), Rational(1, 2))) == true


def test_lt_of_equal_numbers():
    assert normalise(Lt(2, 2)) == false


def test_gt_between_a_negative_rational_and_zero():
    assert normalise(Gt(Rational(-1, 2), 0)) == false


def test_le_of_equal_numbers():
    assert normalise(Le(Rational(1, 2), Rational(1, 2))) == true


def test_ge_between_an_integer_and_a_larger_rational():
    assert normalise(Ge(1, Rational(3, 2))) == false


def test_rationals_that_differ_only_far_from_the_leading_digits_are_compared_exactly():
    assert normalise(Lt(Rational(10**30, 10**30 + 1), Rational(10**30 + 1, 10**30 + 2))) == true


def test_a_symbol_among_the_arguments_gives_none():
    assert normalise(Add(1, NumberKind("x"))) == Add(1, NumberKind("x"))


def test_a_constant_among_the_arguments_gives_none():
    assert normalise(Mul(2, E)) == Mul(2, E)


def test_an_argument_that_becomes_a_literal_is_evaluated_first():
    assert normalise(Add(1, Mul(2, 3))) == NumberKind(7)


def test_literals_of_a_head_without_evaluate_literals_are_left_alone():
    Float = declare_kind("FloatForEvaluation", literals=float)
    Total = declare_function("FloatTotal", Many(Float), returns=Float, domain=true)
    declare_properties(Total, is_associative=True, is_commutative=True)
    assert normalise(Total(Float(0.5), Float(0.5))) == Total(Float(0.5), Float(0.5))


def test_a_head_that_is_not_evaluated_gives_none():
    assert normalise(sin(0)) == sin(0)


def test_the_largest_power_of_two_that_is_computed():
    assert normalise(Pow(2, MAX_BITS)) == NumberKind(2**MAX_BITS)


def test_a_power_above_the_size_limit_is_left_alone():
    assert normalise(Pow(2, MAX_BITS + 1)) == Pow(2, MAX_BITS + 1)


def test_a_power_with_a_denominator_above_the_size_limit_is_left_alone():
    assert normalise(Pow(2, -MAX_BITS - 1)) == Pow(2, -MAX_BITS - 1)


def test_a_power_of_a_rational_above_the_size_limit_is_left_alone():
    assert normalise(Pow(Rational(3, 2), MAX_BITS)) == Pow(Rational(3, 2), MAX_BITS)


def test_a_power_with_an_enormous_exponent_is_left_alone_without_being_computed():
    assert normalise(Pow(3, 10**100)) == Pow(3, 10**100)


def test_one_to_an_enormous_power_is_one():
    assert normalise(Pow(1, 10**100)) == NumberKind(1)


def test_minus_one_to_an_enormous_odd_power_is_minus_one():
    assert normalise(Pow(-1, -(10**100) - 1)) == NumberKind(-1)


def test_zero_to_an_enormous_power_is_zero():
    assert normalise(Pow(0, 10**100)) == NumberKind(0)


def test_the_largest_product_of_two_powers_of_two_that_is_computed():
    half = MAX_BITS // 2
    assert normalise(Mul(2**half, 2**half)) == NumberKind(2**MAX_BITS)


def test_a_product_above_the_size_limit_is_left_alone():
    half = MAX_BITS // 2
    assert normalise(Mul(2**half, 2 ** (half + 1))) == Mul(2**half, 2 ** (half + 1))


def test_a_product_with_a_denominator_above_the_size_limit_is_left_alone():
    half = MAX_BITS // 2
    product = Mul(Rational(1, 2**half), Rational(1, 2 ** (half + 1)))
    assert normalise(product) == product


def test_a_product_of_many_copies_of_a_large_literal_is_left_alone():
    assert normalise(Mul(*[2**13_000] * 4096)) == Mul(*[2**13_000] * 4096)


def test_the_largest_sum_of_two_powers_of_two_that_is_computed():
    assert normalise(Add(2 ** (MAX_BITS - 1), 2 ** (MAX_BITS - 1))) == NumberKind(2**MAX_BITS)


def test_a_sum_above_the_size_limit_is_left_alone():
    assert normalise(Add(2**MAX_BITS, 1)) == Add(1, 2**MAX_BITS)


def test_a_sum_with_a_denominator_above_the_size_limit_is_left_alone():
    half = MAX_BITS // 2
    total = Add(Rational(1, 2**half + 1), Rational(1, 2**half + 3))
    assert normalise(total) == total


def test_a_sum_of_more_integers_than_the_size_limit_is_computed():
    assert normalise(Add(*[1] * (MAX_BITS + 1))) == NumberKind(MAX_BITS + 1)


def test_a_result_at_the_size_limit_still_has_a_repr():
    assert len(repr(normalise(Pow(2, MAX_BITS)))) == 4215


def test_a_power_of_a_fraction_with_a_denominator_above_the_size_limit_is_left_alone():
    assert normalise(Pow(Rational(1, 2), MAX_BITS + 1)) == Pow(Rational(1, 2), MAX_BITS + 1)


def test_gt_of_equal_numbers_is_false():
    assert normalise(Gt(2, 2)) == false


def test_ge_of_equal_numbers_is_true():
    assert normalise(Ge(2, 2)) == true


def test_zero_does_not_absorb_zero_to_the_power_zero():
    assert normalise(Mul(0, Pow(0, 0))) == Mul(0, Pow(0, 0))


def test_zero_absorbs_a_square():
    assert normalise(Mul(0, Pow(NumberKind("x"), 2))) == NumberKind(0)


def test_evaluate_literals_of_add_gives_the_literal_of_the_sum():
    assert Add.evaluate_literals(NumberKind(2), NumberKind(3)) == NumberKind(5)


def test_evaluate_literals_takes_python_numbers_as_calling_the_function_does():
    assert Add.evaluate_literals(2, 3) == NumberKind(5)


def test_evaluate_literals_of_a_comparison_gives_true():
    assert Lt.evaluate_literals(NumberKind(1), NumberKind(2)) == true


def test_evaluate_literals_of_pow_gives_an_integer_literal():
    result = Pow.evaluate_literals(2, 3)
    assert repr(result) == "8" and type(result.value) is int


def test_evaluate_literals_gives_none_where_the_declared_function_gives_none():
    assert Pow.evaluate_literals(NumberKind(0), NumberKind(-1)) is None


def test_evaluate_literals_gives_none_for_an_argument_that_is_not_a_literal():
    assert Add.evaluate_literals(NumberKind("x"), 3) is None


def test_evaluate_literals_rejects_an_argument_of_another_kind_as_calling_the_function_does():
    with pytest.raises(TypeError, match="^Add expects NumberKind, got BoolKind: true$"):
        Add.evaluate_literals(true, 3)


def test_sin_does_not_declare_how_its_literals_compute():
    assert sin.evaluate_literals is None


def test_a_freshly_declared_function_evaluates_literals_with_the_function_it_was_given():
    Smallest = declare_function(
        "EvalSmallest", Many(NumberKind), returns=NumberKind, domain=true, evaluate_literals=min,
    )
    assert Smallest.evaluate_literals(NumberKind(2), NumberKind(3)) == NumberKind(2)


def test_a_function_declared_without_evaluate_literals_has_none():
    Plain = declare_function("EvalPlain", NumberKind, returns=NumberKind, domain=true)
    assert Plain.evaluate_literals is None


def test_a_function_that_is_a_symbol_has_no_evaluate_literals():
    assert NumberFunction("f").evaluate_literals is None


def test_evaluate_literals_must_be_a_function():
    with pytest.raises(TypeError, match="^evaluate_literals of EvalFive must be a function, got 5$"):
        declare_function("EvalFive", NumberKind, returns=NumberKind, domain=true, evaluate_literals=5)


def test_evaluate_literals_is_not_among_the_properties_of_add():
    assert "evaluate_literals" not in Add.properties


def test_evaluate_literals_is_not_a_property():
    assert not is_property("evaluate_literals")


def test_evaluate_literals_cannot_be_declared_as_a_property():
    with pytest.raises(ValueError, match="^evaluate_literals is already an attribute of Expr$"):
        declare_property("evaluate_literals")


def test_evaluate_literals_cannot_be_given_to_declare_properties():
    Late = declare_function("EvalLate", NumberKind, returns=NumberKind, domain=true)
    with pytest.raises(TypeError, match="^evaluate_literals is not a property$"):
        declare_properties(Late, evaluate_literals=abs)


def test_a_freshly_declared_head_of_three_arguments_is_evaluated():
    Clamp = declare_function(
        "EvalClamp", NumberKind, NumberKind, NumberKind, returns=NumberKind, domain=true,
        evaluate_literals=lambda low, value, high: min(max(low, value), high),
    )
    assert normalise(Clamp(0, 7, 5)) == NumberKind(5)


def test_a_freshly_declared_maximum_of_two_numbers_is_the_larger():
    assert normalise(Max(2, 3)) == NumberKind(3)


def test_a_freshly_declared_maximum_combines_its_numbers_beside_a_symbol():
    assert normalise(Max(NumberKind("x"), 2, 3)) == Max(3, NumberKind("x"))


def test_a_freshly_declared_head_of_one_argument_is_evaluated():
    Negate = declare_function(
        "EvalNegate", NumberKind, returns=NumberKind, domain=true,
        evaluate_literals=lambda value: -value,
    )
    assert normalise(Negate(Rational(1, 2))) == Rational(-1, 2)


def test_a_freshly_declared_head_of_one_argument_is_left_alone_on_a_symbol():
    Opposite = declare_function(
        "EvalOpposite", NumberKind, returns=NumberKind, domain=true,
        evaluate_literals=lambda value: -value,
    )
    assert normalise(Opposite(NumberKind("x"))) == Opposite(NumberKind("x"))


def test_a_head_of_one_argument_without_evaluate_literals_keeps_its_argument():
    Wrap = declare_function("EvalWrap", NumberKind, returns=NumberKind, domain=true)
    assert normalise(Wrap(2)) == Wrap(2)


def test_neighbouring_numbers_of_a_freshly_declared_head_that_is_not_commutative_are_combined():
    x = NumberKind("x")
    assert normalise(First(x, 2, 3)) == First(x, 2)


def test_numbers_of_a_head_that_is_not_commutative_are_not_combined_across_a_symbol():
    x = NumberKind("x")
    assert normalise(First(2, x, 3)) == First(2, x, 3)


def test_a_freshly_declared_head_may_give_none_to_leave_its_literals():
    Ratio = declare_function(
        "EvalRatio", NumberKind, NumberKind, returns=NumberKind, domain=true,
        evaluate_literals=lambda a, b: Fraction(a) / b if b else None,
    )
    assert (normalise(Ratio(1, 2)), normalise(Ratio(1, 0))) == (Rational(1, 2), Ratio(1, 0))


def test_a_freshly_declared_comparison_gives_a_result_of_another_kind():
    Divides = declare_function(
        "EvalDivides", NumberKind, NumberKind, returns=BoolKind, domain=true,
        evaluate_literals=lambda a, b: b % a == 0,
    )
    assert (normalise(Divides(3, 6)), normalise(Divides(4, 6))) == (true, false)


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


def test_normalise_adds_the_numbers_among_the_arguments_of_a_sum():
    x = NumberKind("x")
    assert normalise(Add(x, 1, 2)) == Add(3, x)


def test_normalise_multiplies_the_numbers_among_the_arguments_of_a_product():
    x = NumberKind("x")
    assert normalise(Mul(2, x, Rational(1, 2))) == x


@pytest.mark.xfail(strict=True, reason="no power with a rational exponent is evaluated")
def test_a_square_root_that_is_rational():
    assert normalise(Pow(4, Rational(1, 2))) == NumberKind(2)


@pytest.mark.xfail(strict=True, reason="the size of a product is estimated from its factors before they cancel")
def test_a_small_product_of_large_factors_that_cancel():
    large = 2**MAX_BITS
    assert normalise(Mul(large, large, Rational(1, large))) == NumberKind(large)


@pytest.mark.xfail(strict=True, reason="the size of a sum is estimated as if no denominator divided another")
def test_a_small_sum_of_rationals_with_one_large_denominator():
    large = 2**MAX_BITS
    assert normalise(Add(Rational(1, large), Rational(1, large))) == Rational(2, large)


def test_a_fraction_with_denominator_one_becomes_an_integer_literal():
    Halve = declare_function(
        "EvalHalve", NumberKind, returns=NumberKind, domain=true,
        evaluate_literals=lambda value: Fraction(value, 2),
    )
    result = normalise(Halve(4))
    assert repr(result) == "2" and type(result.value) is int


def test_a_freshly_declared_maximum_over_a_fresh_kind_gives_a_literal_of_that_kind():
    Count = declare_kind("EvalCount", literals=(int,))
    CountMax = declare_function(
        "EvalCountMax", Many(Count), returns=Count, domain=true, evaluate_literals=max,
    )
    declare_properties(CountMax, is_associative=True, is_commutative=True)
    result = normalise(CountMax(Count(2), Count(3)))
    assert (result, result.kind) == (Count(3), Count) and result != NumberKind(3)


def test_a_symbol_among_the_arguments_of_a_head_that_is_not_associative_is_left_alone():
    Ratio = declare_function(
        "EvalRatioOfSymbol", NumberKind, NumberKind, returns=NumberKind, domain=true,
        evaluate_literals=lambda a, b: Fraction(a) / b,
    )
    assert normalise(Ratio(NumberKind("x"), 2)) == Ratio(NumberKind("x"), 2)


def test_literals_of_two_kinds_are_both_passed_as_their_values():
    Count = declare_kind("EvalRepeats", literals=(int,))
    Repeat = declare_function(
        "EvalRepeat", NumberKind, Count, returns=NumberKind, domain=true,
        evaluate_literals=lambda number, times: number * times,
    )
    assert normalise(Repeat(Rational(1, 2), Count(4))) == NumberKind(2)


def test_a_literal_of_another_kind_cannot_be_an_argument_of_add():
    Count = declare_kind("EvalTally", literals=(int,))
    with pytest.raises(TypeError, match="^Add expects NumberKind, got EvalTally: 3$"):
        Add(Count(3), 2)


def test_an_error_raised_by_evaluate_literals_propagates():
    Quotient = declare_function(
        "EvalQuotient", NumberKind, NumberKind, returns=NumberKind, domain=true,
        evaluate_literals=lambda a, b: a // b,
    )
    with pytest.raises(ZeroDivisionError):
        normalise(Quotient(1, 0))

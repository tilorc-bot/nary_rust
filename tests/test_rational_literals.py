from fractions import Fraction

import pytest

from nary import Add, E, Many, Mul, NumberKind, Pow, Rational, declare_function, declare_kind, sin
from nary.arithmetic_rules import rules
from nary.lean import to_lean
from nary.logic import true
from nary.normalising import normalise
from nary.rewriting import _has_a_value, rewrite
from nary.rules import rule


def test_a_fraction_makes_a_literal_of_number_kind():
    half = NumberKind(Fraction(1, 2))
    assert (half.is_literal, half.is_atom, half.kind) == (True, True, NumberKind)


def test_value_is_the_fraction():
    assert NumberKind(Fraction(1, 2)).value == Fraction(1, 2)


def test_numerator_and_denominator_are_read_from_the_value():
    value = NumberKind(Fraction(3, 4)).value
    assert (value.numerator, value.denominator) == (3, 4)


def test_numerator_and_denominator_of_an_integer_literal_are_read_the_same_way():
    value = NumberKind(3).value
    assert (value.numerator, value.denominator) == (3, 1)


def test_rational_makes_a_literal_of_number_kind():
    half = Rational(1, 2)
    assert (half.is_literal, half.kind, half.value) == (True, NumberKind, Fraction(1, 2))


def test_rational_is_equal_to_the_literal_made_from_the_fraction():
    assert Rational(1, 2) == NumberKind(Fraction(1, 2))


def test_rational_is_in_lowest_terms():
    assert Rational(2, 4) == Rational(1, 2)


def test_rational_with_denominator_one_is_the_integer_literal():
    assert Rational(4, 2) == NumberKind(2)


def test_rational_with_denominator_zero_raises():
    with pytest.raises(ZeroDivisionError):
        Rational(1, 0)


def test_repr_of_a_rational_literal():
    assert repr(NumberKind(Fraction(3, 4))) == "Rational(3, 4)"


def test_repr_of_a_negative_rational_literal():
    assert repr(NumberKind(Fraction(-3, 4))) == "Rational(-3, 4)"


def test_repr_of_a_rational_literal_too_long_to_print_raises_as_it_does_for_an_integer():
    with pytest.raises(ValueError, match="^Exceeds the limit"):
        repr(NumberKind(Fraction(10**5000 + 1, 10**5000)))


def test_repr_of_a_fraction_literal_of_another_kind_is_the_repr_of_the_fraction():
    Real = declare_kind("Real", literals=(int, float, Fraction))
    Plus = declare_function("Plus", Many(Real), returns=Real, domain=true)
    r = Real("r")
    e = Plus(r, Fraction(1, 2))
    assert repr(e) == "Plus(r, Fraction(1, 2))" and eval(repr(e)) == e


def test_repr_of_an_expression_evaluates_to_the_expression():
    names = {}
    exec("from nary import *", names)
    e = Add(sin(E), Mul(Fraction(-1, 2), Pow(E, Fraction(3, 4))))
    assert repr(e) == "Add(sin(E), Mul(Rational(-1, 2), Pow(E, Rational(3, 4))))"
    assert eval(repr(e), names) == e


def test_lowest_terms():
    assert repr(NumberKind(Fraction(2, 4))) == "Rational(1, 2)"


def test_a_negative_denominator_moves_its_sign_to_the_numerator():
    assert repr(NumberKind(Fraction(1, -2))) == "Rational(-1, 2)"


def test_denominator_one_is_the_integer_literal():
    two = NumberKind(Fraction(2, 1))
    assert two == NumberKind(2) and hash(two) == hash(NumberKind(2))
    assert repr(two) == "2" and type(two.value) is int


def test_a_fraction_that_reduces_to_denominator_one_is_the_integer_literal():
    assert NumberKind(Fraction(6, 3)) == NumberKind(2)


def test_a_fraction_argument_with_denominator_one_is_the_integer_literal():
    x = NumberKind("x")
    assert Add(x, Fraction(2, 1)) == Add(x, 2)


def test_denominator_one_stays_a_fraction_in_a_kind_without_int_literals():
    OnlyFractions = declare_kind("OnlyFractions", literals=Fraction)
    assert repr(OnlyFractions(Fraction(2, 1))) == "Fraction(2, 1)"


def test_zero_denominator_raises():
    with pytest.raises(ZeroDivisionError):
        NumberKind(Fraction(1, 0))


def test_a_fraction_is_accepted_as_an_argument():
    x = NumberKind("x")
    assert Add(x, Fraction(1, 2)).args == (x, NumberKind(Fraction(1, 2)))


def test_a_fraction_is_accepted_on_the_left_of_an_operator():
    x = NumberKind("x")
    assert Fraction(1, 2) * x == Mul(Fraction(1, 2), x)


def test_a_fraction_is_accepted_as_the_replacement_of_a_rule():
    x = NumberKind("x")
    halve = rule(Mul(x, Pow(2, -1)), Mul(Fraction(1, 2), x))
    assert rewrite(sin(x) / 2, [halve]) == Mul(Fraction(1, 2), sin(x))


def test_a_float_is_still_rejected():
    with pytest.raises(TypeError, match="^NumberKind takes .* literal of type int or Fraction, got float: 0.5$"):
        NumberKind(0.5)


def test_a_float_argument_is_still_rejected():
    with pytest.raises(TypeError, match="^Add expects NumberKind, got float: 0.5$"):
        Add(NumberKind("x"), 0.5)


def test_a_subclass_of_fraction_is_rejected_as_bool_is_for_int():
    class Ratio(Fraction):
        pass

    with pytest.raises(TypeError, match="^NumberKind takes .*, got Ratio: Ratio\\(1, 2\\)$"):
        NumberKind(Ratio(1, 2))


def test_equal_fractions_are_equal_literals_with_equal_hashes():
    a, b = NumberKind(Fraction(1, 2)), NumberKind(Fraction(2, 4))
    assert a == b and hash(a) == hash(b)


def test_equality_and_hash_with_a_large_numerator_and_denominator():
    a = NumberKind(Fraction(10**40 + 1, 10**50 + 7))
    b = NumberKind(Fraction(3 * (10**40 + 1), 3 * (10**50 + 7)))
    assert a == b and hash(a) == hash(b)


def test_fractions_that_differ_only_far_from_the_leading_digits_are_not_equal():
    assert NumberKind(Fraction(10**40 + 1, 10**50 + 7)) != NumberKind(Fraction(10**40 + 1, 10**50 + 9))


def test_a_rational_literal_is_not_equal_to_its_fraction():
    assert (NumberKind(Fraction(1, 2)) == Fraction(1, 2)) is False


def test_a_rational_literal_is_not_equal_to_the_division_tree():
    assert NumberKind(Fraction(1, 2)) != Mul(1, Pow(2, -1))


def test_rational_literals_work_as_set_members():
    assert len({NumberKind(Fraction(1, 2)), NumberKind(Fraction(2, 4)), NumberKind(Fraction(1, 3))}) == 2


def test_adding_two_rational_literals_is_not_simplified_at_construction():
    assert repr(Add(Fraction(1, 2), Fraction(1, 2))) == "Add(Rational(1, 2), Rational(1, 2))"


def test_the_division_tree_is_not_turned_into_a_rational_literal():
    assert repr(Mul(3, Pow(2, -1))) == "Mul(3, Pow(2, -1))"


def test_dividing_integer_literals_still_builds_the_division_tree():
    assert repr(NumberKind(3) / 2) == "Mul(3, Pow(2, -1))"


def test_dividing_by_a_rational_literal_builds_a_tree():
    x = NumberKind("x")
    assert repr(x / Fraction(1, 2)) == "Mul(x, Pow(Rational(1, 2), -1))"


def test_negating_a_rational_literal_builds_a_tree():
    assert repr(-NumberKind(Fraction(1, 2))) == "Mul(-1, Rational(1, 2))"


def test_to_lean():
    assert to_lean(NumberKind(Fraction(1, 2))) == "Nary.rat (1/2)"


def test_to_lean_of_a_negative_rational_literal():
    assert to_lean(NumberKind(Fraction(-1, 2))) == "Nary.rat (-1/2)"


def test_to_lean_as_an_argument():
    x = NumberKind("x")
    assert to_lean(Pow(x, Fraction(1, 2))) == "Nary.Pow (some x) (Nary.rat (1/2))"


def test_a_rational_literal_has_a_value():
    assert _has_a_value(NumberKind(Fraction(1, 2)), lambda condition: False)


def test_normalise_removes_the_identity_of_mul():
    assert normalise(Mul(1, Fraction(1, 2))) == NumberKind(Fraction(1, 2))


def test_normalise_removes_the_identity_of_add():
    assert normalise(Add(0, Fraction(1, 2))) == NumberKind(Fraction(1, 2))


def test_normalise_lets_zero_absorb_a_rational_literal():
    assert normalise(Mul(0, Fraction(1, 2))) == NumberKind(0)


def test_normalise_adds_rational_literals():
    assert normalise(Add(Rational(1, 2), Rational(1, 2))) == NumberKind(1)


def test_normalise_orders_rational_literals_by_repr():
    x = NumberKind("x")
    e = normalise(Add(x, Fraction(1, 3), 2, Fraction(1, 2)))
    assert repr(e) == "Add(2, Rational(1, 2), Rational(1, 3), x)"


def test_normalise_gives_the_same_result_for_any_order_of_arguments():
    x = NumberKind("x")
    assert normalise(Mul(x, Fraction(1, 2), 3)) == normalise(Mul(3, Fraction(1, 2), x))


def test_rewrite_removes_the_identity_of_mul():
    assert rewrite(Mul(Fraction(1, 2), 1), rules) == NumberKind(Fraction(1, 2))


def test_rewrite_does_not_treat_a_rational_exponent_as_the_exponent_one():
    x = NumberKind("x")
    assert rewrite(Pow(x, Fraction(1, 2)), rules) == Pow(x, Fraction(1, 2))


def test_rewrite_does_not_cancel_against_a_power_with_a_rational_exponent():
    x = NumberKind("x")
    e = Mul(x, Pow(x, Fraction(-1, 2)))
    assert rewrite(e, rules, known=lambda condition: True) == e


@pytest.mark.xfail(strict=True, reason="arguments are sorted by repr, and 'E' comes before 'Rational(1, 2)'")
def test_normalise_puts_a_rational_literal_before_a_constant_as_it_does_an_integer():
    assert normalise(Mul(E, Fraction(1, 2))).args[0] == NumberKind(Fraction(1, 2))

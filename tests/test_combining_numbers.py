from fractions import Fraction
from math import prod

import pytest

from nary import Add, Many, Mul, NumberKind, Pow, Rational, declare_function, log
from nary._numbers import MAX_BITS
from nary.logic import true
from nary.normalising import normalise
from nary.properties import declare_properties

x, y, z = (NumberKind(name) for name in "xyz")


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
    raise ValueError(e)


POINTS = [{x: Fraction(a), y: Fraction(b), z: Fraction(c)} for a, b, c in [(2, -3, 5), (-1, 7, 0), (4, 4, -2)]]


def test_normalise_adds_the_numbers_beside_a_symbol():
    assert normalise(Add(x, 1, 2)) == Add(3, x)


def test_normalise_adds_numbers_from_every_level_of_a_nested_sum():
    assert normalise(Add(y, Add(x, Add(2, 3)))) == Add(5, x, y)


def test_normalise_multiplies_the_numbers_beside_a_symbol():
    assert normalise(Mul(2, x, 3)) == Mul(6, x)


def test_numbers_that_add_up_to_zero_leave_the_other_arguments():
    assert normalise(Add(x, 2, -2, y)) == Add(x, y)


def test_numbers_that_multiply_to_one_leave_the_one_other_argument():
    assert normalise(Mul(Rational(2, 3), x, Rational(3, 2))) == x


def test_numbers_that_multiply_to_zero_absorb_a_symbol():
    assert normalise(Mul(2, x, 0)) == NumberKind(0)


def test_numbers_that_multiply_to_zero_keep_an_argument_that_may_have_no_value():
    assert normalise(Mul(2, log(x), 0)) == Mul(0, log(x))


def test_numbers_are_added_after_an_inner_head_is_removed():
    assert normalise(Add(1, Mul(1, Add(2, x)))) == Add(3, x)


def test_the_order_of_the_arguments_does_not_change_the_result():
    assert normalise(Add(1, x, Rational(1, 2), y, 2)) == normalise(Add(y, 2, x, 1, Rational(1, 2)))


def test_normalising_twice_is_normalising_once():
    once = normalise(Mul(Add(x, 1, 1), 3, Add(2, y, -5), 2))
    assert normalise(once) == once


def test_a_sum_above_the_size_limit_is_left_as_written():
    large = NumberKind(2**MAX_BITS)
    assert normalise(Add(large, large, x)) == Add(large, large, x)


def test_a_product_above_the_size_limit_is_left_as_written():
    large = NumberKind(2**13_000)
    assert normalise(Mul(large, x, large)) == Mul(large, large, x)


def test_one_number_beside_an_argument_that_sorts_before_it_is_left():
    assert normalise(Mul(Rational(1, 4), Pow(x, 2))) == Mul(Pow(x, 2), Rational(1, 4))


def test_a_power_is_not_combined_with_the_numbers_beside_it():
    assert normalise(Mul(2, Pow(x, 2), 3)) == Mul(6, Pow(x, 2))


def test_numbers_of_a_freshly_declared_head_without_value_of_literals_are_not_combined():
    Total = declare_function("NumbersTotal", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Total, is_associative=True, is_commutative=True, identity_element=0)
    assert normalise(Total(x, 1, 2)) == Total(1, 2, x)


@pytest.mark.parametrize("e", [
    Add(x, 1, 2, Mul(3, y, Rational(1, 2))),
    Mul(Add(x, 2, 3), 4, Add(Rational(1, 3), y, Rational(2, 3))),
    Add(Mul(2, x, 0), z, 7, -7),
])
def test_normalising_keeps_the_value(e):
    for at in POINTS:
        assert value(normalise(e), at) == value(e, at)

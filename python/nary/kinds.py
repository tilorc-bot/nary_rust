from fractions import Fraction

from ._core import Many, _print_fractions_as_rational, declare_kind

__all__ = ["BoolKind", "Many", "NumberKind", "Rational"]

NumberKind = declare_kind("NumberKind", literals=(int, Fraction))
_print_fractions_as_rational(NumberKind)
BoolKind = declare_kind("BoolKind")


def Rational(numerator, denominator):
    """
    Args:
        numerator: An int.
        denominator: An int that is not 0.

    Returns:
        The literal of NumberKind whose value is Fraction(numerator, denominator).

    >>> Rational(2, 4), Rational(4, 2), Rational(1, -2)
    (Rational(1, 2), 2, Rational(-1, 2))
    >>> Rational(1, 2).value
    Fraction(1, 2)
    """
    return NumberKind(Fraction(numerator, denominator))

from fractions import Fraction

from ._core import Many, declare_kind

__all__ = ["BoolKind", "Many", "NumberKind", "Rational"]

NumberKind = declare_kind("NumberKind", literals=(int, Fraction))
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

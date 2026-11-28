"""Exact arithmetic on the values of number literals, giving None above the size limit."""

from fractions import Fraction
from math import prod

__all__ = ["MAX_BITS", "exact_power", "exact_product", "exact_sum"]

MAX_BITS = 14_000


def exact_sum(*terms):
    """The sum of terms.

    Args:
        *terms: Ints and Fractions.

    Returns:
        An int or Fraction, or None if a numerator or denominator may be above 2**MAX_BITS.

    >>> from fractions import Fraction
    >>> exact_sum(2, Fraction(1, 2)), exact_sum(2**MAX_BITS, 1)
    (Fraction(5, 2), None)
    """
    bits_of_largest_numerator = max((_bits(term.numerator) for term in terms), default=0)
    bits_of_denominators = sum(_bits(term.denominator) for term in terms)
    if _bits(len(terms)) + bits_of_largest_numerator + bits_of_denominators > MAX_BITS:
        return None
    return sum(terms)


def exact_product(*factors):
    """The product of factors.

    Args:
        *factors: Ints and Fractions.

    Returns:
        An int or Fraction, or None if a numerator or denominator may be above 2**MAX_BITS.

    >>> from fractions import Fraction
    >>> exact_product(2, Fraction(1, 2)), exact_product(2**MAX_BITS, 2)
    (Fraction(1, 1), None)
    """
    bits_of_numerators = sum(_bits(factor.numerator) for factor in factors)
    bits_of_denominators = sum(_bits(factor.denominator) for factor in factors)
    if max(bits_of_numerators, bits_of_denominators) > MAX_BITS:
        return None
    return prod(factors)


def exact_power(base, exponent):
    """base**exponent.

    Args:
        base: An int or Fraction.
        exponent: An int or Fraction.

    Returns:
        An int or Fraction. None where base**exponent has no value (0**0, 0**-1), where
        exponent is not an integer, or where a numerator or denominator may be above 2**MAX_BITS.

    >>> from fractions import Fraction
    >>> exact_power(Fraction(1, 2), 2), exact_power(2, -1)
    (Fraction(1, 4), Fraction(1, 2))
    >>> exact_power(0, 0), exact_power(0, -1), exact_power(4, Fraction(1, 2))
    (None, None, None)
    >>> exact_power(2, MAX_BITS + 1), exact_power(Fraction(1, 2), MAX_BITS + 1)
    (None, None)
    """
    if exponent.denominator != 1 or (base == 0 and exponent <= 0):
        return None
    if abs(exponent) * max(_bits(base.numerator), _bits(base.denominator)) > MAX_BITS:
        return None
    return Fraction(base) ** exponent


def _bits(n):
    """The least b with abs(n) <= 2**b.

    >>> [_bits(n) for n in (0, 1, -2, 3, 4, 5)]
    [0, 0, 1, 2, 2, 3]
    """
    return (abs(n) - 1).bit_length() if n else 0

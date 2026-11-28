"""Exact arithmetic on number literals."""

import operator
from fractions import Fraction
from math import prod

from .arithmetic import Add, Mul, Pow
from .kinds import NumberKind
from .logic import false, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re

__all__ = ["MAX_BITS", "evaluate"]

MAX_BITS = 14_000
_COMPARISONS = {
    Eq: operator.eq, Ne: operator.ne, Lt: operator.lt,
    Gt: operator.gt, Le: operator.le, Ge: operator.ge,
}


def evaluate(head, args):
    """The literal that head(*args) is equal to, or None to leave head(*args) as written.

    Args:
        head: A function. Add, Mul, Pow, re, Eq, Ne, Lt, Gt, Le and Ge are evaluated.
        args: Its arguments. Unless each is a literal of NumberKind, the result is None.

    Returns:
        A literal of NumberKind, or true or false for a comparison. None where head(*args)
        has no value, is not rational, or has a numerator or denominator that may be
        above 2**MAX_BITS.

    >>> from nary import Add, Lt, Mul, NumberKind, Pow, Rational
    >>> half, zero, two, x = Rational(1, 2), NumberKind(0), NumberKind(2), NumberKind("x")
    >>> evaluate(Add, [half, two]), evaluate(Mul, [half, two]), evaluate(Pow, [half, two])
    (Rational(5, 2), 1, Rational(1, 4))
    >>> evaluate(Lt, [half, two]), evaluate(Pow, [two, NumberKind(-1)])
    (true, Rational(1, 2))
    >>> evaluate(Pow, [zero, zero]), evaluate(Pow, [two, half]), evaluate(Mul, [two, x])
    (None, None, None)
    >>> evaluate(Pow, [two, NumberKind(MAX_BITS)]) == NumberKind(2**MAX_BITS)
    True
    >>> evaluate(Pow, [two, NumberKind(MAX_BITS + 1)]) is None
    True
    """
    if not all(arg.is_literal and arg.kind is NumberKind for arg in args):
        return None
    values = [arg.value for arg in args]
    if head == Add:
        return _sum(values)
    if head == Mul:
        return _product(values)
    if head == Pow and len(values) == 2:
        return _power(*values)
    if head == re and len(values) == 1:
        return args[0]
    if head in _COMPARISONS and len(values) == 2:
        return true if _COMPARISONS[head](*values) else false
    return None


def _bits(n):
    """The least b with abs(n) <= 2**b.

    >>> [_bits(n) for n in (0, 1, -2, 3, 4, 5)]
    [0, 0, 1, 2, 2, 3]
    """
    return (abs(n) - 1).bit_length() if n else 0


def _sum(terms):
    bits_of_largest_numerator = max((_bits(term.numerator) for term in terms), default=0)
    bits_of_denominators = sum(_bits(term.denominator) for term in terms)
    if _bits(len(terms)) + bits_of_largest_numerator + bits_of_denominators > MAX_BITS:
        return None
    return NumberKind(sum(terms))


def _product(factors):
    bits_of_numerators = sum(_bits(factor.numerator) for factor in factors)
    bits_of_denominators = sum(_bits(factor.denominator) for factor in factors)
    if max(bits_of_numerators, bits_of_denominators) > MAX_BITS:
        return None
    return NumberKind(prod(factors))


def _power(base, exponent):
    if exponent.denominator != 1 or (base == 0 and exponent <= 0):
        return None
    if abs(exponent) * max(_bits(base.numerator), _bits(base.denominator)) > MAX_BITS:
        return None
    return NumberKind(Fraction(base) ** exponent)

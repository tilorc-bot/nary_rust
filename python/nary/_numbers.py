"""Exact arithmetic on integers and fractions, written as the library writes them."""

from fractions import Fraction
from math import prod

from ._core import Expr
from .arithmetic import Add, Mul, Pow
from .kinds import NumberKind
from .logic import false, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re

__all__ = ["evaluate", "is_number"]

MAX_POWER_BITS = 14_000


def is_number(e):
    """Whether e is an integer literal or a reduced fraction in the one form the library writes.

    >>> from nary import Mul, NumberKind, Pow
    >>> is_number(NumberKind(-3)), is_number(Pow(2, -1)), is_number(Mul(-3, Pow(2, -1)))
    (True, True, True)
    >>> is_number(Mul(2, Pow(4, -1))), is_number(Mul(1, Pow(2, -1))), is_number(Pow(-2, -1))
    (False, False, False)
    >>> is_number(Pow(0, -1)), is_number(Pow(2, Pow(2, -1))), is_number(NumberKind("x"))
    (False, False, False)
    """
    return _value(e) is not None


def evaluate(head, args):
    """The value of head(*args) when every argument is a number and the result is one too.

    Args:
        head: Add, Mul, Pow, re, Eq, Ne, Lt, Gt, Le or Ge. Any other head gives None.
        args: The arguments. Each must pass is_number(arg).

    Returns:
        A number that passes is_number, or true or false for a comparison. None where
        head(*args) has no value, is not such a number, or is a power whose numerator or
        denominator would take more than MAX_POWER_BITS bits.

    >>> from nary import Add, Eq, Lt, Mul, NumberKind, Pow, sin
    >>> half, zero, three = Pow(2, -1), NumberKind(0), NumberKind(3)
    >>> evaluate(Add, (half, half)), evaluate(Mul, (three, half)), evaluate(Add, ())
    (1, Mul(3, Pow(2, -1)), 0)
    >>> evaluate(Pow, (Mul(-2, Pow(3, -1)), NumberKind(-3))), evaluate(Lt, (half, three))
    (Mul(-27, Pow(8, -1)), true)
    >>> evaluate(Pow, (zero, NumberKind(-1))), evaluate(Pow, (zero, zero))
    (None, None)
    >>> evaluate(Pow, (NumberKind(4), half)), evaluate(sin, (zero,)), evaluate(Eq, (half,))
    (None, None, None)
    """
    if not isinstance(head, Expr):
        return None
    operation = _OPERATIONS.get(head)
    if operation is None:
        return None
    values = []
    for arg in args:
        value = _value(arg)
        if value is None:
            return None
        values.append(value)
    return operation(values)


def _integer(e):
    if e.is_literal and e.kind is NumberKind and type(e.value) is int:
        return e.value
    return None


def _denominator(e):
    if not isinstance(e, Expr) or e.head != Pow:
        return None
    args = e.args
    if len(args) != 2:
        return None
    base, exponent = args
    if _integer(exponent) != -1:
        return None
    d = _integer(base)
    return d if d is not None and d >= 2 else None


def _value(e):
    if not isinstance(e, Expr):
        return None
    if e.is_literal:
        n = _integer(e)
        return None if n is None else Fraction(n)
    head = e.head
    if head is None:
        return None
    if head == Pow:
        d = _denominator(e)
        return None if d is None else Fraction(1, d)
    if head != Mul:
        return None
    args = e.args
    if len(args) != 2:
        return None
    n, d = _integer(args[0]), _denominator(args[1])
    if n is None or d is None or n in (0, 1):
        return None
    q = Fraction(n, d)
    return q if q.denominator == d else None


def _written(q):
    n, d = q.numerator, q.denominator
    if d == 1:
        return NumberKind(n)
    if n == 1:
        return Pow(d, -1)
    return Mul(n, Pow(d, -1))


def _add(values):
    return _written(sum(values, Fraction(0)))


def _multiply(values):
    return _written(prod(values, start=Fraction(1)))


def _power(values):
    if len(values) != 2 or values[1].denominator != 1:
        return None
    base, k = values[0], values[1].numerator
    if base == 0:
        return _written(base) if k > 0 else None
    if base == 1 or base == -1:
        return _written(base ** (k % 2))
    bits = max(abs(base.numerator).bit_length(), base.denominator.bit_length())
    if abs(k) * bits > MAX_POWER_BITS:
        return None
    return _written(base**k)


def _real_part(values):
    return _written(values[0]) if len(values) == 1 else None


def _comparison(holds):
    def compare(values):
        if len(values) != 2:
            return None
        return true if holds(*values) else false

    return compare


_OPERATIONS = {
    Add: _add,
    Mul: _multiply,
    Pow: _power,
    re: _real_part,
    Eq: _comparison(lambda a, b: a == b),
    Ne: _comparison(lambda a, b: a != b),
    Lt: _comparison(lambda a, b: a < b),
    Gt: _comparison(lambda a, b: a > b),
    Le: _comparison(lambda a, b: a <= b),
    Ge: _comparison(lambda a, b: a >= b),
}

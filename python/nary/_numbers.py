"""A temporary stand-in for number arithmetic, to be replaced by reviewed code.

    >>> from nary import Add, Gt, I, Mul, NumberKind, Pow
    >>> from nary._numbers import evaluate, is_number
    >>> half, twelve = Pow(2, -1), NumberKind(12)
    >>> evaluate(Add, (half, half)), evaluate(Pow, (twelve, half)), evaluate(Mul, (I, I))
    (1, Mul(2, Pow(3, Pow(2, -1))), -1)
    >>> evaluate(Pow, (NumberKind(0), NumberKind(-1))), evaluate(Gt, (half, NumberKind(0)))
    (None, true)
    >>> is_number(Mul(3, half)), is_number(Mul(2, I)), is_number(Add(1, I))
    (True, True, False)
"""

from fractions import Fraction
from math import lcm, prod

from ._core import Expr
from .arithmetic import Add, Mul, Pow
from .constants import I
from .kinds import NumberKind
from .logic import false, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re

__all__ = ["evaluate", "is_number"]

LARGEST_EXPONENT = 10_000
TRIAL_DIVISION_LIMIT = 10_000


def is_number(e):
    return _read(e) is not None


def evaluate(head, args):
    values = [_read(arg) for arg in args]
    if None in values:
        return None
    if head in _COMPARISONS:
        sign = _compare(*values)
        return None if sign is None else (true if sign in _COMPARISONS[head] else false)
    if head in _EQUALITIES:
        return true if (values[0] == values[1]) == _EQUALITIES[head] else false
    if head not in _OPERATIONS:
        return None
    result = _OPERATIONS[head](*values)
    return None if result is None else _write(result)


def _make(coefficient, roots, turn):
    turn %= 2
    if turn >= 1:
        coefficient, turn = -coefficient, turn - 1
    kept = {}
    for p, exponent in roots.items():
        whole = exponent.numerator // exponent.denominator
        coefficient *= Fraction(p) ** whole
        if exponent != whole:
            kept[p] = exponent - whole
    if coefficient == 0:
        return Fraction(0), (), Fraction(0)
    return coefficient, tuple(sorted(kept.items())), turn


def _factor(n):
    factors, p = {}, 2
    while p * p <= n and p < TRIAL_DIVISION_LIMIT:
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
        p += 1 if p == 2 else 2
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def _powers(q, x):
    powers = {p: k * x for p, k in _factor(q.numerator).items()}
    powers.update({p: -k * x for p, k in _factor(q.denominator).items()})
    return powers


def _rational(value):
    if value is None or value[1] or value[2]:
        return None
    if abs(value[0].numerator) > LARGEST_EXPONENT:
        return None
    return value[0]


def _read(e):
    if not isinstance(e, Expr) or e.kind is not NumberKind:
        return None
    if e.is_literal:
        return _make(Fraction(e.value), {}, Fraction(0))
    if e == I:
        return _make(Fraction(1), {}, Fraction(1, 2))
    if e.head == Mul:
        values = [_read(arg) for arg in e.args]
        return None if None in values else _multiply(*values)
    if e.head == Pow:
        base, exponent = e.args
        x = _rational(_read(exponent))
        if x is None or not base.is_literal:
            return None
        if base.value == -1:
            return _make(Fraction(1), {}, x)
        if base.value > 0:
            return _make(Fraction(1), _powers(Fraction(base.value), x), Fraction(0))
    return None


def _rational_expressions(q):
    if q.denominator == 1:
        return [NumberKind(q.numerator)]
    if q.numerator == 1:
        return [Pow(q.denominator, -1)]
    return [NumberKind(q.numerator), Pow(q.denominator, -1)]


def _write(value):
    coefficient, roots, turn = value
    by_denominator = {}
    for p, exponent in roots:
        by_denominator.setdefault(exponent.denominator, []).append(p ** exponent.numerator)
    pieces = [Pow(prod(powers), Pow(d, -1)) for d, powers in sorted(by_denominator.items())]
    if turn == Fraction(1, 2):
        pieces.append(I)
    elif turn:
        pieces.append(Pow(-1, _write((turn, (), Fraction(0)))))
    if coefficient != 1 or not pieces:
        pieces = _rational_expressions(coefficient) + pieces
    return pieces[0] if len(pieces) == 1 else Mul(*pieces)


def _multiply(*values):
    coefficient, roots, turn = Fraction(1), {}, Fraction(0)
    for c, value_roots, value_turn in values:
        coefficient, turn = coefficient * c, turn + value_turn
        for p, exponent in value_roots:
            roots[p] = roots.get(p, 0) + exponent
    return _make(coefficient, roots, turn)


def _add(*values):
    nonzero = [value for value in values if value[0]]
    if len({(roots, turn) for _, roots, turn in nonzero}) > 1:
        return None
    if not nonzero:
        return Fraction(0), (), Fraction(0)
    _, roots, turn = nonzero[0]
    return _make(sum(c for c, _, _ in nonzero), dict(roots), turn)


def _power(base, exponent):
    x = _rational(exponent)
    coefficient, roots, turn = base
    if x is None:
        return None
    if coefficient == 0:
        return base if x > 0 else None
    if x.denominator == 1:
        return _make(coefficient ** x, {p: e * x for p, e in roots}, turn * x)
    angle = turn + (coefficient < 0)
    if angle > 1:
        angle -= 2
    powers = _powers(abs(coefficient), x)
    for p, e in roots:
        powers[p] = powers.get(p, 0) + e * x
    return _make(Fraction(1), powers, angle * x)


def _real_part(value):
    if not value[2]:
        return value
    if value[2] == Fraction(1, 2):
        return Fraction(0), (), Fraction(0)
    return None


def _compare(a, b):
    if a[2] or b[2]:
        return None
    sign_a, sign_b = (a[0] > 0) - (a[0] < 0), (b[0] > 0) - (b[0] < 0)
    if sign_a != sign_b or sign_a == 0:
        return (sign_a > sign_b) - (sign_a < sign_b)
    d = lcm(*(e.denominator for _, e in a[1] + b[1]))
    size_a = abs(a[0]) ** d * prod(Fraction(p) ** int(e * d) for p, e in a[1])
    size_b = abs(b[0]) ** d * prod(Fraction(p) ** int(e * d) for p, e in b[1])
    return sign_a * ((size_a > size_b) - (size_a < size_b))


_OPERATIONS = {Add: _add, Mul: _multiply, Pow: _power, re: _real_part}
_COMPARISONS = {Lt: (-1,), Le: (-1, 0), Gt: (1,), Ge: (0, 1)}
_EQUALITIES = {Eq: True, Ne: False}

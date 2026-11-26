"""holds decides a condition from the structure of its expressions, or from known.

    >>> from nary import E, Ne, NumberKind, exp, log, pi
    >>> from nary.properties import has_value, holds
    >>> x = NumberKind("x")
    >>> holds(Ne(exp(x) * pi, 0)), holds(Ne(x, 0)), holds(Ne(x, 0), known={Ne(x, 0)})
    (True, False, True)
    >>> has_value(log(x + 1)), has_value(log(E ** x)), has_value(log(x), known={Ne(x, 0)})
    (False, True, True)

A canonical rational number is a literal, Pow(q, -1) or Mul(p, Pow(q, -1)).

    >>> from fractions import Fraction
    >>> from nary.properties import number, rational
    >>> number(Fraction(-3, 4)), rational(number(Fraction(-3, 4))), rational(x)
    (Mul(-3, Pow(4, -1)), Fraction(-3, 4), None)
"""

from fractions import Fraction

from . import intervals
from .arithmetic import Add, Mul, Pow
from .constants import E, I, pi
from .domains import domain_of
from .elementary import cos, exp, log, sin
from .functions import is_lambda
from .kinds import NumberKind
from .logic import And, Or, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re

__all__ = [
    "has_value", "holds", "integer", "negative", "nonzero", "number", "positive", "rational", "real",
]

ZERO = NumberKind(0)


def integer(e):
    return e.value if e.is_literal and e.kind is NumberKind else None


def rational(e):
    if integer(e) is not None:
        return Fraction(integer(e))
    if e.head == Pow and integer(e.args[1]) == -1 and (integer(e.args[0]) or 0) > 1:
        return Fraction(1, integer(e.args[0]))
    if e.head == Mul and len(e.args) == 2 and integer(e.args[0]) not in (None, 0, 1):
        unit = rational(e.args[1])
        if unit is not None and unit.numerator == 1 and unit.denominator > 1:
            return integer(e.args[0]) * unit
    return None


def number_factors(r):
    p, q = r.numerator, r.denominator
    if q == 1:
        return [NumberKind(p)]
    return ([NumberKind(p)] if p != 1 else []) + [Pow(NumberKind(q), -1)]


def number(r):
    factors = number_factors(Fraction(r))
    return factors[0] if len(factors) == 1 else Mul(*factors)


def holds(condition, known=()):
    if condition == true or condition in known:
        return True
    head, args = condition.head, condition.args
    if head == And:
        return all(holds(c, known) for c in args)
    if head == Or:
        return any(holds(c, known) for c in args)
    if head == Ne and args[1] == ZERO:
        return nonzero(args[0], known)
    if head == Gt and args[1] == ZERO:
        return positive(args[0], known)
    if head == Eq and args[0] == re(args[1]):
        return real(args[1], known)
    return head in _ORDER and _known(*_ordered(condition), known)


_ORDER = {Gt: (Gt, False), Lt: (Gt, True), Ge: (Ge, False), Le: (Ge, True)}


def _ordered(c):
    head, swap = _ORDER[c.head]
    return head, c.args[::-1] if swap else c.args


def _known(head, args, known):
    return any(c.head in _ORDER and _ordered(c) == (head, args) for c in known)


def has_value(e, known=()):
    if e.head is None or is_lambda(e):
        return True
    if not e.head.is_constant or domain_of(e) is None:
        return False
    return all(has_value(a, known) for a in e.args) and holds(domain_of(e), known)


def _all(test):
    return lambda known, *args: all(test(a, known) for a in args)


def _imaginary_sign(t, known):
    rest = list(t.args) if t.head == Mul else [t]
    if rest.count(I) != 1:
        return None
    rest.remove(I)
    return 1 if all(positive(f, known) for f in rest) else -1 if negative(Mul(*rest, 1), known) else None


def _nonreal(known, *terms):
    signs = {_imaginary_sign(t, known) for t in terms if not real(t, known)}
    return len(signs) == 1 and None not in signs


_NONZERO = {
    Add: _nonreal,
    Mul: _all(lambda a, known: nonzero(a, known)),
    Pow: lambda known, b, x: nonzero(b, known) and has_value(x, known),
    exp: lambda known, a: has_value(a, known),
}

_POSITIVE = {
    Add: _all(lambda a, known: positive(a, known)),
    Mul: _all(lambda a, known: positive(a, known)),
    Pow: lambda known, b, x: positive(b, known) and real(x, known),
    exp: lambda known, a: real(a, known),
    log: lambda known, a: a == pi or (rational(a) or 0) > 1,
    re: lambda known, a: positive(a, known),
}

_REAL = {
    Add: _all(lambda a, known: real(a, known)),
    Mul: _all(lambda a, known: real(a, known)),
    Pow: lambda known, b, x: positive(b, known) and real(x, known),
    exp: lambda known, a: real(a, known),
    sin: lambda known, a: real(a, known),
    cos: lambda known, a: real(a, known),
    log: lambda known, a: positive(a, known),
    re: lambda known, a: has_value(a, known),
}


def _decide(table, e, known):
    return e.head in table and table[e.head](known, *e.args)


def nonzero(e, known=()):
    if rational(e) is not None:
        return rational(e) != 0
    if e in (pi, E, I) or Ne(e, 0) in known or positive(e, known) or negative(e, known):
        return True
    return _decide(_NONZERO, e, known) or intervals.nonzero(e)


def positive(e, known=()):
    if rational(e) is not None:
        return rational(e) > 0
    if e in (pi, E) or _known(Gt, (e, ZERO), known) or _decide(_POSITIVE, e, known):
        return True
    return intervals.sign(e) == 1


def negative(e, known=()):
    if rational(e) is not None:
        return rational(e) < 0
    if _known(Gt, (ZERO, e), known) or intervals.sign(e) == -1:
        return True
    if e.head == Mul:
        signs = [negative(f, known) for f in e.args if not positive(f, known)]
        return all(signs) and len(signs) % 2 == 1
    return e.head == Add and all(negative(t, known) for t in e.args)


def real(e, known=()):
    if rational(e) is not None or e in (pi, E):
        return True
    if Eq(re(e), e) in known or positive(e, known) or negative(e, known):
        return True
    if any(c.head in _ORDER and e in c.args for c in known):
        return True
    return _decide(_REAL, e, known) or intervals.real(e)

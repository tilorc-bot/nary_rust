"""satsimp's trigsimp measure: trigonometric nodes, SymPy's count_ops, then nodes, with a rational as one node.

    >>> import nary as nr
    >>> x, y = nr.NumberKind("x"), nr.NumberKind("y")
    >>> measure = trig_measure((nr.sin, nr.cos, nr.tan))
    >>> measure(nr.Pow(nr.cos(x), -2)), measure(1 + nr.tan(x) ** 2)
    ((1, 3, 4), (1, 3, 6))
    >>> count_ops(x - y), count_ops(-x - y), count_ops(nr.Mul(-3, nr.Pow(2, -1), x, nr.Pow(y, -1)))
    (1, 2, 4)

Sums are measured without their sign when they lean negative.

    >>> measure(-nr.sin(x) - nr.cos(x)), measure(-nr.sin(x) - nr.cos(x), signless=True)
    ((2, 4, 9), (2, 3, 5))
"""

from fractions import Fraction
from math import prod

from nary import E, Add, Mul, Pow, exp
from nary.properties import negative, number, positive, rational

__all__ = ["count_heads", "count_ops", "nodes", "trig_measure"]

ONE = Fraction(1)


def _coefficient(e):
    if rational(e) is not None:
        return rational(e), []
    if e.head == Mul:
        numbers = [rational(a) for a in e.args if rational(a) is not None]
        return prod(numbers, start=ONE), [a for a in e.args if rational(a) is None]
    return ONE, [e]


def _product(c, rest):
    factors = ([number(c)] if c != 1 or not rest else []) + rest
    return factors[0] if len(factors) == 1 else Mul(*factors)


def _negate(e):
    c, rest = _coefficient(e)
    return _product(-c, rest)


def _base_exponent(f):
    if f.head == exp:
        return E, f.args[0]
    return f.args if f.head == Pow else (None, None)


def _whole(x):
    return rational(x) is not None and rational(x).denominator == 1


def _power(b, x):
    if b.head == Pow and rational(b.args[1]) is not None and _whole(x):
        b, x = b.args[0], number(rational(b.args[1]) * rational(x))
    if rational(b) is not None and _whole(x) and (rational(b) or rational(x) > 0):
        return number(rational(b) ** int(rational(x)))
    if rational(x) in (0, 1):
        return b if rational(x) else number(ONE)
    if b.head == Mul and _whole(x):
        return _evaluated([_power(f, x) for f in b.args])
    return exp(x) if b == E else Pow(b, x)


def _fraction(c, rest):
    numer = [number(c.numerator)] if c.numerator != 1 else []
    denom = [number(c.denominator)] if c.denominator != 1 else []
    for f in rest:
        b, x = _base_exponent(f)
        if b is not None and (negative(x) or (x.head == Mul and _coefficient(x)[0] < 0 and not positive(x))):
            denom.append(_power(b, _negate(x)))
        else:
            numer.append(f)
    return _evaluated(numer), _evaluated(denom)


def _evaluated(factors):
    if len(factors) < 2:
        return factors[0] if factors else number(ONE)
    c, powers, factors = ONE, {}, list(factors)
    for f in factors:
        if f.head == Mul:
            factors.extend(f.args)
            continue
        b, x = _base_exponent(f) if f.head == Pow else (f, number(ONE))
        if rational(f) is not None:
            c *= rational(f)
        elif b in powers and rational(x) is not None and rational(powers[b]) is not None:
            powers[b] = number(rational(powers[b]) + rational(x))
        else:
            powers[b] = Add(powers[b], x) if b in powers else x
    rest = [_power(b, x) for b, x in powers.items()]
    if any(r.head == Mul or rational(r) is not None for r in rest):
        return _evaluated([number(c), *rest])
    return _product(c, rest if c else [])


def _bare(e):
    return sum(map(count_ops, e.args)) if e.head == Add else count_ops(e)


def _mul_ops(c, rest):
    if c == -1 and len(rest) == 1:
        return 1 + _mul_ops(ONE, rest)
    numer, denom = _fraction(abs(c), rest)
    if rational(numer) is not None:
        ops = 1 + count_ops(denom)
    elif denom != number(ONE):
        ops = 1 + count_ops(denom) + count_ops(numer)
    else:
        args = ([number(abs(c))] if abs(c) != 1 else []) + rest
        ops = _bare(args[0]) if len(args) == 1 else len(args) - 1 + sum(map(count_ops, args))
    return (c < 0) + ops


def _term_ops(t):
    c, rest = _coefficient(t)
    if c > 0 or not rest or (c == -1 and len(rest) == 1):
        return count_ops(_negate(t) if c < 0 else t)
    return _mul_ops(-c, rest)


def count_ops(e):
    c, rest = _coefficient(e)
    if not rest:
        return (c < 0) + (c.denominator != 1)
    if e.head == Add:
        signs = [_coefficient(t)[0] < 0 for t in e.args]
        return len(signs) - 1 + all(signs) + sum(map(_term_ops, e.args))
    if e.head == Mul:
        return _mul_ops(c, rest)
    if e.head is None:
        return int(e == E)
    if e.head == Pow and e.args[1] == number(-ONE):
        return 1 + count_ops(e.args[0])
    if e.head == Pow and e.args[0] == E:
        return 1 + count_ops(e.args[1])
    return 1 + sum(map(count_ops, e.args))


def nodes(e):
    c, rest = _coefficient(e)
    if not rest or e.head is None:
        return 1
    if e.head == Mul:
        return (c != 1 or len(rest) > 1) + (c != 1) + sum(map(nodes, rest))
    return 1 + sum(map(nodes, e.args))


def _leans_negative(e):
    if e.head != Add:
        return _coefficient(e)[0] < 0
    signs = [_leans_negative(t) for t in e.args]
    return 2 * sum(signs) > len(signs)


def _negated_sum(terms):
    c, collected = Fraction(0), {}
    for t in terms:
        k, rest = _coefficient(t)
        if rest:
            s = _product(ONE, rest)
            collected[s] = collected.get(s, 0) - k
        else:
            c -= k
    out = [number(c)] if c else []
    for s, k in collected.items():
        if k:
            out.append(s if k == 1 else _product(k, list(s.args)) if s.head == Mul else _evaluated([number(k), s]))
    return out[0] if len(out) == 1 else Add(*out)


def _signless(e):
    if not _leans_negative(e):
        return e
    return _negated_sum(e.args) if e.head == Add else _negate(e)


def count_heads(e, heads):
    if e.head is None:
        return 0
    return (e.head in heads) + sum(count_heads(arg, heads) for arg in e.args)


def trig_measure(heads):
    def measure(e, signless=False):
        s = _signless(e) if signless else e
        return count_heads(e, heads), count_ops(s), nodes(s)

    return measure

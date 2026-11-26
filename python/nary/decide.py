"""decide settles a relation between numbers with interval arithmetic.

    >>> from nary import E, Eq, Ge, I, Lt, Ne, NumberKind, Pow, log, pi, tan
    >>> from nary.decide import decide
    >>> decide(Ge(log(8), pi + 9)), decide(Lt(Pow(27, -1), tan(2 * pi * Pow(3, -1))))
    (False, False)
    >>> decide(Eq(2, 3)), decide(Ne(E, I)), decide(Lt(I, 2)), decide(Eq(NumberKind("x"), 1))
    (False, True, None, None)
    >>> decide(Eq(re(log(2)), log(2))), decide(Eq(re(log(-2)), log(-2))), decide(Ne(-2, exp(I)))
    (True, False, True)
    >>> decide(Ne(cos(I), 1)), decide(Eq(sin(1 + I), 0))
    (True, False)
"""

from mpmath import iv

from .arithmetic import Add, Mul, Pow
from .constants import E, I, pi
from .elementary import cos, exp, log, sin, tan
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re

__all__ = ["decide", "interval"]

iv.prec = 80

ORDER = {
    Lt: lambda d: _sign(d) < 0, Le: lambda d: _sign(d) <= 0,
    Gt: lambda d: _sign(d) > 0, Ge: lambda d: _sign(d) >= 0,
}
NEGATED = {Lt: Ge, Le: Gt, Gt: Le, Ge: Lt}


def decide(c):
    if c.head not in (Eq, Ne, *ORDER) or len(c.args) != 2:
        return None
    a, b = (interval(arg) for arg in c.args)
    if a is None or b is None:
        return None
    if c.head == Eq and c.args[0] == re(c.args[1]) and b[1] is None:
        return True
    d = (a[0] - b[0], _sub(a[1], b[1]))
    if c.head in (Eq, Ne):
        apart = _sign(d[0]) in (1, -1) or (d[1] is not None and _sign(d[1]) in (1, -1))
        return (c.head == Ne) if apart else None
    if a[1] is not None or b[1] is not None or _sign(d[0]) is None:
        return None
    if ORDER[c.head](d[0]):
        return True
    return False if ORDER[NEGATED[c.head]](d[0]) else None


def interval(e):
    try:
        return _interval(e)
    except (ZeroDivisionError, ValueError, TypeError, OverflowError):
        return None


def _sign(x):
    if x.a > 0:
        return 1
    if x.b < 0:
        return -1
    return 0 if x.a == x.b == 0 else None


def _sub(u, v):
    if u is None and v is None:
        return None
    return (u if u is not None else iv.mpf(0)) - (v if v is not None else iv.mpf(0))


def _interval(e):
    if e.is_literal and type(e.value) is int:
        return iv.mpf(e.value), None
    if e in CONSTANTS:
        return CONSTANTS[e]
    if e.head is None or e.is_symbol:
        return None
    args = [_interval(arg) for arg in e.args]
    if any(arg is None for arg in args):
        return None
    if e.head == Add:
        return iv.mpf(sum((u[0] for u in args), iv.mpf(0))), _imag_sum(args)
    if e.head == Mul:
        out = (iv.mpf(1), None)
        for u in args:
            out = _mul(out, u)
        return out
    if e.head == Pow:
        return _pow(e, *args)
    if e.head == re:
        return args[0][0], None
    (x, y), = args
    if y is not None:
        return _complex(e.head, x, y)
    if e.head == exp:
        return iv.exp(x), None
    if e.head == sin:
        return iv.sin(x), None
    if e.head == cos:
        return iv.cos(x), None
    if e.head == tan:
        c = iv.cos(x)
        return (iv.sin(x) / c, None) if _sign(c) else None
    if e.head == log and _sign(x):
        return (iv.log(x), None) if _sign(x) > 0 else (iv.log(-x), CONSTANTS[pi][0])
    return None


def _complex(f, x, y):
    if f == exp:
        return iv.exp(x) * iv.cos(y), iv.exp(x) * iv.sin(y)
    cosh, sinh = (iv.exp(y) + iv.exp(-y)) / 2, (iv.exp(y) - iv.exp(-y)) / 2
    if f == sin:
        return iv.sin(x) * cosh, iv.cos(x) * sinh
    if f == cos:
        return iv.cos(x) * cosh, -iv.sin(x) * sinh
    return None


def _imag_sum(args):
    parts = [u[1] for u in args if u[1] is not None]
    return iv.mpf(sum(parts, iv.mpf(0))) if parts else None


def _mul(u, v):
    if u[1] is None and v[1] is None:
        return u[0] * v[0], None
    a, b = u[0], u[1] if u[1] is not None else iv.mpf(0)
    c, d = v[0], v[1] if v[1] is not None else iv.mpf(0)
    return a * c - b * d, a * d + b * c


def _pow(e, base, power):
    n = e.args[1]
    if n.is_literal and type(n.value) is int:
        k = n.value
        if abs(k) > 64:
            return None
        if k < 0:
            if base[1] is None:
                if not _sign(base[0]):
                    return None
                return iv.mpf(1) / base[0] ** -k, None
            m = base[0] ** 2 + base[1] ** 2
            base, k = (base[0] / m, -base[1] / m), -k
        out = (iv.mpf(1), None)
        for _ in range(k):
            out = _mul(out, base)
        return out
    if base[1] is None and power[1] is None and _sign(base[0]) == 1:
        return iv.exp(power[0] * iv.log(base[0])), None
    return None


CONSTANTS = {pi: (iv.pi, None), E: (iv.e, None), I: (iv.mpf(0), iv.mpf(1))}

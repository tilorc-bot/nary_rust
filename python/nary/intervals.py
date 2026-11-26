"""enclosure bounds a constant expression with mpmath's interval arithmetic; sign uses it.

    >>> from nary import E, I, Pow, cos, log, pi
    >>> from nary.intervals import enclosure, sign
    >>> sign(E - 3), sign(cos(2)), sign(1 - Pow(2, Pow(2, -1))), sign(pi - pi), sign(I)
    (-1, -1, -1, None, None)
    >>> 3.1415926 < enclosure(log(-1)).imag < 3.1415927, enclosure(log(1 - E) * 0 + 1 / cos(pi / 2))
    (True, None)
"""

from functools import lru_cache

try:
    from mpmath import floor as mpmath_floor
    from mpmath import iv
except ImportError:
    iv = None

from .arithmetic import Add, Mul, Pow
from .constants import E, I, pi
from .elementary import cos, exp, log, sin, tan
from .relational import re

__all__ = ["enclosure", "nonzero", "real", "sign", "turns"]


def _real(z):
    return iv is not None and isinstance(z, iv.mpf)


def _excludes_zero(z):
    return 0 not in z if _real(z) else 0 not in z.real or 0 not in z.imag


def _log(z):
    if _real(z) and z < 0:
        return iv.mpc(iv.log(-z), iv.pi)
    if _real(z) and z > 0:
        return iv.log(z)
    if not _real(z) and (z.real > 0 or 0 not in z.imag):
        return iv.log(z)
    return None


def _pow(b, x, n):
    if n is not None and (n > 0 or _excludes_zero(b)):
        return b ** n
    if n is None and _log(b) is not None:
        return _exp(x * _log(b))
    return None


def _exp(z):
    return iv.exp(z) if _real(z) else iv.mpc(iv.exp(z.real)) * iv.mpc(iv.cos(z.imag), iv.sin(z.imag))


def _tan(z):
    return iv.sin(z) / iv.cos(z) if _real(z) and 0 not in iv.cos(z) else None


_FUNCTIONS = {
    exp: _exp, log: _log, sin: lambda z: iv.sin(z) if _real(z) else None,
    cos: lambda z: iv.cos(z) if _real(z) else None, tan: _tan,
    re: lambda z: z if _real(z) else z.real,
}
_CONSTANTS = {pi: lambda: iv.pi, E: lambda: iv.e, I: lambda: iv.mpc(0, 1)}


def enclosure(e):
    if iv is None:
        return None
    precision, iv.dps = iv.dps, 30
    try:
        return _enclosure(e)
    finally:
        iv.dps = precision


@lru_cache(maxsize=4096)
def _enclosure(e):
    z = _evaluate(e)
    if z is not None and not _real(z) and z.imag.a == z.imag.b == 0:
        return z.real
    return z


def _evaluate(e):
    if e.is_literal:
        return iv.mpf(e.value)
    if e.is_symbol or e.head is None:
        return _CONSTANTS[e]() if e in _CONSTANTS else None
    args = [_enclosure(a) for a in e.args]
    if any(a is None for a in args):
        return None
    if e.head == Add:
        return sum(args[1:], args[0])
    if e.head == Mul:
        out = args[0]
        for a in args[1:]:
            out = out * a
        return out
    if e.head == Pow:
        x = e.args[1]
        n = x.value if x.is_literal else None
        return _pow(*args, n)
    return _FUNCTIONS[e.head](*args) if e.head in _FUNCTIONS else None


def sign(e):
    z = enclosure(e)
    if z is None or not _real(z) or 0 in z:
        return None
    return 1 if z > 0 else -1


def real(e):
    return _real(enclosure(e))


def nonzero(e):
    z = enclosure(e)
    return z is not None and _excludes_zero(z)


def turns(e):
    z = enclosure(e)
    if z is None:
        return None
    precision, iv.dps = iv.dps, 30
    try:
        t = iv.mpf(0.5) - (iv.mpf(0) if _real(z) else z.imag) / (2 * iv.pi)
        low, high = int(mpmath_floor(t.a)), int(mpmath_floor(t.b))
    finally:
        iv.dps = precision
    return low if low == high else None

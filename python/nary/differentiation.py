"""derivative gives the derivative and the conditions under which it exists.

    >>> from nary import Lambda, NumberKind, log, sin
    >>> from nary.differentiation import derivative
    >>> t = NumberKind("t")
    >>> derivative(Lambda(t, sin(t ** 2)))
    (Lambda(t, Mul(cos(Pow(t, 2)), Mul(2, Pow(t, Add(2, -1)), 1))), [])
    >>> derivative(log)
    (Lambda(t, Mul(Pow(t, -1), 1)), [Gt(t, 0)])

A function it has no rule for is left alone.

    >>> from nary.calculus import NumberFunction
    >>> derivative(Lambda(t, NumberFunction("f")(t))) is None
    True
"""

from .arithmetic import Add, Mul, Pow
from .elementary import cos, exp, log, sin, tan
from .functions import Lambda, is_lambda
from .kinds import NumberKind
from .relational import Gt

__all__ = ["derivative"]

CHAIN = {
    sin: lambda u: cos(u),
    cos: lambda u: Mul(-1, sin(u)),
    tan: lambda u: Add(Pow(tan(u), 2), 1),
    exp: lambda u: exp(u),
    log: lambda u: Pow(u, -1),
}


def derivative(f):
    if is_lambda(f) and len(f.args) == 2:
        v, body = f.args
    elif f in CHAIN:
        v = NumberKind("t")
        body = f(v)
    else:
        return None
    conditions = []
    d = _diff(body, v, conditions)
    return None if d is None else (Lambda(v, d), conditions)


def _diff(e, v, conditions):
    if e == v:
        return NumberKind(1)
    if not _contains(e, v):
        return NumberKind(0)
    if e.head == Add:
        terms = [_diff(a, v, conditions) for a in e.args]
        return None if None in terms else Add(*terms)
    if e.head == Mul:
        terms = []
        for i, a in enumerate(e.args):
            d = _diff(a, v, conditions)
            if d is None:
                return None
            terms.append(Mul(*e.args[:i], d, *e.args[i + 1:]))
        return Add(*terms)
    if e.head == Pow and not _contains(e.args[1], v):
        b, n = e.args
        if not (n.is_literal and isinstance(n.value, int)):
            conditions.append(Gt(b, 0))
        d = _diff(b, v, conditions)
        return None if d is None else Mul(n, Pow(b, Add(n, -1)), d)
    if e.head in CHAIN:
        if e.head == log:
            conditions.append(Gt(e.args[0], 0))
        d = _diff(e.args[0], v, conditions)
        return None if d is None else Mul(CHAIN[e.head](e.args[0]), d)
    return None


def _contains(e, v):
    return e == v or (e.head is not None and (_contains(e.head, v) or any(_contains(a, v) for a in e.args)))

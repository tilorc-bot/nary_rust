import itertools
import random

import mpmath

import nary as nr
from nary import Add, Mul, Pow, cos, exp, log, re, sin, tan
from nary.logic import And, Not, Or, false, true

mpmath.mp.dps = 50
ZERO = mpmath.mpf("1e-30")


def _is_zero(z):
    return abs(z) < ZERO


def _strict(f):
    def apply(*values):
        if any(v is None for v in values):
            return None
        return f(*values)
    return apply


def _pow(b, e):
    if _is_zero(b):
        return mpmath.mpc(0) if e.real > ZERO else None
    if e.imag == 0 and e.real == int(e.real):
        return b ** int(e.real)
    return mpmath.exp(e * mpmath.log(b))


def _real(z):
    return _is_zero(mpmath.mpc(z).imag)


def _compare(op):
    def compare(a, b):
        if not (_real(a) and _real(b)):
            return None
        a, b = mpmath.mpc(a).real, mpmath.mpc(b).real
        return op(a, b) if not _is_zero(a - b) else op(0, 0)
    return compare


def _and(*values):
    if False in values:
        return False
    return None if None in values else True


def _or(*values):
    if True in values:
        return True
    return None if None in values else False


FUNCTIONS = {
    Add: _strict(lambda *zs: mpmath.fsum(zs) if zs else mpmath.mpc(0)),
    Mul: _strict(lambda *zs: mpmath.fprod(zs) if zs else mpmath.mpc(1)),
    Pow: _strict(_pow),
    sin: _strict(mpmath.sin),
    cos: _strict(mpmath.cos),
    tan: _strict(lambda z: None if _is_zero(mpmath.cos(z)) else mpmath.tan(z)),
    exp: _strict(mpmath.exp),
    log: _strict(lambda z: None if _is_zero(z) else mpmath.log(z)),
    re: _strict(lambda z: mpmath.mpc(mpmath.mpc(z).real)),
    nr.Eq: _strict(lambda a, b: _is_zero(a - b)),
    nr.Ne: _strict(lambda a, b: not _is_zero(a - b)),
    nr.Lt: _strict(_compare(lambda a, b: a < b)),
    nr.Gt: _strict(_compare(lambda a, b: a > b)),
    nr.Le: _strict(_compare(lambda a, b: a <= b)),
    nr.Ge: _strict(_compare(lambda a, b: a >= b)),
    Not: _strict(lambda p: not p),
    And: _and,
    Or: _or,
}

CONSTANTS = {
    nr.pi: mpmath.mpc(mpmath.pi), nr.E: mpmath.mpc(mpmath.e), nr.I: mpmath.mpc(0, 1),
    true: True, false: False,
}


def evaluate(e, values):
    if e.is_symbol:
        return values[e.name]
    if e.is_literal:
        return mpmath.mpc(e.value)
    if e.is_constant:
        return CONSTANTS[e]
    return FUNCTIONS[e.head](*(evaluate(a, values) for a in e.args))


def same(a, b):
    if a is None or b is None or isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return abs(a - b) <= mpmath.mpf("1e-20") * max(1, abs(a), abs(b))


_pi = mpmath.pi
SPECIAL = [mpmath.mpc(z) for z in (
    0, 1, -1, 2, -2, mpmath.mpf(1) / 2, 1j, -1j, 1 + 1j, -3,
    _pi / 2, -_pi / 2, _pi, mpmath.mpc(0, _pi), mpmath.mpc(_pi, 1),
)]


def symbols_of(*exprs):
    found = {}
    for e in exprs:
        stack = [e]
        while stack:
            e = stack.pop()
            if e.is_symbol:
                found[e.name] = e.kind
            elif e.head is not None:
                stack.extend(e.args)
    return sorted(found.items())


def points(symbols, seed=0, limit=300):
    rng = random.Random(seed)
    numbers = [n for n, k in symbols if k is nr.NumberKind]
    booleans = [n for n, k in symbols if k is nr.BoolKind]
    pool = SPECIAL + [mpmath.mpc(rng.uniform(-3, 3), rng.choice((0, rng.uniform(-3, 3))))
                      for _ in range(30)]
    special = SPECIAL if len(numbers) <= 2 else SPECIAL[:6]
    result = [dict(zip(numbers, c)) for c in itertools.product(special, repeat=len(numbers))]
    while len(result) < limit and numbers:
        result.append({n: rng.choice(pool) for n in numbers})
    for c in itertools.product((True, False), repeat=len(booleans)):
        for point in result:
            yield {**point, **dict(zip(booleans, c))}


def counterexamples(lhs, rhs, known=()):
    found = []
    for point in points(symbols_of(lhs, rhs, *known)):
        if all(evaluate(c, point) is True for c in known):
            left, right = evaluate(lhs, point), evaluate(rhs, point)
            if not same(left, right):
                found.append((point, left, right))
    return found

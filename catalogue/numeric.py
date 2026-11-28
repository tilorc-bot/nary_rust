"""The numerical check of a catalogue entry, independent of SymPy.

``evaluate(e, values)`` works out the value of an nary expression at a point
with mpmath, following the meanings in ``lean/Nary/`` (issue #2), not
SymPy's: a number expression has a complex value or no value (``None``), a
boolean expression is ``True``, ``False`` or ``None``. Every function is
strict except ``And`` and ``Or``, which follow Kleene logic as in
``lean/Nary/Logic.lean``. ``0**0``, ``1/0`` and ``log(0)`` have no value;
there is no infinity and no ``nan``. ``Pow(b, e)`` is ``exp(e*log(b))``
with the principal logarithm, 0 at ``b = 0`` when ``re(e) > 0``, and no
value at ``b = 0`` otherwise.

``check(input, expected, condition)`` evaluates both sides at many points
(``points``) and returns the points where the claim of the entry fails:
the condition holds there, and the two sides do not both have no value or
the same value.

What it establishes: no counterexample among the points tried. The points
are chosen to include the exact places where the functions of main lose
their value (0, and points where ``cos`` is 0) and the branch cut of
``log`` (the negative reals), as well as random real and complex points.
It is evidence, not a proof. Its weak spots, said plainly:

- "Is zero" is decided with a tolerance (``ZERO``), at 50 digits, so a
  value that is not 0 but smaller than ``1e-30`` counts as 0, and the
  domain of ``tan`` at a point like pi/2, which cannot be written exactly in
  floating point, is decided by that tolerance.
- A point very close to the branch cut, but not on it, can land on either
  side after rounding. The points tried are either exactly on the cut or
  far from it.
- ``Derivative(f)(a)`` is computed with mpmath's numerical differentiation,
  and "``f`` has a value near ``a``" is tested at eight points on a small
  circle around ``a``. It is only used for functions that are
  complex-differentiable wherever they have a value (all the declared ones
  except ``re``, which no entry differentiates).
"""

import itertools
import random

import mpmath

import nary as nr
from nary import Add, Mul, Pow, cos, exp, log, re, sin, tan
from nary.calculus import Derivative
from nary.functions import is_lambda
from nary.logic import And, Not, Or, false, true

__all__ = ["ZERO", "check", "evaluate", "points", "same"]

mpmath.mp.dps = 50

# Below this, a number counts as 0, both in domains and in comparing sides.
ZERO = mpmath.mpf("1e-30")


def _is_zero(z):
    return abs(z) < ZERO


def _strict(f):
    """``f`` applied to values, with no value if an argument has none."""
    def apply(*values):
        if any(v is None for v in values):
            return None
        return f(*values)
    return apply


def _pow(b, e):
    if _is_zero(b):
        return mpmath.mpc(0) if e.real > 0 else None
    return mpmath.exp(e * mpmath.log(b))


def _real(z):
    return _is_zero(mpmath.mpc(z).imag)


def _compare(op):
    def compare(a, b):
        if not (_real(a) and _real(b)):
            return None
        return op(mpmath.mpc(a).real, mpmath.mpc(b).real)
    return compare


def _and(*values):
    if any(v is False for v in values):
        return False
    if any(v is None for v in values):
        return None
    return True


def _or(*values):
    if any(v is True for v in values):
        return True
    if any(v is None for v in values):
        return None
    return False


_FUNCTIONS = {
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
    nr.Lt: _strict(_compare(lambda a, b: a < b and not _is_zero(a - b))),
    nr.Gt: _strict(_compare(lambda a, b: a > b and not _is_zero(a - b))),
    nr.Le: _strict(_compare(lambda a, b: a < b or _is_zero(a - b))),
    nr.Ge: _strict(_compare(lambda a, b: a > b or _is_zero(a - b))),
    Not: _strict(lambda p: not p),
    And: _and,
    Or: _or,
}

_CONSTANTS = {
    nr.pi: mpmath.mpc(mpmath.pi),
    nr.E: mpmath.mpc(mpmath.e),
    nr.I: mpmath.mpc(0, 1),
    true: True,
    false: False,
}

# Where "f has a value near a" is tested for Derivative(f)(a).
_NEAR = [mpmath.mpf("1e-12") * mpmath.expjpi(mpmath.mpf(k) / 4) for k in range(8)]


def _function(f, values):
    """The meaning of the function expression ``f``: a Python function from
    a complex number to a complex number or ``None``."""
    if is_lambda(f):
        *variables, body = f.args
        (variable,) = variables
        return lambda z: evaluate(body, {**values, variable.name: z})
    if f.is_constant and f in _FUNCTIONS:
        return _FUNCTIONS[f]
    if f.head == Derivative:
        (g,) = f.args
        g = _function(g, values)

        def derivative(a):
            if g(a) is None or any(g(a + h) is None for h in _NEAR):
                return None
            return mpmath.diff(g, a)

        return derivative
    raise ValueError(f"no numerical meaning for the function {f!r}")


def evaluate(e, values):
    """The value of ``e`` where each symbol has the value given by name in
    ``values``: an ``mpc``, ``True``/``False``, or ``None`` for no value."""
    if e.is_symbol:
        return values[e.name]
    if e.is_literal:
        return mpmath.mpc(e.value)
    if e.is_constant:
        if e in _CONSTANTS:
            return _CONSTANTS[e]
        raise ValueError(f"no numerical meaning for the constant {e!r}")
    args = [evaluate(a, values) for a in e.args]
    if e.head in _FUNCTIONS:
        return _FUNCTIONS[e.head](*args)
    (arg,) = args
    return None if arg is None else _function(e.head, values)(arg)


def same(a, b):
    """Whether two values are both no value or the same value."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return abs(a - b) <= ZERO * max(1, abs(a), abs(b))


# Values tried for each number symbol: the places where the functions of
# main lose their value or change branch, small integers, and random points.
_pi = mpmath.pi
_SPECIAL = [mpmath.mpc(z) for z in (
    0, 1, -1, 2, -2, 3, mpmath.mpf(1) / 2, -mpmath.mpf(1) / 2,
    1j, -1j, 2j, 1 + 1j, -1 - 2j, mpmath.mpc(-3, 0),
    _pi / 2, -_pi / 2, _pi, 3 * _pi / 2, _pi / 4,
    mpmath.mpc(0, _pi), mpmath.mpc(0, 2 * _pi), mpmath.mpc(_pi, 1),
)]


def _random_values(rng, n):
    values = []
    for _ in range(n):
        values.append(mpmath.mpc(rng.uniform(-3, 3)))
        values.append(mpmath.mpc(rng.uniform(-3, 3), rng.uniform(-3, 3)))
    return values


def points(symbols, seed=0, limit=400):
    """Points at which to evaluate an entry with these symbols (a list of
    ``(name, kind)``): dictionaries from name to value. Every combination
    of the special values when there are few, then random points."""
    rng = random.Random(seed)
    number = [name for name, kind in symbols if kind is nr.NumberKind]
    boolean = [name for name, kind in symbols if kind is nr.BoolKind]
    pool = _SPECIAL + _random_values(rng, 20)
    result = []
    special = _SPECIAL if len(number) <= 2 else _SPECIAL[:8]
    for combo in itertools.product(special, repeat=len(number)):
        result.append(dict(zip(number, combo)))
    while len(result) < limit and number:
        result.append({name: rng.choice(pool) for name in number})
    if not number:
        result = [{}]
    with_booleans = []
    for p in result:
        for combo in itertools.product((True, False), repeat=len(boolean)):
            with_booleans.append({**p, **dict(zip(boolean, combo))})
    return with_booleans


def symbols_of(*exprs):
    """The free symbols of the expressions, as ``(name, kind)`` in order of
    first appearance, not counting the variables of lambdas."""
    found = []

    def walk(e, bound):
        if e.is_symbol:
            if e.name not in bound and (e.name, e.kind) not in found:
                found.append((e.name, e.kind))
        elif is_lambda(e):
            *variables, body = e.args
            walk(body, bound | {v.name for v in variables})
        elif e.head is not None:
            walk(e.head, bound)
            for a in e.args:
                walk(a, bound)

    for e in exprs:
        if e is not None:
            walk(e, frozenset())
    return found


class Result:
    """What ``check`` found: the points tried, those where the condition
    held, those where both sides had no value, and the counterexamples,
    each as ``(point, input value, expected value)``."""

    def __init__(self):
        self.tried = 0
        self.held = 0
        self.both_none = 0
        self.counterexamples = []

    @property
    def value_counterexamples(self):
        """Counterexamples where both sides have a value and they differ,
        as opposed to one side having no value."""
        return [c for c in self.counterexamples if c[1] is not None and c[2] is not None]

    def __repr__(self):
        return (f"Result(tried={self.tried}, held={self.held}, both_none={self.both_none}, "
                f"counterexamples={len(self.counterexamples)})")


def check(input, expected, condition=None, seed=0):
    """Evaluate ``input`` and ``expected`` at the points of ``points`` where
    ``condition`` holds (is ``True``), and collect the counterexamples."""
    result = Result()
    for point in points(symbols_of(input, expected, condition), seed=seed):
        result.tried += 1
        if condition is not None and evaluate(condition, point) is not True:
            continue
        result.held += 1
        a, b = evaluate(input, point), evaluate(expected, point)
        if a is None and b is None:
            result.both_none += 1
        if not same(a, b):
            result.counterexamples.append((point, a, b))
    return result

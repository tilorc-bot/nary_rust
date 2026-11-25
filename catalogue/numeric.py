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
It is evidence, not a proof.

"Is zero" (the domain of ``Pow``, ``log`` and ``tan``, and comparing the
two sides) is decided with a tolerance that depends on the working
precision: at ``d`` digits a number counts as 0 when it is smaller than
``10**-(3*d//5)`` (``zero_tolerance``), so 1e-30 at 50 digits. A number
that is 0 but computed with rounding (``cos(pi/2)``, with pi rounded) is
about ``10**-d``, below the tolerance at every precision; a number that is
not 0 stays the same size, so at a high enough precision it is above the
tolerance. ``check`` therefore decides each point at the precisions of
``PRECISIONS`` in turn and takes the first verdict that a higher precision
repeats: a tiny non-zero value (such as ``exp(-3*pi**2/log(sqrt(2)))``,
about 8e-38, which 50 digits took for 0) gets its true verdict at 100 and
200 digits. A point where no two consecutive precisions agree is
``unsure``: neither a counterexample nor a confirmation, and reported
apart. Its other weak spots, said plainly:

- A value that is not 0 but smaller than the tolerance at the highest
  precision (``10**-120``) still counts as 0 at every precision, and the
  domain of ``tan`` at a point like pi/2, which cannot be written exactly in
  floating point, is decided this way.
- A value whose real or imaginary part counts as 0 by that rule (relative
  to the size of the value) is made exactly 0 (``_snap``), so a value that
  is real but computed with rounding lies on the branch cut of ``log``
  rather than on the side the rounding error picks. A value truly off the
  cut by less than the tolerance is put on it. The points tried are either
  exactly on the cut or far from it.
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

__all__ = ["PRECISIONS", "check", "evaluate", "points", "same", "zero_tolerance"]

mpmath.mp.dps = 50

# The working precisions (decimal digits) at which check decides a point, in
# order; the verdict is the first one the next precision repeats.
PRECISIONS = (50, 100, 200)

_TOLERANCES = {}


def zero_tolerance():
    """Below this, a number counts as 0, in domains and in comparing sides:
    ``10**-(3*d//5)`` at the working precision of ``d`` digits."""
    dps = mpmath.mp.dps
    if dps not in _TOLERANCES:
        _TOLERANCES[dps] = mpmath.mpf(10) ** -(3 * dps // 5)
    return _TOLERANCES[dps]


def _is_zero(z):
    return abs(z) < zero_tolerance()


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

# Functions, so that pi and e are computed at the working precision.
_CONSTANTS = {
    nr.pi: lambda: mpmath.mpc(mpmath.pi),
    nr.E: lambda: mpmath.mpc(mpmath.e),
    nr.I: lambda: mpmath.mpc(0, 1),
    true: lambda: True,
    false: lambda: False,
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
            return _CONSTANTS[e]()
        raise ValueError(f"no numerical meaning for the constant {e!r}")
    args = [evaluate(a, values) for a in e.args]
    if e.head in _FUNCTIONS:
        return _snap(_FUNCTIONS[e.head](*args))
    (arg,) = args
    return None if arg is None else _snap(_function(e.head, values)(arg))


def _snap(z):
    """``z`` with a real or imaginary part that counts as 0 (relative to
    ``|z|``, as in ``same``) made exactly 0, so that a value that is real
    but computed with rounding (``1/(1 - sqrt(2))``) is on the branch cut
    of ``log``, not on a side chosen by the sign of the rounding error."""
    if not isinstance(z, mpmath.mpc):
        return z
    small = zero_tolerance() * max(1, abs(z))
    real = 0 if abs(z.real) < small else z.real
    imag = 0 if abs(z.imag) < small else z.imag
    return z if (real, imag) == (z.real, z.imag) else mpmath.mpc(real, imag)


def same(a, b):
    """Whether two values are both no value or the same value."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return abs(a - b) <= zero_tolerance() * max(1, abs(a), abs(b))


_SPECIALS = {}


def _special():
    """Values tried for each number symbol: the places where the functions of
    main lose their value or change branch, small integers. Computed at the
    working precision, so that pi/2 is as close to pi/2 as that precision
    allows."""
    dps = mpmath.mp.dps
    if dps not in _SPECIALS:
        pi = mpmath.pi
        _SPECIALS[dps] = [mpmath.mpc(z) for z in (
            0, 1, -1, 2, -2, 3, mpmath.mpf(1) / 2, -mpmath.mpf(1) / 2,
            1j, -1j, 2j, 1 + 1j, -1 - 2j, mpmath.mpc(-3, 0),
            pi / 2, -pi / 2, pi, 3 * pi / 2, pi / 4,
            mpmath.mpc(0, pi), mpmath.mpc(0, 2 * pi), mpmath.mpc(pi, 1),
        )]
    return _SPECIALS[dps]


def _random_values(rng, n):
    values = []
    for _ in range(n):
        values.append(mpmath.mpc(rng.uniform(-3, 3)))
        values.append(mpmath.mpc(rng.uniform(-3, 3), rng.uniform(-3, 3)))
    return values


def points(symbols, seed=0, limit=400):
    """Points at which to evaluate an entry with these symbols (a list of
    ``(name, kind)``): dictionaries from name to value. Every combination
    of the special values when there are few, then random points. The
    points are the same at every precision (the random ones are floats,
    the special ones are computed at the working precision)."""
    rng = random.Random(seed)
    number = [name for name, kind in symbols if kind is nr.NumberKind]
    boolean = [name for name, kind in symbols if kind is nr.BoolKind]
    specials = _special()
    pool = specials + _random_values(rng, 20)
    result = []
    special = specials if len(number) <= 2 else specials[:8]
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
    each as ``(point, input value, expected value)``, at the precision that
    decided the point. ``unsure``: the points (as ``(point, verdicts by
    precision)``) where no two consecutive precisions agree; ``revised``:
    how many points the first precision got wrong, as a higher one showed."""

    def __init__(self):
        self.tried = 0
        self.held = 0
        self.both_none = 0
        self.counterexamples = []
        self.unsure = []
        self.revised = 0

    @property
    def value_counterexamples(self):
        """Counterexamples where both sides have a value and they differ,
        as opposed to one side having no value."""
        return [c for c in self.counterexamples if c[1] is not None and c[2] is not None]

    def __repr__(self):
        return (f"Result(tried={self.tried}, held={self.held}, both_none={self.both_none}, "
                f"counterexamples={len(self.counterexamples)}, unsure={len(self.unsure)}, "
                f"revised={self.revised})")


def _verdict(input, expected, condition, point):
    """``(verdict, input value, expected value)`` at the working precision;
    the verdict is ``"skipped"`` (the condition does not hold),
    ``"both-none"``, ``"same"``, ``"definedness"`` (one side has no value)
    or ``"value"`` (different values)."""
    if condition is not None and evaluate(condition, point) is not True:
        return "skipped", None, None
    a, b = evaluate(input, point), evaluate(expected, point)
    if a is None and b is None:
        return "both-none", a, b
    if same(a, b):
        return "same", a, b
    return ("definedness" if a is None or b is None else "value"), a, b


def check(input, expected, condition=None, seed=0):
    """Evaluate ``input`` and ``expected`` at the points of ``points`` where
    ``condition`` holds (is ``True``), and collect the counterexamples. Each
    point is decided at the precisions of ``PRECISIONS`` in turn, until two
    consecutive ones agree (see the module docstring)."""
    symbols = symbols_of(input, expected, condition)
    result = Result()
    pending = None  # indices of the points not decided yet
    verdicts = {}   # index -> [(verdict, point, a, b) by precision]
    decided = {}    # index -> (verdict, point, a, b)
    for dps in PRECISIONS:
        with mpmath.workdps(dps):
            found = points(symbols, seed=seed)
            for i in (range(len(found)) if pending is None else pending):
                verdict, a, b = _verdict(input, expected, condition, found[i])
                history = verdicts.setdefault(i, [])
                history.append((verdict, found[i], a, b))
                if len(history) >= 2 and history[-1][0] == history[-2][0]:
                    decided[i] = history[-1]
        pending = [i for i in verdicts if i not in decided]
        if not pending:
            break
    for i in sorted(verdicts):
        result.tried += 1
        if i not in decided:
            result.unsure.append((verdicts[i][0][1], [v[0] for v in verdicts[i]]))
            continue
        verdict, point, a, b = decided[i]
        if verdict != verdicts[i][0][0]:
            result.revised += 1
        if verdict == "skipped":
            continue
        result.held += 1
        if verdict == "both-none":
            result.both_none += 1
        if verdict in ("definedness", "value"):
            result.counterexamples.append((point, a, b))
    return result

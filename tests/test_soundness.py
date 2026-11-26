import cmath
import itertools
import math
import random
from importlib.util import find_spec

import pytest
from nary import (
    E, Add, BoolKind, Eq, Ge, Gt, I, Le, Lt, Mul, Ne, NumberKind, Pow, arithmetic_rules, cos,
    elementary_rules, exp, log, logic_rules, pi, re, sin, tan
)
from nary.calculus import Derivative
from nary.functions import is_lambda
from nary.kinds import Many
from nary.logic import And, Not, Or, false, true
from nary.simplify import simplify

needs_mpmath = pytest.mark.skipif(find_spec("mpmath") is None, reason="mpmath")
CIRCLE = [cmath.exp(2j * math.pi * k / 32) for k in range(32)]


class Undecided(Exception):
    pass


def snap(z):
    if not cmath.isfinite(z) or abs(z) > 1e8:
        raise Undecided
    t = 1e-13 * max(1, abs(z))
    return complex(0.0 if abs(z.real) < t else z.real, 0.0 if abs(z.imag) < t else z.imag)


def close(a, b):
    return abs(a - b) <= 1e-9 * max(1, abs(a), abs(b))


def strict(f):
    return lambda *values: None if any(v is None for v in values) else f(*values)


def power(b, e):
    if b == 0:
        return 0j if e.real > 0 else None
    return cmath.exp(e * cmath.log(b))


def order(f):
    return strict(lambda a, b: f(a.real, b.real, close(a, b)) if a.imag == b.imag == 0 else None)


def kleene(absorbing):
    def apply(*values):
        if absorbing in values:
            return absorbing
        return None if None in values else not absorbing
    return apply


FUNCTIONS = {
    Add: strict(lambda *zs: sum(zs, 0j)),
    Mul: strict(lambda *zs: math.prod(zs, start=1 + 0j)),
    Pow: strict(power),
    sin: strict(cmath.sin),
    cos: strict(cmath.cos),
    tan: strict(lambda z: None if snap(cmath.cos(z)) == 0 else cmath.tan(z)),
    exp: strict(cmath.exp),
    log: strict(lambda z: None if z == 0 else cmath.log(z)),
    re: strict(lambda z: complex(z.real)),
    Eq: strict(close),
    Ne: strict(lambda a, b: not close(a, b)),
    Lt: order(lambda a, b, same: a < b and not same),
    Le: order(lambda a, b, same: a < b or same),
    Gt: order(lambda a, b, same: a > b and not same),
    Ge: order(lambda a, b, same: a > b or same),
    Not: strict(lambda p: not p),
    And: kleene(False),
    Or: kleene(True),
}
CONSTANTS = {pi: complex(math.pi), E: complex(math.e), I: 1j, true: True, false: False}


def is_run(e):
    return e.is_symbol and e.kind.family is Many


def derivative(g):
    def estimate(a, r):
        values = [g(a + r * w) for w in CIRCLE]
        return None if None in values else sum(v / w for v, w in zip(values, CIRCLE)) / (32 * r)

    def at(a):
        first, second = estimate(a, 5e-4), estimate(a, 2.5e-4)
        if g(a) is None or first is None or second is None:
            return None
        error = abs(first - second) / max(1, abs(second))
        if 1e-6 < error < 0.1:
            raise Undecided
        return second if error <= 1e-6 else None
    return at


def function(f, env):
    if f.is_symbol:
        return env[f.name]
    if is_lambda(f):
        variable, body = f.args
        return lambda z: evaluate(body, {**env, variable.name: z})
    if f.head == Derivative:
        return derivative(function(f.args[0], env))
    return lambda *args: number(FUNCTIONS[f](*args))


def number(value):
    return snap(value) if isinstance(value, complex) else value


def evaluate(e, env):
    if e.kind.inputs is not None:
        return function(e, env)
    if e.is_symbol:
        return env[e.name]
    if e.is_literal:
        return complex(e.value)
    if e.is_constant:
        return CONSTANTS[e]
    args = [v for a in e.args for v in (env[a.name] if is_run(a) else [evaluate(a, env)])]
    if e.head in FUNCTIONS:
        return number(FUNCTIONS[e.head](*args))
    return None if None in args else function(e.head, env)(*args)


def same(a, b):
    if callable(a) and callable(b):
        return all(same(*values) for values in (safe(a, b, z) for z in SPECIAL[::3]))
    if a is None or b is None or isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return close(a, b)


def safe(a, b, z):
    try:
        return a(z), b(z)
    except Undecided:
        return None, None


SPECIAL = sorted({
    complex(z) for z in (
        0, 1, -1, 2, -2, 3, -3, 0.5, -0.5, 1j, -1j, 2j, 1 + 1j, -1 + 1j, -2 - 1j,
        1j * math.pi, -1j * math.pi, 2j * math.pi, 0.5j * math.pi, math.pi + 1j,
        *(k * math.pi / 6 for k in range(-6, 13)), *(k * math.pi / 4 for k in range(-4, 9)),
    )
}, key=lambda z: (z.real, z.imag))


def point(rng):
    kind = rng.random()
    if kind < 0.4:
        return rng.choice(SPECIAL)
    if kind < 0.6:
        return complex(rng.randint(-4, 4))
    if kind < 0.8:
        return complex(rng.uniform(-3, 3))
    return complex(rng.uniform(-3, 3), rng.uniform(-3, 3))


def sample(variable, rng, erased):
    if variable.kind.family is Many:
        inner = variable.kind.params[0]
        return [sample(inner("_"), rng, erased) for _ in range(rng.randrange(4))]
    if variable.kind.inputs is not None:
        return function(rng.choice([sin, cos, tan, exp, log]), {})
    if not erased and rng.random() < 0.1:
        return None
    if variable.kind is BoolKind:
        return rng.choice([True, False])
    return point(rng)


def environments(r, count=3000, seed=0):
    rng = random.Random(seed)
    names = [v.name for v in r.variables]
    plain = [v for v in r.variables if v.kind is NumberKind]
    if len(plain) == len(names) <= 2:
        for values in itertools.product(SPECIAL, repeat=len(plain)):
            yield dict(zip(names, values))
    for _ in range(count if names else 0):
        yield {v.name: sample(v, rng, v in r.erased) for v in r.variables}


def check(r):
    held = 0
    for env in environments(r):
        try:
            if r.condition is not None and evaluate(r.condition, env) is not True:
                continue
            a, b = evaluate(r.pattern, env), evaluate(r.replacement, env)
        except Undecided:
            continue
        held += 1
        if not same(a, b):
            return held, (env, a, b)
    return held, None


RULES = [
    *arithmetic_rules.rules, *elementary_rules.rules, *logic_rules.rules,
]


@pytest.mark.parametrize("r", RULES, ids=lambda r: r.name or repr(r))
def test_rule_is_sound(r):
    held, counterexample = check(r)
    assert counterexample is None, f"{r!r} fails at {counterexample}"
    assert held > 0, f"the condition of {r!r} never held"


x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
p, q = BoolKind("p"), BoolKind("q")
EXPRESSIONS = [
    x + x, x - x, 2 * x + 3 * x - x, x * y + y * x, (x + 1) * (x - 1) - x**2, 2 * (x + y) - 2 * y,
    x * x * x, x**2 * x**3, x**-1 * x**2, x / x, x**0, 0 * x, 0 * log(x), (x * y) ** 2,
    (x**2) ** 3, (x**3) ** -1, (x ** Pow(2, -1)) ** 2, (x**2) ** Pow(2, -1),
    Pow(4, Pow(2, -1)), Pow(8, Pow(3, -1)) * x, Pow(-4, Pow(2, -1)), Pow(25, Pow(3, -1)),
    Pow(2, -1) + Pow(3, -1), (1 + I) ** 2, I**3 * x, Pow(4 * x, Pow(2, -1)), Pow(0, x),
    x / (x * y), (x + y) / (x + y), Add(x, y, -x, -y, z), 1 / (1 / x),
    exp(log(x)), log(exp(x)), exp(x) * exp(y), exp(x) ** 2, exp(0), log(1), E**x, exp(I * pi),
    exp(2 * log(x)), log(x * y), log(x**2), exp(log(x) + log(y)),
    sin(x) ** 2 + cos(x) ** 2, sin(-x), cos(-x), tan(-x), sin(x + 2 * pi), cos(x + pi),
    sin(pi / 6), cos(pi / 4), tan(pi / 3), sin(pi / 2 - x), sin(x) / cos(x), tan(x) * cos(x),
    re(x + I * y), re(re(x)), sin(3 * pi + x), cos(-2 * x + pi / 2),
]
CONDITIONS = [
    Eq(x, x), Ne(x, x), Lt(x, x), Le(x, x), Not(Lt(x, y)), Not(Not(p)), And(p, true), Or(p, false),
    And(p, false), Or(p, true), And(p, p), Or(p, And(p, q)), Not(And(p, q)), And(p, Not(p)),
    Or(p, Not(p)), Eq(x + 1, 1 + x), Lt(x + 1, x + 2), And(Lt(x, y), Gt(y, x)),
]


ASSUMED = [
    (x / x, [Ne(x, 0)]), (x**0, [Gt(x, 0)]), (log(exp(x)), [Eq(re(x), x)]), (x * 0, [Ne(x, 0)]),
    ((x**2) ** Pow(2, -1), [Gt(x, 0)]), (log(x * y), [Gt(x, 0), Gt(y, 0)]),
    (exp(2 * log(x)), [Ne(x, 0)]), (x**-1 * x**2, [Lt(x, 0)]), ((x**3) ** -1, [Ne(x, 0)]),
    (Pow(x * y, Pow(2, -1)), [Gt(x, 0)]), (Lt(x, x), [Eq(re(x), x)]), (re(x * y), [Gt(x, 0)]),
    (Pow(x**2, Pow(3, -1)), [Gt(x, 0)]), (log(x**2), [Gt(x, 0)]), (Le(x, x + 1), [Gt(x, 0)]),
]


def points(conditions, count=400, seed=1):
    rng = random.Random(seed)
    for _ in range(count):
        env = {v.name: rng.choice([True, False]) if v.kind is BoolKind else point(rng)
               for v in (x, y, z, p, q)}
        if all(evaluate(c, env) is True for c in conditions):
            yield env


@pytest.mark.parametrize(("e", "known"), [(e, []) for e in EXPRESSIONS + CONDITIONS] + ASSUMED,
                         ids=repr)
def test_simplify_is_sound(e, known):
    result = simplify(e, known=known or None)
    for env in points(known):
        try:
            a, b = evaluate(e, env), evaluate(result, env)
        except Undecided:
            continue
        assert same(a, b), f"{e!r} -> {result!r} differs at {env}: {a} vs {b}"

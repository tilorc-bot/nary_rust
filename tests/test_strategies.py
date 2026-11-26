import pytest
from test_soundness import Undecided, check, evaluate, points, same

from nary import Gt, Lt, Mul, NumberKind, Pow, cos, exp, log, sin, tan
from nary.strategies import STRATEGIES, apply

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
RULES = list({r.name: r for rules in STRATEGIES.values() for r in rules}.values())
INPUTS = [
    x * (y + z), (x + 1) ** 2, (x + y) * (x - y), (x + 1) ** 3, (x + 2) * (x + 1) * (y + 1),
    log(x) * (y + 1), log(x + 1) ** 2, 1 / x + 1 / y, x / y + z, log(x * y), log(x) + log(y),
    sin(2 * x), cos(2 * x), 2 * sin(x) * cos(x), cos(x) ** 2 - sin(x) ** 2, tan(x) ** 2 + 1,
    x**y * x**z, exp(x) * exp(y), sin(x + y), exp(x) + log(x) * tan(y), (x + y) ** -2,
    exp(x + y + 1), log(-2 * x * y), 2 * log(x) - 3 * log(y), sin(3 * x), cos(x + y),
    sin(x) * cos(y) + sin(y) * cos(x), 1 / x + y / 3 + z, sin(x) ** 2 / cos(x) ** 2,
]
KNOWN = [Gt(x, 0), Gt(y, 0)]


@pytest.mark.parametrize("r", RULES, ids=lambda r: r.name)
def test_rule_is_sound(r):
    held, counterexample = check(r)
    assert counterexample is None, f"{r!r} fails at {counterexample}"
    assert held > 0


@pytest.mark.parametrize("name", STRATEGIES)
@pytest.mark.parametrize("known", [None, KNOWN], ids=["free", "positive"])
def test_strategy_terminates_and_is_sound(name, known):
    for e in INPUTS:
        result = apply(name, e, known)
        for env in points(known or []):
            try:
                a, b = evaluate(e, env), evaluate(result, env)
            except Undecided:
                continue
            assert same(a, b), f"{name}: {e!r} -> {result!r} differs at {env}"


def test_strategies():
    assert apply("expand", (x + 1) ** 2) == apply("expand", x**2 + 2 * x + 1)
    assert apply("expand_log", log(x * y), KNOWN) == log(x) + log(y)
    assert apply("logcombine", log(x) + log(y), KNOWN) == log(x * y)
    assert apply("trigsimp", cos(x) ** 2 - sin(x) ** 2) == cos(2 * x)
    assert apply("powsimp", x**y * x**z, KNOWN) == x ** (y + z)


def test_sympy_forms():
    assert apply("expand", (x + y) ** 3) == apply("expand", x**3 + 3 * x**2 * y + 3 * x * y**2 + y**3)
    assert apply("expand", exp(x + y)) == exp(x) * exp(y)
    assert apply("expand_log", log(2 * x)) == log(2) + log(x)
    assert apply("expand_log", log(x * y), [Lt(x, 0), Lt(y, 0)]) == log(-x) + log(-y)
    assert apply("logcombine", 2 * log(x) - log(y), KNOWN) == log(x**2 / y)
    assert apply("expand_trig", cos(2 * x)) == apply("expand_trig", 2 * cos(x) ** 2 - 1)
    assert apply("trigsimp", sin(x) * cos(y) + sin(y) * cos(x)) == sin(x + y)
    assert apply("together", 1 / x + 1 / y) == Mul(x + y, Pow(x, -1), Pow(y, -1))

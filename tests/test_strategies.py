import pytest
from test_soundness import Undecided, check, evaluate, points, same

from nary import Gt, NumberKind, cos, exp, log, sin, tan
from nary.strategies import STRATEGIES, apply

x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
RULES = [r for rules in STRATEGIES.values() for r in rules]
INPUTS = [
    x * (y + z), (x + 1) ** 2, (x + y) * (x - y), (x + 1) ** 3, (x + 2) * (x + 1) * (y + 1),
    log(x) * (y + 1), log(x + 1) ** 2, 1 / x + 1 / y, x / y + z, log(x * y), log(x) + log(y),
    sin(2 * x), cos(2 * x), 2 * sin(x) * cos(x), cos(x) ** 2 - sin(x) ** 2, tan(x) ** 2 + 1,
    x**y * x**z, exp(x) * exp(y), sin(x + y), exp(x) + log(x) * tan(y), (x + y) ** -2,
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

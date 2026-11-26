import doctest
import importlib

import pytest

for name in ("sympy", "satassume", "satsimp"):
    pytest.importorskip(name)

MODULES = ["translate", "prove", "rows", "engine", "substitute", "methods", "record", "scoreboard"]


@pytest.mark.parametrize("name", MODULES)
def test_docstring_examples(name):
    module = importlib.import_module(f"nary.satsimp.{name}")
    result = doctest.testmod(module, optionflags=doctest.ELLIPSIS)
    assert result.failed == 0
    assert result.attempted > 0



def test_trig_measure_is_satsimps_without_abs():
    import sympy
    from satsimp.methods.trigsimp.wiring import measure

    import nary as nr
    from nary.satsimp.methods import trig_measure
    from nary.satsimp.translate import from_sympy

    x, y = sympy.symbols("x y")
    s, c, t = sympy.sin, sympy.cos, sympy.tan
    ours = trig_measure((nr.sin, nr.cos, nr.tan))
    for e in [s(x) ** 2 - 2, -c(x) ** 2 - 1, s(2 * y) - c(2 * y) ** 2, -3 * s(2 * x) * s(4 * x) / 2,
              (c(x) ** 2 + 1) / (s(x) ** 2 - 2), t(x) ** 4 + 2 * t(x) ** 2 + 1, x * c(x) / (3 * y)]:
        trig, ops, _, nodes = measure(e)
        assert ours(from_sympy(e)) == (trig, ops, nodes), e

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


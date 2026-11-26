import doctest
import importlib
import subprocess
import sys

import pytest

MODULES = ["engine", "measure", "methods", "prove", "rows", "substitute", "tables"]

WITHOUT_SYMPY = f"""
import sys
sys.modules["sympy"] = None
import nary as nr
for name in {MODULES!r}:
    __import__("nary.satsimp." + name)
from nary.satsimp.methods import Simplifier
x = nr.NumberKind("x")
simplifier = Simplifier()
print(simplifier.trigsimp(nr.sin(x) ** 2 + nr.cos(x) ** 2 + nr.tan(x) * nr.cos(x), nr.Ne(nr.cos(x), 0)))
print(simplifier.refine(nr.Pow(nr.Pow(x, 2), nr.Pow(2, -1)), nr.Gt(x, 0)))
print(sorted(name for name in sys.modules if name.partition(".")[0] == "sympy"), sys.modules["sympy"])
"""


@pytest.mark.parametrize("name", MODULES)
def test_docstring_examples(name):
    module = importlib.import_module(f"nary.satsimp.{name}")
    result = doctest.testmod(module, optionflags=doctest.ELLIPSIS)
    assert result.failed == 0


def test_the_port_runs_without_sympy():
    run = subprocess.run([sys.executable, "-c", WITHOUT_SYMPY], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert run.stdout.splitlines() == ["Add(1, sin(x))", "x", "['sympy'] None"]

import subprocess
import sys

BLOCKED = """
import sys
sys.modules["mpmath"] = None
from nary import E, I, Lt, NumberKind, Pow, cos, exp
from nary.autosimp import autosimp
x = NumberKind("x")
for e, known in [
    (Lt(E, 3), []), (cos(2) / cos(2), []), (Pow(exp(5 * I), Pow(2, -1)), []),
    (2 * x - x, []), (Pow(3 + 4 * I, Pow(2, -1)), []), (Pow(Pow(x, 2), Pow(2, -1)), [Lt(x, 0)]),
]:
    print(autosimp(e, known))
"""


def test_autosimp_runs_without_mpmath_and_interval_steps_wait():
    run = subprocess.run([sys.executable, "-c", BLOCKED], capture_output=True, text=True, check=True)
    assert run.stdout.split("\n")[:-1] == [
        "Lt(E, 3)", "Pow(cos(2), 0)", "Pow(exp(Mul(5, I)), Pow(2, -1))", "x", "Add(2, I)", "Mul(-1, x)",
    ]

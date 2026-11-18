"""Check that Lean accepts what nary.lean prints.

Prints a handful of example expressions with ``to_lean_example`` into a
temporary Lean file that imports ``Nary``, and runs ``lake env lean`` on it
in this directory. Each example is checked three times: at the top level,
after ``open Nary`` and inside ``namespace Nary``, since the full names are
meant to be correct wherever the output is pasted. Lean only checks that
each line is a well-typed term of the stated type; it does not check that
the term means what the Python expression means.

Run by hand, with the Python that has ``nary`` installed, after
``lake build``:

    .venv/bin/python lean/check_printer.py

It is not part of the Python tests, which do not need Lean.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import nary as nr
from nary.calculus import Derivative, NumberFunction
from nary.lean import to_lean_example
from nary.logic import And, Not, Or, false, true

LEAN_DIR = Path(__file__).resolve().parent

x, y = nr.NumberKind("x"), nr.NumberKind("y")
p, q = nr.BoolKind("p"), nr.BoolKind("q")
f = NumberFunction("f")

EXAMPLES = [
    # symbols, literals and a list: x - y and x / 2
    x - y,
    x / 2,
    # positional arguments, the constants, the elementary functions
    nr.Pow(nr.E, nr.I * nr.pi) + nr.log(nr.sin(x) + nr.cos(y) * nr.tan(x)),
    nr.exp(nr.re(x)) ** -3,
    # empty lists
    nr.Add() * nr.Mul(),
    # comparisons and logic
    And(nr.Eq(x, 0), Or(p, Not(q)), nr.Ne(x, y), true),
    Or(x < y, x <= y, x > y, x >= y, false),
    # a lambda, and a call of a lambda (a substitution)
    nr.Lambda(x, x * x),
    nr.Lambda(x, nr.sin(x))(y + 1),
    # a function symbol, Derivative, and a declared function as a value
    f(x) + Derivative(f)(y),
    Derivative(Derivative(nr.sin)),
    nr.Lambda(y, Derivative(nr.Lambda(x, x * y))(y)),
    # symbol names that are Lean names, keywords, or not identifiers
    nr.NumberKind("I") * nr.I + nr.NumberKind("pi") + nr.NumberKind("fun")
    + nr.NumberKind("at") + nr.NumberKind("x 1") + nr.NumberKind("θ"),
    And(nr.BoolKind("true"), nr.BoolKind("Not"), true),
]


def find_lake():
    lake = shutil.which("lake")
    if lake is None:
        candidate = Path.home() / ".elan" / "bin" / "lake"
        if candidate.exists():
            lake = str(candidate)
    if lake is None:
        sys.exit("lake not found: install elan, or put ~/.elan/bin on PATH")
    return lake


def main():
    lines = [to_lean_example(e) for e in EXAMPLES]
    for e, line in zip(EXAMPLES, lines):
        print(f"{e!r}\n    {line}")
    body = "\n".join(lines)
    source = (
        "import Nary\n\n"
        f"{body}\n\n"
        "section\nopen Nary\n\n"
        f"{body}\n\n"
        "end\n\n"
        "namespace Nary\n\n"
        f"{body}\n\n"
        "end Nary\n"
    )
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "CheckPrinter.lean"
        path.write_text(source, encoding="utf-8")
        result = subprocess.run(
            [find_lake(), "env", "lean", str(path)],
            cwd=LEAN_DIR, capture_output=True, text=True,
        )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or output:
        print(f"\nLean reported a problem (exit status {result.returncode}):")
        print(output)
        print("\nThe Lean file was:\n")
        for number, line in enumerate(source.splitlines(), 1):
            print(f"{number:4} {line}")
        sys.exit(1)
    print(f"\nLean accepted all {len(lines)} examples, in each of three contexts.")


if __name__ == "__main__":
    main()

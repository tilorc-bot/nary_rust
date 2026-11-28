import os
import signal
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from nary import Add, Lambda, NumberKind, declare_function, declare_kind, sin
from nary.arithmetic_rules import rules
from nary.lean import to_lean
from nary.logic import true
from nary.rewriting import rewrite
from nary.rules import rule

DEPTH = 100_000
REWRITE_DEPTH = 1_000
SHALLOW = 100
WIDTH = 100_000
COST_DEPTH = 1_000
TIMEOUT = 60
PR_SET_DUMPABLE = 4

PRELUDE = f"""
import ctypes, sys
if sys.platform == "linux":
    ctypes.CDLL(None).prctl({PR_SET_DUMPABLE}, 0, 0, 0, 0)
from nary import Add, Lambda, NumberKind, cos, sin
from nary.arithmetic_rules import rules
from nary.lean import to_lean
from nary.rewriting import rewrite
from nary.rules import rule
x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")


def left(n, inner=x, outer=x):
    e = inner
    for _ in range(n - 1):
        e = Add(e, x)
    return Add(e, outer)


def right(n, inner=x, outer=x):
    e = inner
    for _ in range(n - 1):
        e = Add(x, e)
    return Add(outer, e)


def nested_sin(n, inner=x, outer=sin):
    e = inner
    for _ in range(n - 1):
        e = sin(e)
    return outer(e)


def left_with_plus(n):
    e = x
    for _ in range(n):
        e = e + x
    return e


def right_with_plus(n):
    e = x
    for _ in range(n):
        e = x + e
    return e


chain = {{"left": left, "right": right, "sin": nested_sin}}
with_plus = {{"left": left_with_plus, "right": right_with_plus}}
other_outer = {{"left": y, "right": y, "sin": cos}}
"""

TOP = {"left": "Add 2 NumberKind False", "right": "Add 2 NumberKind False", "sin": "sin 1 NumberKind False"}
TOP_OF = "print(e.head, len(e.args), e.kind, e.is_atom)"

OPERATIONS = {
    "build": ("e = chain[shape](n)\n" + TOP_OF, TOP),
    "build with +": ("e = with_plus[shape](n)\n" + TOP_OF, TOP),
    "free": (
        "def build_and_drop():\n    e = chain[shape](n)\n    del e\nbuild_and_drop()\nprint('freed')",
        "freed",
    ),
    "hash": ("e = chain[shape](n)\nprint(hash(e) == hash(e))", "True"),
    "dict key": ("e = chain[shape](n)\nprint({e: 'found'}[e])", "found"),
    "set member": ("e = chain[shape](n)\nprint(e in {e})", "True"),
    "e == e": ("e = chain[shape](n)\nprint(e == e)", "True"),
    "equal chains": ("print(chain[shape](n) == chain[shape](n))", "True"),
    "differ innermost": ("print(chain[shape](n) == chain[shape](n, inner=y))", "False"),
    "differ outermost": (
        "print(chain[shape](n) == chain[shape](n, outer=other_outer[shape]))",
        "False",
    ),
    "repr": ("e = chain[shape](n)\nprint(len(repr(e)) > n)", "True"),
    "str": ("e = chain[shape](n)\nprint(len(str(e)) > n)", "True"),
    "rewrite": ("e = chain[shape](n)\nprint(rewrite(e, rules).kind)", "NumberKind"),
    "to_lean": ("e = chain[shape](n)\nprint(len(to_lean(e)) > n)", "True"),
    "rule": ("e = chain[shape](n)\nprint(type(rule(Add(e, z), z)).__name__)", "Rule"),
    "Lambda": ("e = chain[shape](n)\nprint(Lambda(z, e).args[1] is e)", "True"),
}

HASH = "hash recurses in the core: SIGSEGV at depth 1e5"
EQUAL = "== recurses in the core and through tuple ==: RecursionError"
REPR = "repr recurses through repr of the args: RecursionError"
REWRITE = "rewrite recurses in Python: RecursionError from depth ~1e3"
TO_LEAN = "to_lean recurses in Python: RecursionError from depth ~1e3"
FAILS_TODAY = {
    "hash": HASH,
    "dict key": "a dict hashes its key: " + HASH,
    "set member": "a set hashes its members: " + HASH,
    "equal chains": EQUAL,
    "differ innermost": EQUAL,
    ("differ outermost", "left"): EQUAL,
    "repr": REPR,
    "str": REPR,
    "rewrite": REWRITE,
    "to_lean": TO_LEAN,
}
CRASHES_TODAY = {"hash": HASH}


def depth_of(operation):
    return REWRITE_DEPTH if operation == "rewrite" else DEPTH


def shapes_of(operation):
    return ["left", "right"] if operation == "build with +" else ["left", "right", "sin"]


def cases(operations, failing):
    for operation in operations:
        for shape in shapes_of(operation):
            reason = failing.get((operation, shape), failing.get(operation))
            marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
            yield pytest.param((operation, shape), marks=marks, id=f"{operation}-{shape}")


WORKS = list(cases(OPERATIONS, FAILS_TODAY))
DOES_NOT_CRASH = list(cases(
    ["hash", "equal chains", "differ innermost", "repr", "str", "rewrite", "to_lean"],
    CRASHES_TODAY,
))


def run(snippet):
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
    try:
        done = subprocess.run(
            [sys.executable, "-c", PRELUDE + snippet],
            capture_output=True, text=True, timeout=TIMEOUT, env=env,
        )
    except subprocess.TimeoutExpired:
        return f"timed out after {TIMEOUT}s"
    if done.returncode < 0:
        return f"killed by {signal.Signals(-done.returncode).name}"
    if done.returncode == 1 and "Traceback" in done.stderr:
        return "raised " + done.stderr.strip().splitlines()[-1][:200]
    if done.returncode:
        return f"exited with status {done.returncode}"
    return done.stdout.strip()


def snippet_for(operation, shape):
    return f"shape = {shape!r}\nn = {depth_of(operation)}\n" + OPERATIONS[operation][0] + "\n"


@pytest.fixture(scope="module")
def outcomes():
    every = {param.values[0] for param in WORKS + DOES_NOT_CRASH}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {case: pool.submit(run, snippet_for(*case)) for case in every}
        yield futures
        for future in futures.values():
            future.cancel()


def crashed(result):
    return result.startswith(("killed by", "timed out", "exited with status"))


@pytest.mark.parametrize("case", DOES_NOT_CRASH)
def test_does_not_crash(case, outcomes):
    operation, shape = case
    result = outcomes[case].result()
    assert not crashed(result), f"{operation} of a {shape} chain at depth {depth_of(operation)}: {result}"


@pytest.mark.parametrize("case", WORKS)
def test_works(case, outcomes):
    operation, shape = case
    expected = OPERATIONS[operation][1]
    if isinstance(expected, dict):
        expected = expected[shape]
    result = outcomes[case].result()
    assert result == expected, f"{operation} of a {shape} chain at depth {depth_of(operation)}: {result}"


x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")


def left(n, inner=x):
    e = inner
    for _ in range(n):
        e = Add(e, x)
    return e


def nested_sin(n, inner=x):
    e = inner
    for _ in range(n):
        e = sin(e)
    return e


@pytest.mark.parametrize("build", [left, nested_sin])
def test_shallow_chains(build):
    e = build(SHALLOW)
    assert {e: 1}[build(SHALLOW)] == 1
    assert e == build(SHALLOW)
    assert e != build(SHALLOW, inner=y)
    assert len(repr(e)) == len(str(e)) > SHALLOW
    assert rewrite(e, rules).kind is NumberKind
    assert len(to_lean(e)) > SHALLOW
    assert rule(Add(e, z), z).pattern.args[0] is e


@pytest.fixture(scope="module")
def wide():
    return Add(x, *(NumberKind(f"x{i}") for i in range(WIDTH - 2)), x)


@pytest.fixture(scope="module")
def wide_twin():
    return Add(x, *(NumberKind(f"x{i}") for i in range(WIDTH - 2)), x)


def test_wide_top(wide):
    assert (wide.head, len(wide.args), wide.kind, wide.is_atom) == (Add, WIDTH, NumberKind, False)


def test_wide_hash(wide, wide_twin):
    assert hash(wide) == hash(wide_twin)
    assert {wide: "found"}[wide_twin] == "found"
    assert wide_twin in {wide}


def test_wide_equality(wide, wide_twin):
    assert wide == wide
    assert wide == wide_twin
    assert wide != Add(x, *wide.args[1:-1], y)
    assert wide != Add(y, *wide.args[1:])


def test_wide_repr(wide):
    assert len(repr(wide)) == len(str(wide)) > WIDTH


def test_wide_to_lean(wide):
    assert len(to_lean(wide)) > WIDTH


def test_wide_lambda(wide):
    assert Lambda(z, wide).args[1] is wide


class Tally:
    hashed = 0

    def __hash__(self):
        Tally.hashed += 1
        return 0


TallyKind = declare_kind("TallyKind", literals=Tally)
grow = declare_function("grow", TallyKind, returns=TallyKind, domain=true)


@pytest.mark.xfail(
    sys.version_info < (3, 14), strict=True,
    reason="the core does not cache the hash, and tuples cache theirs only from Python 3.14: quadratic",
)
def test_hashing_every_subterm_of_a_chain_is_linear():
    subterms = [TallyKind(Tally())]
    for _ in range(COST_DEPTH - 1):
        subterms.append(grow(subterms[-1]))
    Tally.hashed = 0
    for e in subterms:
        hash(e)
    assert Tally.hashed < 10, (
        f"hashing the {COST_DEPTH} subterms of a chain hashed its innermost leaf {Tally.hashed} times"
    )

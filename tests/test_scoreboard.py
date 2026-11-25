"""The scoreboard (scoreboard/): SymPy's test files run on nary.

- The committed reports are what ``scoreboard.report`` writes now.
- The installed SymPy's test file is the pinned one (git blob sha).
- Every assert statement of the file, found here independently with
  ``ast``, has at least one case: none is silently dropped.
- Every hand-written difference names a case that fails.
"""

import ast
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytest.importorskip("sympy")

from scoreboard import report, rules  # noqa: E402
from scoreboard.collect import collect, source  # noqa: E402

FILES = sorted(rules.FILES)


@pytest.mark.parametrize("name", FILES)
def test_pinned_file(name):
    path, sha = rules.FILES[name]
    data = source(path)
    assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == sha


@pytest.mark.parametrize("name", FILES)
def test_report_is_current(name):
    assert (report.HERE / f"{name}.md").read_text(encoding="utf-8") == report.render(name), (
        f"{name}.md is out of date: run .venv/bin/python -m scoreboard.report")


@pytest.mark.parametrize("name", FILES)
def test_every_assert_has_a_case(name):
    path, _ = rules.FILES[name]
    asserts = sorted((node.lineno, node.col_offset) for node in ast.walk(ast.parse(source(path)))
                     if isinstance(node, ast.Assert))
    expected = [(line, sum(a[0] == line for a in asserts[:i]))
                for i, (line, _) in enumerate(asserts)]
    cases = collect(path)
    assert sorted({(c.line, c.position) for c in cases}) == expected
    assert len({c.id for c in cases}) == len(cases)


@pytest.mark.parametrize("name", FILES)
def test_piles(name):
    path, _ = rules.FILES[name]
    for case in collect(path):
        pile, reason = report.score(case)
        assert pile in rules.PILES
        assert reason or pile == rules.GAP


def test_differences_name_failing_cases():
    failing = {case.id for path, _ in rules.FILES.values() for case in collect(path)
               if case.op and report.score(case)[0] in (rules.GAP, rules.DIFFERS)}
    for case_id, (kind, note) in rules.DIFFERENCES.items():
        assert case_id in failing and kind in rules.DIFFERENCE_KINDS and note


def test_a_reason_is_kept_through_arithmetic():
    from scoreboard.collect import Value, lift
    oo = Value(why={rules.name("oo")})
    x = lift(2)
    assert (x + 1).expr is not None and not (x + 1).why
    assert (1 / (x ** oo) + 0.5).why == {(rules.MISSING, "infinities"), (rules.MISSING, "floats")}
    assert x.is_real.why == {(rules.NOT_APPLICABLE, "an assumption query (is_real)")}

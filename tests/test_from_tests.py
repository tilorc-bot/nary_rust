"""The entries generated from SymPy's test files (catalogue/from_tests).

- The committed files are what the generator writes now (regenerate and
  compare, as tests/test_lean.py does for the Lean rules).
- The ledger has exactly one row per assert statement of the pinned test
  file, found here independently with ``ast``: every assert is accounted
  for.
- The installed SymPy's test file is the pinned one (git blob sha), and
  every source links to it at the pinned commit with a line anchor.
- Every entry row names existing entries, and every generated entry's
  sources are exactly the rows that name it.
"""

import ast
import importlib
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

sympy = pytest.importorskip("sympy")

from catalogue import numeric  # noqa: E402
from catalogue.entries import ENTRIES, HAND_WRITTEN  # noqa: E402
from catalogue.from_tests import generate, rules  # noqa: E402
from catalogue.from_tests.power import ENTRIES as GENERATED, LEDGER, LINKS  # noqa: E402
from catalogue.sympy_check import SYMPY_COMMIT  # noqa: E402

PATH, SHA = rules.FILES["power"]


def _installed():
    module = importlib.import_module(generate.module_name(PATH))
    return Path(module.__file__).read_bytes()


def _asserts():
    """``(function, line, position)`` of every assert statement of the file:
    the top-level function it is in (``<module>`` outside one), its first
    line, and its index among the asserts that start on that line."""
    tree = ast.parse(_installed())
    found = []
    for top in tree.body:
        function = top.name if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)) \
            else "<module>"
        for node in ast.walk(top):
            if isinstance(node, ast.Assert):
                found.append((function, node.lineno, node.col_offset))
    by_line = Counter()
    result = []
    for function, line, _ in sorted(found, key=lambda f: (f[1], f[2])):
        result.append((function, line, by_line[line]))
        by_line[line] += 1
    return result


def test_pinned_file():
    assert generate.git_blob_sha(_installed()) == SHA


def test_generated_files_are_current():
    for path, text in generate.render("power").items():
        assert path.read_text(encoding="utf-8") == text, (
            f"{path.name} is out of date: run .venv/bin/python -m catalogue.from_tests")


def test_ledger_is_every_assert():
    rows = [(r.source.function, r.source.line, r.source.position) for r in LEDGER]
    assert rows == _asserts()
    assert len({r.id for r in LEDGER}) == len(LEDGER)


def test_categories():
    for r in LEDGER:
        assert r.category in rules.CATEGORIES
        assert bool(r.entries) == (r.category == "entry")
        assert bool(r.reason) == (r.category != "entry")
    counts = Counter(r.category for r in LEDGER)
    assert sum(counts.values()) == len(_asserts())


def test_links_are_permalinks():
    sources = [r.source for r in LEDGER] + [s for e in GENERATED for s in e.sources]
    for s in sources:
        assert s.file == PATH
        assert s.url.startswith(f"https://github.com/sympy/sympy/blob/{SYMPY_COMMIT}/{PATH}#L")
        assert f"#L{s.line}" in s.url


def test_rows_and_entries_agree():
    """Each entry row names generated or hand-written entries; the sources of
    each generated entry, and of each linked hand-written entry, are exactly
    the rows that name it."""
    generated = {e.name: e for e in GENERATED}
    hand = {e.name for e in HAND_WRITTEN}
    named = {}
    for r in LEDGER:
        for name in r.entries:
            assert name in generated or name in hand
            named.setdefault(name, []).append(r.source)
    for name, e in generated.items():
        assert list(e.sources) == named.get(name), name
    for name, sources in LINKS.items():
        assert name in hand and list(sources) == named[name]
    assert set(named) == set(generated) | set(LINKS)
    in_catalogue = {e.name: e for e in ENTRIES}
    for name in generated:
        assert in_catalogue[name] == generated[name]
    for name, sources in LINKS.items():
        assert in_catalogue[name].sources == sources


def test_undecided_classes_are_listed():
    for e in GENERATED:
        if e.status == "undecided":
            assert e.cause in rules.UNDECIDED_CLASSES


def test_tiny_value_is_not_zero():
    """At 50 digits exp(-3*pi**2/log(sqrt(2))), about 8e-38, is below the
    tolerance and so counts as 0 (and 0**(1/3) is 0); the check decides the
    point at higher precisions, where it is not 0, and the entry
    power_l384_1, which SymPy gets right, has no counterexample."""
    import nary as nr
    tiny = nr.exp(nr.Mul(-3, nr.Pow(nr.pi, 2), nr.Pow(nr.log(nr.Pow(2, nr.Pow(2, -1))), -1)))
    assert numeric.evaluate(nr.Pow(tiny, nr.Pow(3, -1)), {}) == 0
    entry = {e.name: e for e in GENERATED}["power_l384_1"]
    result = numeric.check(entry.input, entry.expected, entry.when)
    assert not result.counterexamples and not result.unsure and result.revised == 1
    assert entry.status == "accepted"

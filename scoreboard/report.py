"""Scoring the cases of a SymPy test file and writing the report.

``python -m scoreboard.report`` writes ``<name>.md`` for each file of
``rules.FILES``. ``tests/test_scoreboard.py`` fails when a report is not
what this writes now.

A case ``left == right`` passes when nary's engine (``nary.rewriting`` with
``nary.arithmetic_rules``, knowing the conditions that stand for the
symbols' SymPy assumptions) rewrites both sides to the same expression, up
to the order of the arguments of ``Add`` and ``Mul``. A case ``left !=
right`` passes when it does not. That is what the assert says in SymPy,
where building an expression is what rewrites it.

A case that does not pass is a gap, unless it has a reason not to count
against nary: an entry in ``rules.DIFFERENCES``, or the numerical check
(``catalogue.numeric``) finds a point where one side has a value and the
other has none and no point where both have different values. Then nary's
definitions make the two sides different expressions, and SymPy's do not.
"""

from collections import Counter
from pathlib import Path

from nary.arithmetic_rules import rules as RULES
from nary.logic import And, true
from nary.rewriting import rewrite

from catalogue import numeric
from catalogue.engine import normal
from catalogue.entry import ASSUMPTIONS
from catalogue.sympy_check import to_sympy

from . import rules
from .collect import collect
from .rules import DIFFERS, GAP, MISSING, NOT_APPLICABLE, NOT_RUN, PASS

__all__ = ["render", "score", "write"]

HERE = Path(__file__).resolve().parent


def _conditions(case):
    """The nary conditions for the SymPy assumptions of the case's symbols."""
    symbols = {name: kind(name) for name, kind in numeric.symbols_of(case.left, case.right)}
    return [ASSUMPTIONS[fact](symbols[name]) for name, facts in case.assume.items()
            for fact in facts.items() if fact in ASSUMPTIONS]


def score(case):
    """``(pile, reason)`` of a case."""
    if case.pile:
        return case.pile, case.reason
    equal = case.op == "=="
    if (to_sympy(case.left, case.assume) == to_sympy(case.right, case.assume)) != equal:
        return NOT_RUN, "SymPy, given nary's form of the two sides, does not make the test pass"
    conditions = _conditions(case)
    left, right = (rewrite(e, RULES, known=lambda c: c == true or c in conditions)
                   for e in (case.left, case.right))
    if (normal(left) == normal(right)) == equal:
        if not equal:
            return PASS, "nary keeps the two sides apart, as SymPy does"
        if normal(case.left) == normal(case.right):
            return PASS, "the two sides are the same expression as written"
        return PASS, "the engine rewrites the two sides to the same expression"
    if case.id in rules.DIFFERENCES:
        kind, note = rules.DIFFERENCES[case.id]
        return DIFFERS, f"{kind}: {note}"
    if equal:
        when = And(*conditions) if len(conditions) > 1 else conditions[0] if conditions else None
        found = numeric.check(case.left, case.right, when)
        if found.value_counterexamples:
            return GAP, ("to review: the numerical check finds different values (SymPy is "
                         "wrong, or the check is)")
        if found.counterexamples:
            sides = sorted({"left" if a is None else "right" for _, a, _ in found.counterexamples})
            return DIFFERS, (f"definition: the {' and the '.join(sides)} side has no value at a "
                             "point where the other has one")
    return GAP, ""


# ---- the report ------------------------------------------------------------


def _percent(part, whole):
    return f"{part} of {whole} ({100 * part / whole:.0f}%)" if whole else "0 of 0"


def _link(case, path):
    lines = f"L{case.line}" + (f"-L{case.end_line}" if case.end_line != case.line else "")
    return f"[{case.id}](https://github.com/sympy/sympy/blob/{rules.SYMPY_COMMIT}/{path}#{lines})"


def _code(text):
    return "`" + text.replace("|", "\\|") + "`"


def render(name):
    """The report for the test file ``name`` of ``rules.FILES``."""
    path, _ = rules.FILES[name]
    scored = [(case, *score(case)) for case in collect(path)]
    count = Counter(pile for _, pile, _ in scored)
    lines = [
        "<!-- Written by `python -m scoreboard.report`; do not edit. -->",
        f"# SymPy's `{path}` on nary",
        "",
        f"SymPy {rules.SYMPY_VERSION}. {len(scored)} cases: one for each `==` or `!=` that an "
        "assert makes when the test runs.",
        "",
        "| | passing |",
        "|---|---|",
        f"| cases nary can write, differences left out | "
        f"{_percent(count[PASS], count[PASS] + count[GAP])} |",
        f"| the same, with the cases nary cannot write yet | "
        f"{_percent(count[PASS], count[PASS] + count[GAP] + count[MISSING])} |",
        "",
        "| pile | cases | meaning |",
        "|---|---|---|",
    ]
    lines += [f"| {pile} | {count[pile]} | {meaning} |" for pile, meaning in rules.PILES.items()]
    passing = Counter(reason for _, pile, reason in scored if pile == PASS)
    lines += ["", "Passing, by how: " + "; ".join(f"{n} where {how}" for how, n in
                                                   passing.most_common()) + "."]

    def section(pile, title, group, show_reason):
        cases = [(c, reason) for c, p, reason in scored if p == pile]
        if not cases:
            return
        lines.extend(["", f"## {title}: {len(cases)}"])
        groups = Counter(group(c, reason) for c, reason in cases)
        for key, n in sorted(groups.items(), key=lambda g: (-g[1], g[0])):
            lines.extend(["", f"**{key}** ({n})", ""])
            for c, reason in cases:
                if group(c, reason) == key:
                    note = f": {reason}" if show_reason and reason else ""
                    form = f", in nary {_code(f'{c.left!r} {c.op} {c.right!r}')}" if c.op else ""
                    lines.append(f"- {_link(c, path)} {_code(c.source)}{form}{note}")

    by_function = lambda c, reason: c.function  # noqa: E731
    by_reason = lambda c, reason: reason        # noqa: E731
    section(GAP, "Gaps, by test function", by_function, True)
    section(DIFFERS, "Differences", by_reason, False)
    section(PASS, "Passing", by_reason, False)
    section(MISSING, "Not expressible yet", by_reason, False)
    section(NOT_APPLICABLE, "Not applicable", by_reason, False)
    section(NOT_RUN, "Not run", by_reason, False)
    return "\n".join(lines) + "\n"


def write():
    for name in rules.FILES:
        path = HERE / f"{name}.md"
        path.write_text(render(name), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    write()

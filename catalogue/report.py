"""Counts for the catalogue, in Markdown: ``python -m catalogue.report``.

Entries by area and by tag, how many today's engine reaches, how many are
proved in Lean, the mismatches by kind, and the mismatch questions.
"""

from collections import Counter

from .engine import reaches
from .entries import ENTRIES
from .entry import TAGS
from .lean import proved
from .mismatches import KINDS, MISMATCHES


def report():
    passing = {e.name for e in ENTRIES if reaches(e)}
    lean = set(proved())
    lines = [
        f"- entries: {len(ENTRIES)}; today's engine reaches {len(passing)}; "
        f"proved in Lean {len(lean)}, stated only {len(ENTRIES) - len(lean)}",
        f"- entries with SymPy assumptions: {sum(bool(e.assume) for e in ENTRIES)}; "
        f"through a SymPy call rather than automatic evaluation: "
        f"{sum(e.sympy != 'auto' for e in ENTRIES)}",
        f"- marked as needing open PR #27: {sum('#27' in e.needs for e in ENTRIES)}",
        "",
        "| tag | entries | engine reaches | proved in Lean |",
        "|---|---|---|---|",
    ]
    for tag in TAGS:
        names = [e.name for e in ENTRIES if tag in e.tags]
        lines.append(f"| {tag} | {len(names)} | {len(passing & set(names))} | "
                     f"{len(lean & set(names))} |")
    areas = Counter(e.area for e in ENTRIES)
    lines += ["", "By area: " + ", ".join(f"{a} {c}" for a, c in areas.items()), ""]
    kinds = Counter(m.kind for m in MISMATCHES)
    lines.append(f"- mismatches: {len(MISMATCHES)} ("
                 + ", ".join(f"{k} {kinds[k]}" for k in KINDS if kinds[k]) + "); "
                 f"rejected SymPy results: {kinds['rejected']}")
    lines += ["", "Engine reaches: " + ", ".join(e.name for e in ENTRIES if e.name in passing)]
    lines += ["", "Mismatch questions:", ""]
    for m in MISMATCHES:
        if not m.question.startswith(("As ", "None expected", "Same, ")):
            lines.append(f"- **{m.name}** ({m.kind}): `{m.sympy}` gives `{m.sympy_gives}`. "
                         f"{m.question}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

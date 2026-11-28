"""Counts for the catalogue, in Markdown: ``python -m catalogue.report``.

Entries by status; for the accepted ones, by area and by tag, how many
today's engine reaches and how many are proved in Lean; the rejected and
undecided ones by kind, and the questions of the undecided ones.
"""

from collections import Counter

from .engine import reaches
from .entries import ENTRIES, with_status
from .entry import AREAS, KINDS, STATUSES, TAGS
from .lean import proved


def _counts(counter, keys):
    return ", ".join(f"{k} {counter[k]}" for k in keys if counter[k])


def report():
    accepted = with_status("accepted")
    others = with_status("rejected", "undecided")
    passing = {e.name for e in accepted if reaches(e)}
    lean = set(proved())
    statuses = Counter(e.status for e in ENTRIES)
    lines = [
        f"- entries: {len(ENTRIES)} ({_counts(statuses, STATUSES)})",
        f"- accepted: today's engine reaches {len(passing)} of {len(accepted)}; "
        f"proved in Lean {len(lean)}, stated only {len(accepted) - len(lean)}",
        f"- accepted with SymPy assumptions: {sum(bool(e.assume) for e in accepted)}; "
        f"through a SymPy call rather than automatic evaluation: "
        f"{sum(e.sympy != 'auto' for e in accepted)}",
        f"- accepted, marked as needing open PR #27: {sum('#27' in e.needs for e in accepted)}",
    ]
    for status in ("rejected", "undecided"):
        group = with_status(status)
        kinds = Counter(e.kind for e in group)
        numeric = Counter(e.numeric or "no nary form" for e in group)
        lines.append(f"- {status}: {len(group)}, by kind: {_counts(kinds, KINDS)}; "
                     f"numerical check finds: "
                     f"{_counts(numeric, ('value', 'definedness', 'none', 'no nary form'))}")
    lines += [
        "",
        "Accepted entries by tag:",
        "",
        "| tag | accepted | engine reaches | proved in Lean |",
        "|---|---|---|---|",
    ]
    for tag in TAGS:
        names = {e.name for e in accepted if tag in e.tags}
        lines.append(f"| {tag} | {len(names)} | {len(passing & names)} | {len(lean & names)} |")
    lines += ["", "By area:", "", "| area | accepted | rejected | undecided |", "|---|---|---|---|"]
    for area in AREAS:
        row = Counter(e.status for e in ENTRIES if e.area == area)
        if row:
            lines.append(f"| {area} | {row['accepted']} | {row['rejected']} | "
                         f"{row['undecided']} |")
    lines += ["", "Engine reaches: " + ", ".join(e.name for e in accepted if e.name in passing)]
    lines += ["", "Rejected: " + ", ".join(f"`{e.sympy_source}`" for e in others
                                           if e.status == "rejected")]
    lines += ["", "Undecided entries, questions for Tilo:", ""]
    for e in with_status("undecided"):
        if not e.question.startswith(("As ", "None expected", "Same, ")):
            lines.append(f"- **{e.name}** ({e.kind}): `{e.sympy_source}` gives "
                         f"`{e.sympy_gives}`. {e.question}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())

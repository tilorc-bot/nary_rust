"""satsimp's tables, translated to nary rules when they are loaded.

    >>> tables = trigsimp_tables()
    >>> tables.rows["normalize"]
    [Row(Rule(tan(u), Mul(Pow(cos(u), -1), sin(u))), 'rule', strict=True)]
    >>> tables.report.translated, len(tables.report.skipped)
    (21, 47)

A row that is not translated is counted with everything it lacks.

    >>> tables.report.lacking().most_common(2)
    [('function cosh', 26), ('function sinh', 24)]

needs orders what nary lacks by the rows each addition would translate.

    >>> tables.report.needs()[:3]
    [('function Abs', 5), ('function cot', 9), ('function atan', 11)]
"""

from collections import Counter
from functools import cache
from typing import NamedTuple

import sympy

from nary.logic import And, true
from nary.rules import rule

from .prove import definedness, prover
from .translate import Untranslatable, from_sympy, head_named, head_of, lacking

__all__ = ["Report", "Row", "refine_tables", "translate", "trigsimp_tables"]


class Row(NamedTuple):
    rule: object
    kind: str
    strict: bool
    opaque: tuple = ()

    def __repr__(self):
        return f"Row({self.rule!r}, {self.kind!r}, strict={self.strict})"


class Tables(NamedTuple):
    rows: dict
    report: object


class Report:
    def __init__(self):
        self.rows = {}

    def add(self, row, kind, opaque=()):
        key = tuple(sympy.sympify(t) for t in row if t is not None)
        if key not in self.rows:
            try:
                self.rows[key] = translate(row, kind, opaque)
            except Untranslatable as error:
                self.rows[key] = error.reason
        found = self.rows[key]
        return found._replace(kind=kind, opaque=opaque) if isinstance(found, Row) else None

    @property
    def translated(self):
        return sum(isinstance(r, Row) for r in self.rows.values())

    @property
    def skipped(self):
        return {k: r for k, r in self.rows.items() if not isinstance(r, Row)}

    def lacking(self):
        return Counter(reason for reasons in self.skipped.values() for reason in reasons)

    def needs(self):
        remaining, added, order = list(self.skipped.values()), set(), []
        while remaining:
            unlocked = Counter(next(iter(r - added)) for r in remaining if len(r - added) == 1)
            counts = unlocked or Counter(x for r in remaining for x in r - added)
            item = min(counts, key=lambda x: (-counts[x], x))
            added.add(item)
            remaining = [r for r in remaining if not r <= added]
            order.append((item, len(self.skipped) - len(remaining)))
        return order


def translate(row, kind="rule", opaque=()):
    lhs, rhs, condition = (sympy.sympify(t) for t in row[:3])
    missing = set().union(*(lacking(t, wildcards=True) for t in (lhs, rhs, condition)))
    if len(row) > 3 and row[3] is not None:
        missing.add("row with unless")
    if missing:
        raise Untranslatable(frozenset(missing))
    lhs, rhs, condition = (from_sympy(t, wildcards=True) for t in (lhs, rhs, condition))
    try:
        r = rule(lhs, rhs, when=None if condition == true else condition)
    except (TypeError, ValueError) as error:
        raise Untranslatable(frozenset({f"nary rule: {error}"})) from None
    return Row(r, kind, _strict(r), opaque)


def _strict(r):
    left, right = definedness(r.pattern), definedness(r.replacement)
    if left is None or right is None:
        return False
    given = right if r.condition is None else And(r.condition, right)
    try:
        return prover(given)(left)
    except Untranslatable:
        return False


def _parts(parts):
    return parts if isinstance(parts, tuple) else (parts,)


@cache
def refine_tables():
    from satsimp.engine.spec import Identities
    from satsimp.methods.refine.identities import families, family_spec

    report, handlers = Report(), {}
    for family in families():
        for key, parts in family_spec(family).handlers.items():
            for part in _parts(parts):
                kind = "identity" if isinstance(part, Identities) else "rule"
                opaque = tuple(filter(None, map(head_of, getattr(part, "opaque", None) or ())))
                rows = [r for r in (report.add(row, kind, opaque) for row in part.rows) if r]
                if rows and head_named(key) is not None:
                    handlers.setdefault(head_named(key), []).append(rows)
    return Tables(handlers, report)


@cache
def trigsimp_tables():
    from satsimp.methods.trigsimp import wiring
    from satsimp.methods.trigsimp.rules import normal, pythagorean, quotients

    report = Report()

    def table(rows, kind):
        return [r for r in (report.add(row, kind) for row in rows) if r]

    return Tables({
        "normalize": table(normal.RULES, "rule"),
        "conditional": table(wiring.CONDITIONAL, "rule"),
        "quotients": table(quotients.RULES, "rule"),
        "pythagorean": table(pythagorean.SINE_COSINE, "substitution"),
        "substitutions": table(wiring.SUBSTITUTIONS, "substitution"),
        "heads": tuple(filter(None, map(head_of, wiring.HEADS))),
    }, report)

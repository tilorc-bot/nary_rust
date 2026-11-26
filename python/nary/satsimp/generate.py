"""satsimp's tables translated to nary rules, written as tables.py by python -m nary.satsimp.generate.

    >>> rows, report = trigsimp_tables()
    >>> rows["normalize"]
    ('rule', (), [Row(Rule(tan(u), Mul(Pow(cos(u), -1), sin(u))), 'rule', strict=True)])
    >>> report.translated, len(report.skipped)
    (21, 47)

A row that is not translated is counted with everything it lacks.

    >>> report.lacking().most_common(2)
    [('function cosh', 26), ('function sinh', 24)]

needs orders what nary lacks by the rows each addition would translate.

    >>> report.needs()[:3]
    [('function Abs', 5), ('function cot', 9), ('function atan', 11)]
"""

import json
from collections import Counter
from importlib.metadata import distribution
from pathlib import Path

import sympy

import nary
import nary.logic
from nary.logic import true
from nary.rules import rule

from .rows import Row, strict
from .translate import Untranslatable, from_sympy, head_named, head_of, lacking

__all__ = ["Report", "refine_tables", "source", "translate", "trig_heads", "trigsimp_tables"]


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
    return Row(r, kind, strict(r), opaque)


def _parts(parts):
    return parts if isinstance(parts, tuple) else (parts,)


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
                    handlers.setdefault(head_named(key), []).append((kind, opaque, rows))
    return handlers, report


def trigsimp_tables():
    from satsimp.methods.trigsimp import wiring
    from satsimp.methods.trigsimp.rules import normal, pythagorean, quotients

    report = Report()

    def table(rows, kind):
        return kind, (), [r for r in (report.add(row, kind) for row in rows) if r]

    return {
        "normalize": table(normal.RULES, "rule"),
        "conditional": table(wiring.CONDITIONAL, "rule"),
        "quotients": table(quotients.RULES, "rule"),
        "pythagorean": table(pythagorean.SINE_COSINE, "substitution"),
        "substitutions": table(wiring.SUBSTITUTIONS, "substitution"),
    }, report


def trig_heads():
    from satsimp.methods.trigsimp import wiring

    return tuple(filter(None, map(head_of, wiring.HEADS)))


def _commit(name):
    return json.loads(distribution(name).read_text("direct_url.json"))["vcs_info"]["commit_id"]


def _names(e, found):
    if e.head is None:
        if not e.is_literal:
            found[repr(e)] = e
    else:
        _names(e.head, found)
        for arg in e.args:
            _names(arg, found)
    return found


def _declaration(s):
    if s.kind.inputs is None:
        return f'{s!r} = NumberKind("{s!r}")'
    return f'{s!r} = FunctionKind({_tuple(s.kind.inputs)}, NumberKind)("{s!r}")'


def _by_type(name):
    return not name.isupper(), not name[0].isupper(), name


def _imports(constants):
    logic = sorted(n for n, c in constants.items() if getattr(nary.logic, n, None) is c)
    core = {n for n, c in constants.items() if getattr(nary, n, None) is c} - set(logic)
    return [f"from nary import {', '.join(sorted(core | {'FunctionKind', 'NumberKind'}, key=_by_type))}",
            f"from nary.logic import {', '.join(sorted(logic, key=_by_type))}"]


def _tuple(items):
    return f"({', '.join(map(repr, items))}{',' if len(items) == 1 else ''})"


def _part(kind, opaque, rows, indent):
    return [f'("{kind}", {_tuple(opaque)}, [',
            *(f"{indent}    ({r.rule.pattern!r}, {r.rule.replacement!r}, {r.rule.condition or true!r}),"
              for r in rows),
            f"{indent}]),"]


def source():
    refine, trigsimp, heads = refine_tables()[0], trigsimp_tables()[0], trig_heads()
    found = {}
    for kind, opaque, rows in [p for parts in refine.values() for p in parts] + list(trigsimp.values()):
        for e in (*opaque, *(t for r in rows for t in (r.rule.pattern, r.rule.replacement, r.rule.condition or true))):
            _names(e, found)
    for e in (*refine, *heads):
        _names(e, found)
    symbols = {n: e for n, e in found.items() if e.is_symbol}
    lines = [
        *_imports({n: e for n, e in found.items() if not e.is_symbol}), "",
        f'SOURCE = "satsimp {_commit("satsimp")}"',
        f'SYMPY = "{sympy.__version__}"', "",
        *(_declaration(symbols[n]) for n in sorted(symbols)), "",
        "REFINE = {",
    ]
    for head, parts in refine.items():
        lines += [f"    {head!r}: ["]
        for part in parts:
            first, *rest = _part(*part, "        ")
            lines += [f"        {first}", *rest]
        lines += ["    ],"]
    lines += ["}", "", "TRIGSIMP = {"]
    for name, part in trigsimp.items():
        first, *rest = _part(*part, "    ")
        lines += [f'    "{name}": {first}', *rest]
    lines += ["}", "", f"TRIG_HEADS = {_tuple(heads)}", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    (Path(__file__).parent / "tables.py").write_text(source())

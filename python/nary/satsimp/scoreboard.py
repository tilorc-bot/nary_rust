"""Run as python -m nary.satsimp.scoreboard CASES [CATALOGUE ...]; results are compared with Add and Mul flattened and sorted.

    >>> import nary as nr
    >>> x, y = nr.NumberKind("x"), nr.NumberKind("y")
    >>> normal(nr.Add(y, nr.Mul(x, 2))) == normal(nr.Add(nr.Mul(2, x), y))
    True

A condition is plain when its relations compare symbols, literals and constants.

    >>> plain(nr.Gt(x, 0)), plain(nr.Eq(nr.re(x), x)), plain(nr.Ne(nr.cos(x), 0))
    (True, True, False)
"""

import json
import sys
from collections import Counter

import nary as nr
from nary.logic import And, true
from nary.rules import is_flat, is_unordered

from .methods import PROVIDERS, Simplifier
from .record import load
from .translate import Untranslatable, from_sympy, lacking, to_sympy

__all__ = ["normal", "plain", "score_catalogue", "score_tests"]

SETTINGS = [(name, strict, rows) for rows in (True, False) for name in PROVIDERS
            if rows or name != "none" for strict in (True, False)]


def normal(e):
    if e.head is None:
        return e
    head, args = normal(e.head), [normal(a) for a in e.args]
    if head.is_constant and head.kind.inputs is not None:
        if is_flat(head):
            args = [b for a in args for b in (a.args if a.head == head else (a,))]
        if is_unordered(head):
            args.sort(key=repr)
    return head(*args)


def _atomic(e):
    return e.head is None or (e.head == nr.re and e.args[0].head is None)


def plain(condition):
    if condition.head in (nr.Eq, nr.Ne, nr.Lt, nr.Gt, nr.Le, nr.Ge):
        return all(map(_atomic, condition.args))
    return condition.head is None or all(map(plain, condition.args))


def _run(simplifier, method, e, assumptions):
    if method == "refine":
        return simplifier.refine(e, assumptions)
    if method == "trigsimp":
        return simplifier.trigsimp(e, assumptions)
    return simplifier.trigsimp(simplifier.refine(e, assumptions), assumptions)


def _tally(simplifiers):
    out = {}
    for setting, s in simplifiers.items():
        out[setting] = {"loops": len(s.loops), "refused": len(s.refused),
                        "proved plain": sum(map(plain, s.proved)),
                        "proved compound": sum(not plain(c) for c in s.proved)}
    return out


def score_tests(cases):
    outside, inside = Counter(), []
    for method, expr, assumptions, result in cases:
        missing = lacking(expr) | lacking(assumptions) | lacking(result)
        if missing:
            outside[frozenset(missing)] += 1
        else:
            inside.append((method, *map(from_sympy, (expr, assumptions, result)), result))
    simplifiers = {setting: Simplifier(PROVIDERS[setting[0]], *setting[1:]) for setting in SETTINGS}
    scores = {setting: Counter() for setting in SETTINGS}
    for method, expr, assumptions, expected, result in inside:
        rewritten = normal(expected) != normal(expr)
        for setting, simplifier in simplifiers.items():
            got = _run(simplifier, method, expr, assumptions)
            score = scores[setting]
            score[f"{method} {'rewritten' if rewritten else 'unchanged'}"] += 1
            if normal(got) == normal(expected):
                score[f"{method} same"] += rewritten
            elif to_sympy(got) == result:
                score[f"{method} same after SymPy evaluation"] += rewritten
            elif not rewritten:
                score[f"{method} changed where satsimp did not"] += 1
    return {"cases": len(cases), "outside": outside, "scores": scores,
            "engine": _tally(simplifiers)}


def _nary(text, symbols):
    namespace = {**vars(nr), **vars(nr.logic)}
    namespace.update({name: getattr(nr, kind)(name) for name, kind in symbols.items()})
    value = eval(text, namespace)
    return nr.NumberKind(value) if isinstance(value, int) else value


def score_catalogue(entries):
    simplifiers = {setting: Simplifier(PROVIDERS[setting[0]], *setting[1:]) for setting in SETTINGS}
    scores = {setting: Counter() for setting in SETTINGS}
    reached = {setting: [] for setting in SETTINGS}
    outside = []
    for entry in entries:
        try:
            e, expected, *conditions = (_nary(t, entry["symbols"])
                                        for t in (entry["input"], entry["expected"], *entry["conditions"]))
        except (NameError, AttributeError, TypeError):
            outside.append(entry["name"])
            continue
        assumptions = And(*conditions) if conditions else true
        for setting, simplifier in simplifiers.items():
            try:
                got = _run(simplifier, "both", e, assumptions)
            except Untranslatable:
                got = e
            if normal(got) == normal(expected):
                reached[setting].append(entry["name"])
            scores[setting]["entries"] += 1
    return {"entries": len(entries), "outside": outside, "reached": reached,
            "engine": _tally(simplifiers)}


def _name(setting):
    provider, strict, rows = setting
    return f"{provider}{'' if rows else ' alone'} {'strict' if strict else 'loose'}"


def main(argv):
    with open(argv[0]) as file:
        report = score_tests(load(file))
    report["outside"] = sorted(([sorted(k), v] for k, v in report["outside"].items()), key=lambda r: -r[1])
    report["scores"] = {_name(k): dict(c) for k, c in report["scores"].items()}
    report["engine"] = {_name(k): c for k, c in report["engine"].items()}
    for path in argv[1:]:
        with open(path) as file:
            found = score_catalogue(json.load(file))
        found["reached"] = {_name(k): v for k, v in found["reached"].items()}
        found["engine"] = {_name(k): c for k, c in found["engine"].items()}
        report[path] = found
    json.dump(report, sys.stdout, indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1:])

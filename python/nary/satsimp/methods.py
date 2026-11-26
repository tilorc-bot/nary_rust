"""refine and trigsimp on nary expressions, with satsimp's rows.

    >>> import nary as nr
    >>> from nary.logic import true
    >>> x = nr.NumberKind("x")
    >>> plain, sympy = Simplifier(none), Simplifier(sympy_round_trip)
    >>> e = nr.sin(x) ** 2 + nr.cos(x) ** 2
    >>> plain.trigsimp(e), sympy.trigsimp(e)
    (Add(Pow(sin(x), 2), Pow(cos(x), 2)), 1)
    >>> plain.trigsimp(nr.sin(x) / nr.cos(x))
    tan(x)
    >>> plain.refine(nr.E ** x), plain.refine(nr.Pow(nr.Pow(x, 2), 3), nr.Gt(x, 0))
    (exp(x), Pow(x, Mul(3, 2)))

The round trip may give a value where there was none, which strict refuses.

    >>> e = nr.tan(x) ** 2 - nr.cos(x) ** -2
    >>> sympy.trigsimp(e), Simplifier(sympy_round_trip, strict=False).trigsimp(e)
    (Add(Pow(tan(x), 2), Mul(-1, Pow(cos(x), -2))), -1)
    >>> sympy.refused[0]
    (Add(Pow(tan(x), 2), Mul(-1, 1), Mul(-1, Pow(tan(x), 2))), -1)

The native canonical form, autosimp, takes the assumptions as known conditions.

    >>> native = Simplifier(autosimp)
    >>> native.trigsimp(nr.sin(x) ** 2 + nr.cos(x) ** 2), native.refine(x / x), native.refine(x / x, nr.Ne(x, 0))
    (1, Pow(x, 0), 1)
"""

from nary import Add, Mul
from nary.autosimp import autosimp
from nary.logic import And, true

from .engine import Engine, identity_handler, rule_handler, size
from .prove import prover
from .rows import refine_tables, trigsimp_tables
from .substitute import substitution_handler
from .translate import from_sympy, to_sympy

__all__ = ["PROVIDERS", "Simplifier", "autosimp", "none", "sympy_round_trip"]


def none(e, known=()):
    return e


def sympy_round_trip(e, known=()):
    return from_sympy(to_sympy(e))


PROVIDERS = {"none": none, "sympy": sympy_round_trip, "native": autosimp}


def _conjuncts(condition):
    if condition == true:
        return frozenset()
    if condition.head == And:
        return frozenset().union(*map(_conjuncts, condition.args))
    return frozenset([condition])


def _by_head(rows):
    tables = {}
    for row in rows:
        tables.setdefault(row.rule.pattern.head, []).append(row)
    return {head: [rule_handler(rs)] for head, rs in tables.items()}


def _count(e, heads):
    if e.head is None:
        return 0
    return (e.head in heads) + sum(_count(arg, heads) for arg in e.args)


def _smallest(rows, measure):
    handlers = [rule_handler([row]) for row in rows]

    def handler(e, engine):
        found = [new for new in (h(e, engine) for h in handlers) if new is not None]
        return min(found, key=measure) if found else None

    return handler


class Simplifier:
    def __init__(self, canonical=none, strict=True, rows=True):
        self.canonical, self.strict, self.rows = canonical, strict, rows
        self.loops, self.refused, self.proved = [], [], []

    def _run(self, handlers, e, known, conjuncts):
        def canonical(e):
            return self.canonical(e, conjuncts)

        engine = Engine(handlers if self.rows else {}, known, canonical, self.strict)
        result = engine(e)
        self.loops += engine.loops
        self.refused += engine.refused
        return result

    def refine(self, e, assumptions=true):
        handlers = {
            head: [(rule_handler if rows[0].kind == "rule" else identity_handler)(rows)
                   for rows in parts]
            for head, parts in refine_tables().rows.items()
        }
        return self._run(handlers, e, prover(assumptions, self.proved), _conjuncts(assumptions))

    def trigsimp(self, e, assumptions=true):
        tables = trigsimp_tables().rows
        heads = tables["heads"]
        if not _count(e, heads):
            return e

        def measure(e):
            return _count(e, heads), size(e)

        known, conjuncts = prover(assumptions, self.proved), _conjuncts(assumptions)

        def run(handlers, e):
            return self._run(handlers, e, known, conjuncts)

        conditional = _by_head(tables["conditional"])
        normalize = {**_by_head(tables["normalize"]), **conditional}
        pythagorean = substitution_handler(tables["pythagorean"], measure, heads)
        substitute = substitution_handler(tables["substitutions"], measure, heads)
        simplify = {**conditional, Add: [substitute],
                    Mul: [_smallest(tables["quotients"], measure), substitute]}
        best, best_m = e, measure(e)
        while True:
            normal = run(normalize, best)
            out = min(run(simplify, normal),
                      run(simplify, run({Add: [pythagorean], Mul: [pythagorean]}, normal)),
                      key=measure)
            if not measure(out) < best_m:
                return best
            best, best_m = out, measure(out)

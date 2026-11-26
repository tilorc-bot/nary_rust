"""refine and trigsimp on nary expressions, with satsimp's rows.

    >>> import nary as nr
    >>> x = nr.NumberKind("x")
    >>> plain, native = Simplifier(none), Simplifier()
    >>> e = nr.sin(x) ** 2 + nr.cos(x) ** 2
    >>> plain.trigsimp(e), native.trigsimp(e)
    (Add(Pow(sin(x), 2), Pow(cos(x), 2)), 1)
    >>> plain.trigsimp(nr.sin(x) / nr.cos(x))
    tan(x)
    >>> plain.refine(nr.E ** x), plain.refine(nr.Pow(nr.Pow(x, 2), 3), nr.Gt(x, 0))
    (exp(x), Pow(x, Mul(3, 2)))

The canonical form, autosimp by default, takes the assumptions as known conditions.

    >>> native.refine(x / x), native.refine(x / x, nr.Ne(x, 0))
    (Pow(x, 0), 1)

A step that gives a value where there was none is refused, unless strict is False.

    >>> e = nr.cos(x) * nr.tan(x) ** 2 / nr.sin(x)
    >>> native.trigsimp(e) == e, Simplifier(strict=False).trigsimp(e)
    (True, tan(x))
"""

from nary import Add, Mul
from nary.autosimp import autosimp
from nary.logic import true

from .engine import Engine, identity_handler, rule_handler
from .measure import count_heads, trig_measure
from .prove import conjuncts, decide, prover
from .rows import refine_tables, trigsimp_tables
from .substitute import substitution_handler
from .tables import TRIG_HEADS

__all__ = ["Simplifier", "none"]


def none(e, known=()):
    return e


def _by_head(rows):
    tables = {}
    for row in rows:
        tables.setdefault(row.rule.pattern.head, []).append(row)
    return {head: [rule_handler(rs)] for head, rs in tables.items()}


def _smallest(rows, measure):
    handlers = [rule_handler([row]) for row in rows]

    def handler(e, engine):
        found = [new for new in (h(e, engine) for h in handlers) if new is not None]
        return min(found, key=measure) if found else None

    return handler


class Simplifier:
    def __init__(self, canonical=autosimp, strict=True, rows=True, decide=decide):
        self.canonical, self.strict, self.rows, self.decide = canonical, strict, rows, decide
        self.loops, self.refused, self.proved = [], [], []

    def _run(self, handlers, e, known, given):
        def canonical(e):
            return self.canonical(e, given)

        engine = Engine(handlers if self.rows else {}, known, canonical, self.strict)
        result = engine(e)
        self.loops += engine.loops
        self.refused += engine.refused
        return result

    def refine(self, e, assumptions=true):
        handlers = {
            head: [(rule_handler if rows[0].kind == "rule" else identity_handler)(rows)
                   for rows in parts]
            for head, parts in refine_tables().items()
        }
        return self._run(handlers, e, self._prover(assumptions), conjuncts(assumptions))

    def _prover(self, assumptions):
        return prover(assumptions, self.proved, self.decide)

    def trigsimp(self, e, assumptions=true):
        tables, heads = trigsimp_tables(), TRIG_HEADS
        if not count_heads(e, heads):
            return e

        measure = trig_measure(heads)
        known, given = self._prover(assumptions), conjuncts(assumptions)

        def run(handlers, e):
            return self._run(handlers, e, known, given)

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

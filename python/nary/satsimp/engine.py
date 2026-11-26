"""The driver: an expression's arguments first, then its canonical form, then the handlers of its head, until nothing changes.

    >>> import nary as nr
    >>> from nary.rules import rule
    >>> from nary.satsimp.prove import prover
    >>> from nary.satsimp.rows import Row
    >>> a, x = nr.NumberKind("a"), nr.NumberKind("x")
    >>> rows = [Row(rule(nr.tan(a), nr.sin(a) / nr.cos(a)), "rule", strict=True)]
    >>> run = Engine({nr.tan: [rule_handler(rows)]}, prover())
    >>> run(nr.tan(x) + nr.tan(nr.tan(x)))
    Add(Mul(sin(x), Pow(cos(x), -1)), Mul(sin(Mul(sin(x), Pow(cos(x), -1))), Pow(cos(Mul(sin(x), Pow(cos(x), -1))), -1)))

A row whose right side may have a value where its left side has none fires only where the left side is proved to have a value, unless strict is False.

    >>> rows = [Row(rule(nr.tan(a) * nr.cos(a), nr.sin(a)), "rule", strict=False)]
    >>> e = nr.tan(x) * nr.cos(x)
    >>> Engine({nr.Mul: [rule_handler(rows)]}, prover())(e)
    Mul(tan(x), cos(x))
    >>> Engine({nr.Mul: [rule_handler(rows)]}, prover(nr.Ne(nr.cos(x), 0)))(e)
    sin(x)
    >>> Engine({nr.Mul: [rule_handler(rows)]}, prover(), strict=False)(e)
    sin(x)

Rows that undo each other stop at a guard, and the input comes back.

    >>> loop = [Row(rule(nr.sin(a), nr.cos(a)), "rule", True), Row(rule(nr.cos(a), nr.sin(a)), "rule", True)]
    >>> handler = rule_handler(loop)
    >>> run = Engine({nr.sin: [handler], nr.cos: [handler]}, prover())
    >>> run(nr.sin(x)), run.loops
    (sin(x), [sin(x)])
"""

from nary import arithmetic_rules  # noqa: F401
from nary.functions import is_lambda
from nary.rewriting import _flatten, _match_top, _substitute, has_a_value

from .measure import identity_measure
from .prove import conjuncts, definedness, implies

__all__ = ["Engine", "identity_handler", "rule_handler", "size"]

MAX_STEPS = 200
MAX_FIRINGS = 5000


class Loop(RecursionError):
    pass


def _identity(e):
    return e


class Engine:
    def __init__(self, handlers, known, canonical=_identity, strict=True):
        self.handlers, self.known, self.canonical, self.strict = handlers, known, canonical, strict
        self.cache, self.active, self.firings = {}, set(), 0
        self.loops, self.refused = [], []

    def __call__(self, e):
        try:
            return self.refine(e)
        except Loop:
            self.loops.append(e)
            return e

    def refine(self, e):
        chain = []
        while e not in self.cache:
            if e in self.active or e in chain or len(chain) > MAX_STEPS:
                raise Loop(e)
            chain.append(e)
            self.active.add(e)
            try:
                new = self._step(e)
            finally:
                self.active.discard(e)
            if new is None:
                self.cache[e] = e
            else:
                e = new
        for old in chain:
            self.cache[old] = self.cache[e]
        return self.cache[e]

    def _step(self, e):
        if e.head is None or is_lambda(e):
            return None
        args = tuple(self.refine(arg) for arg in e.args)
        new = self.normal(e.head(*args) if args != e.args else e)
        if new != e:
            return new
        for handler in self.handlers.get(e.head, ()):
            new = handler(e, self)
            if new is not None and new != e:
                self.firings += 1
                if self.firings > MAX_FIRINGS:
                    raise Loop(e)
                return new
        return None

    def normal(self, e):
        new = self.canonical(e)
        if new == e or not self.strict or self.defined_where(e, new):
            return new
        self.refused.append((e, new))
        return e

    def defined_where(self, old, new):
        before, after = definedness(old), definedness(new)
        if before is None or after is None:
            return False
        return conjuncts(before) <= conjuncts(after) or self.known(implies(after, before))

    def apply(self, row, e):
        rule = row.rule
        for bindings, used in _match_top(rule.pattern, e):
            if rule.condition is not None and not self.known(_substitute(rule.condition, bindings)):
                continue
            if self.strict and not self._sound(row, bindings):
                continue
            replacement = _substitute(rule.replacement, bindings)
            if used is None:
                return replacement
            first = min(used)
            args = [replacement if i == first else arg
                    for i, arg in enumerate(e.args) if i == first or i not in used]
            return _flatten(e.head(*args))
        return None

    def _sound(self, row, bindings):
        if row.strict:
            return all(has_a_value(bindings[v], self.known) for v in row.rule.erased)
        condition = definedness(_substitute(row.rule.pattern, bindings))
        return condition is not None and self.known(condition)


def rule_handler(rows):
    def handler(e, engine):
        e = _flatten(e)
        for row in rows:
            new = engine.apply(row, e)
            if new is not None and new != e:
                return new
        return None

    return handler


def size(e):
    return 1 + sum(size(arg) for arg in e.args) if e.head is not None else 1


def _has(e, heads):
    return e.head is not None and (e.head in heads or any(_has(arg, heads) for arg in e.args))


def identity_handler(rows):
    busy = []
    kind, heads, modulus = rows[0].measure

    def handler(e, engine):
        if busy:
            return None
        e = _flatten(e)
        measure = identity_measure(kind, {*heads, e.head} if kind == "default" else heads, modulus, engine.known)
        before = measure(e)
        for row in rows:
            new = engine.apply(row, e)
            if new is None:
                continue
            busy.append(row)
            try:
                new = Engine(engine.handlers, engine.known, engine.canonical, engine.strict)(new)
            finally:
                busy.pop()
            if not _has(new, row.opaque) and measure(new) < before:
                return new
        return None

    return handler

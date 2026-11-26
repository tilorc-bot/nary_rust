"""normalise applies the laws declared for each head, from the leaves up.

    >>> from nary import BoolKind, I, Ne, NumberKind, Pow, log, sin
    >>> from nary.logic import And, Not, Or, false, true
    >>> from nary.normalising import normalise
    >>> x, y, p, q = NumberKind("x"), NumberKind("y"), BoolKind("p"), BoolKind("q")
    >>> normalise(y + x + 0 + x * 1), normalise(x * y * x * 2 * 3)
    (Add(y, Mul(2, x)), Mul(6, y, Pow(x, 2)))
    >>> normalise(x / 2 + x / 3), normalise(Pow(12, Pow(2, -1)) * I * I)
    (Mul(5, Pow(6, -1), x), Mul(-2, Pow(3, Pow(2, -1))))
    >>> normalise(And(q, Or(p, false), q, true)), normalise(Not(Not(p)))
    (And(p, q), p)

A part is erased only when it has a value.

    >>> normalise(sin(x) * 0), normalise(log(x) * 0), normalise(log(x) - log(x))
    (0, Mul(0, log(x)), Mul(0, log(x)))

Powers merge where both sides have a value at the same points.

    >>> normalise(x * x), normalise(Pow(x, -1) * Pow(x, -1)), normalise(x * x / x)
    (Pow(x, 2), Pow(x, -2), Mul(Pow(x, -1), Pow(x, 2)))
    >>> normalise(x / x), normalise(x / x, known=lambda condition: condition == Ne(x, 0))
    (Pow(x, 0), 1)
"""

from . import arithmetic_rules, logic_rules  # noqa: F401
from ._core import Expr
from ._identities import (
    Law, absorbing, associative, commutative, heads, idempotent, identities, identity,
    involution, repeats,
)
from ._numbers import evaluate, is_number
from .domains import domain_of
from .functions import is_lambda
from .logic import true
from .rewriting import _has_a_value

__all__ = ["normalise"]


def normalise(e, known=None):
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    return _Normaliser(known or (lambda condition: False)).normal(e)


def _element(head, value):
    return value if isinstance(value, Expr) else head.kind.output(value)


def _flatten(head, args):
    return [part for arg in args for part in (arg.args if arg.head == head else (arg,))]


def _key(e):
    if e.is_literal:
        return 0, type(e.value).__name__, e.value
    if e.is_constant:
        return 1, e.name
    if e.is_symbol:
        return 2, e.name, e.kind.name
    return 3, _key(e.head), tuple(_key(arg) for arg in e.args)


class _Normaliser:
    def __init__(self, known):
        self.known, self.done, self.numbers, self.tables, self.through = known, {}, {}, {}, {}
        for F in heads():
            law = self.laws(F).get(repeats)
            if law is not None:
                self.through.setdefault(law.args[0].head, []).append((F, law))

    def laws(self, head):
        if head not in self.tables:
            items = identities(head)
            self.tables[head] = {item.of: item for item in items if isinstance(item, Law)}
        return self.tables[head]

    def number(self, e):
        if e not in self.numbers:
            self.numbers[e] = is_number(e)
        return self.numbers[e]

    def order(self, e):
        return not self.number(e), _key(e)

    def normal(self, e):
        if e.head is None or is_lambda(e):
            return e
        if e not in self.done:
            head = self.normal(e.head)
            self.done[e] = self.node(head, [self.normal(arg) for arg in e.args])
        return self.done[e]

    def holds(self, condition):
        condition = self.normal(condition)
        return condition == true or self.known(condition) is True

    def has_a_value(self, e):
        return _has_a_value(e, self.holds)

    def node(self, head, args):
        laws = self.laws(head)
        if associative in laws:
            args = _flatten(head, args)
        if commutative in laws:
            args = self.fold(head, sorted(args, key=self.order))
        elif args and all(map(self.number, args)):
            value = evaluate(head, args)
            if value is not None and value != head(*args):
                return self.normal(value)
        if repeats in laws:
            merged = self.merge(laws[repeats], args, commutative in laws)
            if merged is not None:
                return self.node(head, merged)
        if idempotent in laws:
            args = [arg for i, arg in enumerate(args) if arg not in args[:i]]
        if absorbing in laws:
            z = _element(head, laws[absorbing].args[0])
            if z in args and all(self.has_a_value(arg) for arg in args if arg != z):
                return z
        if identity in laws and associative in laws:
            unit = _element(head, laws[identity].args[0])
            args = [arg for arg in args if arg != unit]
            if len(args) < 2:
                return args[0] if args else unit
        if commutative in laws:
            args = sorted(args, key=self.order)
        if involution in laws and args[0].head == head:
            return args[0].args[0]
        return self.counted(head(*args))

    def fold(self, head, args):
        pool, changed = [], False
        for a in filter(self.number, args):
            for k, b in enumerate(pool):
                value = evaluate(head, (b, a))
                if value is not None and len(_flatten(head, [value])) < 2:
                    pool[k], changed = self.normal(value), True
                    break
            else:
                pool.append(a)
        if not changed:
            return args
        return self.fold(head, pool + [arg for arg in args if not self.number(arg)])

    def split(self, term, law):
        form, count = law.args
        if term.head != form.head:
            return term, count.kind(1)
        if commutative in self.laws(form.head):
            numbers = [arg for arg in term.args if self.number(arg)]
            rest = [arg for arg in term.args if not self.number(arg)]
            base = rest[0] if len(rest) == 1 else form.head(*rest)
            return base, self.node(form.head, numbers) if numbers else count.kind(1)
        (base,) = [arg for arg, p in zip(term.args, form.args) if p != count]
        (n,) = [arg for arg, p in zip(term.args, form.args) if p == count]
        return base, n

    def merge(self, law, args, any_order):
        merged, groups, changed = [], {}, False
        for arg in args:
            base = None if self.number(arg) else self.split(arg, law)[0]
            k = groups.get(base)
            if k is not None:
                combined = self.combine(merged[k], arg, law)
                if combined is not None:
                    merged[k], changed = combined, True
                    continue
            if not any_order:
                groups = {}
            if base is not None:
                groups[base] = len(merged)
            merged.append(arg)
        return merged if changed else None

    def combine(self, a, b, law):
        form, count = law.args
        G = form.head
        (base, m), (other, n) = self.split(a, law), self.split(b, law)
        total = self.normal(m + n)
        if base != other or commutative in self.laws(G) and not self.number(total):
            return None
        merged = G(*(total if p == count else base for p in form.args))
        return self.normal(merged) if self.alike([a, b], merged, G) else None

    def alike(self, parts, merged, G):
        before = [domain_of(part) for part in parts if part.head == G]
        after = [domain_of(merged)]
        if None in before + after:
            return False
        before = {self.normal(c) for c in before} - {true}
        after = {self.normal(c) for c in after} - {true}
        return before == after or all(self.known(c) is True for c in before | after)

    def counted(self, e):
        if self.number(e):
            return e
        for F, law in self.through.get(e.head, ()):
            base, n = self.split(e, law)
            if n == n.kind(1):
                return base
            if n == n.kind(0) and identity in self.laws(F) and self.has_a_value(e):
                return _element(F, self.laws(F)[identity].args[0])
        return e

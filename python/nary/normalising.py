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
from . import _numbers
from ._core import Expr
from ._identities import (
    Law, absorbing, associative, commutative, heads, idempotent, identities, identity,
    involution, repeats,
)
from .domains import domain_of
from .functions import is_lambda
from .kinds import Many
from .logic import true
from .rewriting import _has_a_value

__all__ = ["normalise"]


def normalise(e, known=None):
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    return _Normaliser(known or (lambda condition: False)).normal(e)


def _element(head, value):
    return value if isinstance(value, Expr) else head.kind.output(value)


def _variadic(head):
    inputs = head.kind.inputs
    return bool(inputs) and inputs[-1].family is Many


def _key(e):
    if e.is_literal:
        return 0, type(e.value).__name__, e.value
    if e.is_constant:
        return 1, e.name
    if e.is_symbol:
        return 2, e.name, e.kind.name
    return 3, _key(e.head), tuple(_key(arg) for arg in e.args)


class _Restart:
    def __init__(self, args):
        self.args = args


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
            self.numbers[e] = _numbers.is_number(e)
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

    def alike(self, parts, whole):
        before = [domain_of(part) for part in parts]
        after = [domain_of(whole)]
        if None in before + after:
            return False
        before = {self.normal(c) for c in before} - {true}
        after = {self.normal(c) for c in after} - {true}
        return before == after or all(self.known(c) is True for c in before | after)

    def node(self, head, args):
        laws = self.laws(head)
        for needs, step in _STEPS:
            if all(law in laws for law in needs):
                result = step(self, head, laws, args)
                if isinstance(result, Expr):
                    return result
                if isinstance(result, _Restart):
                    return self.node(head, result.args)
                args = result
        return head(*args)


def _flatten(n, head, laws, args):
    return [part for arg in args for part in (arg.args if arg.head == head else (arg,))]


def _evaluate(n, head, laws, args):
    if not args or not all(map(n.number, args)):
        return args
    value = _numbers.evaluate(head, args)
    if value is None or value == head(*args):
        return args
    return n.normal(value)


def _fold(n, head, laws, args):
    pool, changed = [], False
    for a in filter(n.number, args):
        for k, b in enumerate(pool):
            value = _numbers.evaluate(head, (b, a))
            if value is not None and len(_flatten(n, head, laws, [value])) < 2:
                pool[k], changed = n.normal(value), True
                break
        else:
            pool.append(a)
    if not changed:
        return args
    return _fold(n, head, laws, pool + [arg for arg in args if not n.number(arg)])


def _sort(n, head, laws, args):
    return sorted(args, key=n.order)


def _merge_repeats(n, head, laws, args):
    law, any_order = laws[repeats], commutative in laws
    merged, groups, changed = [], {}, False
    for arg in args:
        base = None if n.number(arg) else _split(n, arg, law)[0]
        k = groups.get(base)
        if k is not None:
            combined = _combine(n, merged[k], arg, law)
            if combined is not None:
                merged[k], changed = combined, True
                continue
        if not any_order:
            groups = {}
        if base is not None:
            groups[base] = len(merged)
        merged.append(arg)
    return _Restart(merged) if changed else args


def _split(n, term, law):
    form, count = law.args
    if term.head != form.head:
        return term, count.kind(1)
    if commutative in n.laws(form.head):
        numbers = [arg for arg in term.args if n.number(arg)]
        rest = [arg for arg in term.args if not n.number(arg)]
        base = rest[0] if len(rest) == 1 else form.head(*rest)
        return base, n.node(form.head, numbers) if numbers else count.kind(1)
    (base,) = [arg for arg, p in zip(term.args, form.args) if p != count]
    (k,) = [arg for arg, p in zip(term.args, form.args) if p == count]
    return base, k


def _combine(n, a, b, law):
    form, count = law.args
    (base, k), (other, m) = _split(n, a, law), _split(n, b, law)
    total = n.normal(k + m)
    if base != other or commutative in n.laws(form.head) and not n.number(total):
        return None
    merged = form.head(*(total if p == count else base for p in form.args))
    parts = [part for part in (a, b) if part.head == form.head]
    return n.normal(merged) if n.alike(parts, merged) else None


def _count(n, head, laws, args):
    e = head(*args)
    if n.number(e):
        return args
    for F, law in n.through.get(head, ()):
        base, k = _split(n, e, law)
        if k == k.kind(1):
            return base
        if k == k.kind(0) and identity in n.laws(F) and n.has_a_value(e):
            return _element(F, n.laws(F)[identity].args[0])
    return args


def _drop_duplicates(n, head, laws, args):
    return [arg for i, arg in enumerate(args) if arg not in args[:i]]


def _absorb(n, head, laws, args):
    z = _element(head, laws[absorbing].args[0])
    if z in args and all(n.has_a_value(arg) for arg in args if arg != z):
        return z
    return args


def _drop_units(n, head, laws, args):
    unit = _element(head, laws[identity].args[0])
    kept = [arg for arg in args if arg != unit]
    if len(kept) < 2:
        return kept[0] if kept else unit
    return kept if _variadic(head) else args


def _cancel(n, head, laws, args):
    (arg,) = args
    return arg.args[0] if arg.head == head else args


_STEPS = [
    ((associative,), _flatten),
    ((), _evaluate),
    ((associative, commutative), _fold),
    ((commutative,), _sort),
    ((repeats,), _merge_repeats),
    ((idempotent,), _drop_duplicates),
    ((absorbing,), _absorb),
    ((identity,), _drop_units),
    ((involution,), _cancel),
    ((), _count),
]

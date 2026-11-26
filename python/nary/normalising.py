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

from . import arithmetic_rules, elementary_rules, logic_rules  # noqa: F401
from . import _numbers
from ._core import Expr
from ._identities import (
    Law, absorbing, associative, commutative, composes, dominant, heads, idempotent, identities,
    identity, involution, maps, repeats, undoes,
)
from .domains import domain_of
from .functions import is_lambda
from .kinds import Many
from .logic import true
from .rewriting import _has_a_value, _substitute

__all__ = ["normalise"]


def normalise(e, known=None):
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    return _Normaliser(known or (lambda condition: False)).normal(e)


def _element(head, value):
    return value if isinstance(value, Expr) else head.kind.output(value)


def _is_head(e):
    return e.is_constant and e.kind.inputs is not None


def _variadic(head):
    inputs = head.kind.inputs
    return bool(inputs) and inputs[-1].family is Many


def _bind(form, e):
    if e.head != form.head or len(e.args) != len(form.args):
        return None
    return dict(zip(form.args, e.args))


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
        self.known, self.done, self.numbers, self.tables, self.domains = known, {}, {}, {}, {}
        self.through, self.merging = {}, {}
        for F in heads():
            for law in self.laws(F).get(repeats, ()):
                self.through.setdefault(law.args[0].head, []).append((F, law))
            for law in self.laws(F).get(maps, ()):
                if law.normal == "merged" and _is_head(law.args[2]):
                    self.merging.setdefault(law.args[3], []).append(law)

    def laws(self, head):
        if head not in self.tables:
            table = {}
            for item in identities(head):
                if isinstance(item, Law):
                    table.setdefault(item.of, []).append(item)
            self.tables[head] = table
        return self.tables[head]

    def unit(self, head):
        units = self.laws(head).get(identity)
        return _element(head, units[0].args[0]) if units else None

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

    def satisfied(self, law, bindings):
        return law.when is None or self.holds(_substitute(law.when, bindings))

    def has_a_value(self, e):
        return _has_a_value(e, self.holds)

    def conditions(self, e):
        if e not in self.domains:
            if e.head is None:
                self.domains[e] = frozenset()
            elif is_lambda(e) or not _is_head(e.head) or domain_of(e) is None:
                self.domains[e] = None
            else:
                parts = [self.conditions(arg) for arg in e.args]
                self.domains[e] = None if None in parts else frozenset(
                    {self.normal(domain_of(e))}.union(*parts)) - {true}
        return self.domains[e]

    def alike(self, before, after):
        before, after = self.conditions(before), self.conditions(after)
        if before is None or after is None:
            return False
        return all(self.known(c) is True for c in before ^ after)

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


def _merge_pairs(args, key, combine, any_order):
    merged, groups, changed = [], {}, False
    for arg in args:
        group = key(arg)
        k = groups.get(group)
        if k is not None:
            combined = combine(merged[k], arg)
            if combined is not None:
                merged[k], changed = combined, True
                continue
        if not any_order:
            groups = {}
        if group is not None:
            groups[group] = len(merged)
        merged.append(arg)
    return merged if changed else None


def _merge_maps(n, head, laws, args):
    for law in n.merging.get(head, ()):
        form, hole, F, G = law.args

        def key(arg):
            bindings = _bind(form, arg)
            return bindings and tuple(v for p, v in bindings.items() if p != hole)

        def combine(a, b):
            first, second = _bind(form, a), _bind(form, b)
            if not (n.satisfied(law, first) or n.satisfied(law, second)):
                return None
            merged = _substitute(form, {**first, hole: F(first[hole], second[hole])})
            return n.normal(merged) if n.alike(head(a, b), merged) else None

        merged = _merge_pairs(args, key, combine, commutative in laws)
        if merged is not None:
            return _Restart(merged)
    return args


def _merge_repeats(n, head, laws, args):
    (law,) = laws[repeats]
    form, count = law.args

    def key(arg):
        return None if n.number(arg) else _split(n, arg, law)[0]

    def combine(a, b):
        (base, k), (other, m) = _split(n, a, law), _split(n, b, law)
        total = n.normal(k + m)
        if base != other or commutative in n.laws(form.head) and not n.number(total):
            return None
        merged = form.head(*(total if p == count else base for p in form.args))
        return n.normal(merged) if n.alike(head(a, b), merged) else None

    merged = _merge_pairs(args, key, combine, commutative in laws)
    return args if merged is None else _Restart(merged)


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


def _count(n, head, laws, args):
    e = head(*args)
    if n.number(e):
        return args
    for F, law in n.through.get(head, ()):
        base, k = _split(n, e, law)
        if k == k.kind(1):
            return base
        if k == k.kind(0) and n.unit(F) is not None and n.has_a_value(e):
            return n.unit(F)
    return args


def _drop_duplicates(n, head, laws, args):
    return [arg for i, arg in enumerate(args) if arg not in args[:i]]


def _absorb(n, head, laws, args):
    z = _element(head, laws[absorbing][0].args[0])
    if z in args and all(n.has_a_value(arg) for arg in args if arg != z):
        return z
    return args


def _dominate(n, head, laws, args):
    z = _element(head, laws[dominant][0].args[0])
    return z if z in args else args


def _drop_units(n, head, laws, args):
    unit = n.unit(head)
    kept = [arg for arg in args if arg != unit]
    if len(kept) < 2:
        return kept[0] if kept else unit
    return kept if _variadic(head) else args


def _cancel(n, head, laws, args):
    (arg,) = args
    return arg.args[0] if arg.head == head else args


def _undo(n, head, laws, args):
    e = head(*args)
    for law in laws[undoes]:
        (inner,) = law.args
        bindings = _bind(inner, args[0])
        if bindings and n.satisfied(law, bindings):
            (value,) = bindings.values()
            if n.alike(e, value):
                return value
    return args


def _compose(n, head, laws, args):
    e = head(*args)
    for law in laws[composes]:
        form, count, F = law.args
        (base,) = [p for p in form.args if p != count]
        outer = _bind(form, e)
        inner = outer and _bind(form, outer[base])
        if inner and n.satisfied(law, outer):
            merged = _substitute(form, {**inner, count: F(inner[count], outer[count])})
            if n.alike(e, merged):
                return n.normal(merged)
    return args


def _map_unit(n, head, laws, args):
    e = head(*args)
    for law in laws[maps]:
        form, hole, F, G = law.args
        bindings = _bind(form, e)
        if _is_head(F) and bindings and bindings[hole] == n.unit(F):
            unit = n.unit(G)
            if unit is not None and n.alike(e, unit):
                return unit
    return args


def _map_split(n, head, laws, args):
    e = head(*args)
    for law in laws[maps]:
        form, hole, F, G = law.args
        bindings = _bind(form, e)
        if law.normal != "split" or not bindings or bindings[hole].head != F:
            continue
        parts = bindings[hole].args
        out = [i for i, part in enumerate(parts) if n.satisfied(law, {**bindings, hole: part})]
        if commutative not in n.laws(F):
            out = [i for k, i in enumerate(out) if i == k]
        if associative not in n.laws(G):
            out = out[:1]
        if not out:
            continue
        pieces = [_substitute(form, {**bindings, hole: parts[i]}) for i in out]
        rest = [part for i, part in enumerate(parts) if i not in out]
        if rest:
            pieces.append(_substitute(form, {**bindings, hole: F(*rest)}))
        result = G(*pieces)
        if n.alike(e, result):
            return n.normal(result)
    return args


def _map_shift(n, head, laws, args):
    shifts = [law for law in laws[maps] if not _is_head(law.args[2])]
    if not shifts:
        return args
    (arg,) = args
    candidates = [(arg, ())]
    for law in shifts:
        form, hole, F, G = law.args
        if _translation(law) is None:
            for x, outside in list(candidates):
                y = n.normal(_substitute(F, {hole: x}))
                if n.normal(_substitute(F, {hole: y})) == x:
                    candidates.append((y, outside + ((law, 1),)))
    for law in shifts:
        if _translation(law) is not None:
            candidates = [_reduce(n, law, x, outside) for x, outside in candidates]
    best, outside = min(candidates, key=lambda c: (_negative(n, c[0]), _key(c[0])))
    if best == arg or None in outside:
        return args
    value = head(best)
    for law, times in outside:
        form, hole, F, G = law.args
        for _ in range(times):
            value = _substitute(G, {hole: value})
    return n.normal(value)


def _translation(law):
    form, hole, F, G = law.args
    if hole not in F.args or not _is_head(F.head):
        return None
    others = [arg for arg in F.args if arg != hole]
    step = others[0] if len(others) == 1 else F.head(*others)
    return step if _numbers.remainder(F.head, step, step) is not None else None


def _reduce(n, law, x, outside):
    form, hole, F, G = law.args
    step = _translation(law)
    terms = list(x.args) if x.head == F.head else [x]
    for i, term in enumerate(terms):
        found = _numbers.remainder(F.head, term, step)
        if found is not None and found[0] != 0:
            k, left = found
            terms[i] = left
            return n.normal(F.head(*terms)), outside + (_times(n, law, k),)
    return x, outside


def _times(n, law, k):
    form, hole, F, G = law.args
    if G == hole:
        return law, 0
    if n.normal(_substitute(G, {hole: G})) == hole:
        return law, k % 2
    return (law, k) if 0 < k <= 4 else None


def _negative(n, e):
    while not n.number(e):
        if not e.args or commutative not in n.laws(e.head):
            return False
        e = e.args[0]
    return _numbers.sign(e) == -1


_STEPS = [
    ((associative,), _flatten),
    ((), _evaluate),
    ((associative, commutative), _fold),
    ((commutative,), _sort),
    ((), _merge_maps),
    ((repeats,), _merge_repeats),
    ((idempotent,), _drop_duplicates),
    ((dominant,), _dominate),
    ((absorbing,), _absorb),
    ((identity,), _drop_units),
    ((involution,), _cancel),
    ((undoes,), _undo),
    ((composes,), _compose),
    ((maps,), _map_unit),
    ((maps,), _map_split),
    ((maps,), _map_shift),
    ((), _count),
]

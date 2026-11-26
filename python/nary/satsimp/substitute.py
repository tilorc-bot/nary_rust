"""Substitution rows: a monomial identity applied inside a sum, kept when the sum gets smaller.

    >>> import nary as nr
    >>> from nary.satsimp.engine import Engine, size
    >>> from nary.satsimp.prove import prover
    >>> from nary.satsimp.rows import trigsimp_tables
    >>> rows = trigsimp_tables().rows["substitutions"]
    >>> measure = lambda e, signless=False: (size(e),)
    >>> handler = substitution_handler(rows, measure, (nr.sin, nr.cos, nr.tan))
    >>> x, y = nr.NumberKind("x"), nr.NumberKind("y")
    >>> handler(y * nr.sin(x) * nr.cos(x) ** -1, Engine({}, prover()))
    Mul(y, tan(x))

Like terms are not collected, so a sum needs a canonical form to get smaller.

    >>> e = nr.sin(x) ** 2 + nr.cos(x) ** 2
    >>> handler(e, Engine({}, prover())) is None
    True
    >>> from nary.satsimp.methods import sympy_round_trip
    >>> handler(e, Engine({}, prover(), sympy_round_trip))
    1

Under strict, a candidate may not have a value where the expression has none.

    >>> e = nr.Mul(nr.Pow(nr.cos(x), -1), nr.Pow(nr.cos(x), 2), nr.sin(x))
    >>> handler(e, Engine({}, prover())) is None, handler(e, Engine({}, prover(), strict=False))
    (True, Mul(Pow(2, -1), sin(Mul(2, x))))
"""

import itertools

from nary import Add, Mul, NumberKind, Pow
from nary.rewriting import _match, _substitute

__all__ = ["substitution_handler"]

MAX_SITES = 64


def _flat(head, e):
    return [a for arg in e.args for a in _flat(head, arg)] if e.head == head else [e]


def _factors(e):
    return _flat(Mul, e)


def _terms(e):
    return _flat(Add, e)


def _base_exponent(f):
    if f.head == Pow and f.args[1].is_literal:
        return f.args[0], f.args[1].value
    return f, 1


def _monomial(e):
    powers = {}
    for f in _factors(e):
        base, k = _base_exponent(f)
        powers[base] = powers.get(base, 0) + k
    return powers


def _power(base, k):
    return base if k == 1 else Pow(base, k)


def _join(head, unit, items):
    flat = [a for item in items for a in _flat(head, item)]
    return flat[0] if len(flat) == 1 else head(*flat) if flat else NumberKind(unit)


def _sites(pattern, powers, heads):
    def extend(k, bindings, used):
        if k == len(pattern):
            yield bindings, used, min(powers[base] // p for base, p in used.items())
            return
        pbase, p = pattern[k]
        for base, e in powers.items():
            if base in used or base.head not in heads or e * p <= 0 or abs(e) < abs(p):
                continue
            for new in _match(pbase, base, bindings):
                yield from extend(k + 1, new, {**used, base: p})

    yield from extend(0, {}, {})


def _replaced(term, parts):
    powers = _monomial(term)
    for pattern, _, j in parts:
        for base, p in pattern.items():
            powers[base] -= p * j
    rest = [_power(base, k) for base, k in powers.items() if k]
    sums = [[_join(Mul, 1, combo) for combo in itertools.product(*[_terms(rhs)] * j)]
            for _, rhs, j in parts]
    return [_join(Mul, 1, rest + list(combo)) for combo in itertools.product(*sums)]


def _candidate(terms, chosen, row):
    parts = {}
    for i, bindings, pattern, j in chosen:
        if any(set(pattern) & set(p) for p, _, _ in parts.get(i, ())):
            continue
        parts.setdefault(i, []).append((pattern, _substitute(row.rule.replacement, bindings), j))
    new = []
    for i, t in enumerate(terms):
        new.extend(_replaced(t, parts[i]) if i in parts else (t,))
    return _join(Add, 0, new)


def substitution_handler(rows, measure, heads):
    table = [(row, [_base_exponent(f) for f in _factors(row.rule.pattern)]) for row in rows]

    def holds(row, bindings, engine):
        condition = row.rule.condition
        if condition is not None and not engine.known(_substitute(condition, bindings)):
            return False
        return not engine.strict or engine._sound(row, bindings)

    def handler(expr, engine):
        terms = _terms(expr)
        powers = [_monomial(t) for t in terms]
        best, best_m = None, measure(expr, signless=True)
        for row, pattern in table:
            sites = []
            for i, pw in enumerate(powers):
                for bindings, used, j in _sites(pattern, pw, heads):
                    if len(sites) < MAX_SITES and holds(row, bindings, engine):
                        sites.append((i, bindings, used, j))
            groups = {}
            for site in sites:
                groups.setdefault(tuple(sorted(site[1].items(), key=repr)), []).append(site)
            choices = [[s] for s in sites] + [g for g in groups.values() if len(g) > 1]
            if len(groups) > 1:
                choices.append(sites)
            for chosen in choices:
                candidate = engine.normal(_candidate(terms, chosen, row))
                if expr.head != Add and candidate.head == Add:
                    continue
                m = measure(candidate, signless=True)
                if m < best_m and (not engine.strict or engine.defined_where(expr, candidate)):
                    best, best_m = candidate, m
        return best

    return handler

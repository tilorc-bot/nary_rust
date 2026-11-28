import cmath
import random
from fractions import Fraction
from itertools import permutations, product

import pytest

from nary import BoolKind
from nary.normalising import normalise


def value(e, at, model):
    if e.is_symbol:
        return at[e]
    if e.is_literal:
        return Fraction(e.value)
    if e.is_constant:
        return model[e]
    return model[e.head](*(value(arg, at, model) for arg in e.args))


def symbols(*es):
    found = set()
    for e in es:
        if e.is_symbol:
            found.add(e)
        elif not e.is_atom:
            found.update(symbols(*e.args))
    return sorted(found, key=repr)


def assignments(es, sample):
    names = symbols(*es)
    if all(name.kind == BoolKind for name in names):
        for values in product([False, True], repeat=len(names)):
            yield dict(zip(names, values))
        return
    rng = random.Random(repr(es))
    for _ in range(8):
        yield {name: sample(name.kind, rng) for name in names}


def same(left, right):
    if isinstance(left, complex) or isinstance(right, complex):
        return cmath.isclose(complex(left), complex(right), rel_tol=1e-9, abs_tol=1e-9)
    return left == right


def unequal_pairs(table, model, sample):
    return [
        (e, other) for e, other, *_ in table
        if not all(
            same(value(e, at, model), value(other, at, model))
            for at in assignments((e, other), sample)
        )
    ]


def shape(e):
    if e.is_atom:
        return repr(e)
    args = [shape(arg) for arg in e.args]
    if getattr(e.head, "is_commutative", False):
        args.sort()
    return f"{shape(e.head)}({', '.join(args)})"


def knowing(*conditions):
    held = {normalise(condition) for condition in conditions}
    return lambda condition: condition in held


def check_same_normal_form(e, expected, known=None):
    got, wanted = normalise(e, known), normalise(expected)
    assert got == wanted, f"{e!r} normalises to {got!r}, not {wanted!r}"


def check_different_normal_form(e, other, known=None):
    got, unwanted = normalise(e, known), normalise(other)
    assert got != unwanted, f"{e!r} normalises to {got!r}, the normal form of {other!r}"


def check_shape_kept(e):
    got = normalise(e)
    assert shape(got) == shape(e), f"{e!r} normalises to {got!r}"


def cases(table):
    return [
        pytest.param(
            *row[:-1], id=repr(row[0]),
            marks=pytest.mark.xfail(strict=True, raises=AssertionError, reason=row[-1])
            if row[-1] else (),
        )
        for row in table
    ]


def pairs(table):
    return [pytest.param(e, other, id=repr(e)) for e, other, *_ in table]


def compositions(args):
    for cuts in product([False, True], repeat=len(args) - 1):
        parts, start = [], 0
        for i, cut in enumerate(cuts, 1):
            if cut:
                parts.append(args[start:i])
                start = i
        yield parts + [args[start:]]


def bracketings(f, args):
    if len(args) == 1:
        yield args[0]
        return
    for parts in compositions(args):
        if len(parts) > 1:
            for choice in product(*(list(bracketings(f, part)) for part in parts)):
                yield f(*choice)
    yield f(*args)


def every_writing(f, args):
    for order in permutations(args):
        yield from bracketings(f, list(order))

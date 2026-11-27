from collections import Counter
from functools import reduce
from math import gcd

import pytest

from nary import BoolKind, FunctionKind, Many, Ne, NumberKind, declare_function, log
from nary._identities import (
    Equal, Law, PatternKind, a, absorbing, associative, b, commutative, declare_identities, f,
    idempotent, identity, s, t,
)
from nary.arithmetic import Add
from nary.commutative import law_step, routine_laws
from nary.logic import false, true
from nary.normalising import normalise

x, y, z = (NumberKind(name) for name in "xyz")
p, q = BoolKind("p"), BoolKind("q")

minus = FunctionKind((PatternKind,), PatternKind)("minus")
op = FunctionKind((PatternKind, PatternKind), PatternKind)("op")

torsion = Law("torsion", Equal(f(s, a, a, a, t), f(s, t)), ("n",))
saturation = Law("saturation", Equal(f(s, a, a, a, t), f(s, a, a, t)), ("k",))
opposites = Law("opposites", Equal(f(s, a, minus(a), t), f(s, t)), (minus,))
folds = Law("folds", Equal(f(s, a, b, t), f(s, op(a, b), t)), (op,))
mystery = Law("mystery", Equal(f(a, a), f(a)))


@law_step(torsion)
def _reduce_counts(head, counts, has_a_value, n):
    return Counter({e: c % n if has_a_value(e) else c for e, c in counts.items()})


@law_step(saturation)
def _cap_counts(head, counts, has_a_value, k):
    return Counter({e: min(c, k) for e, c in counts.items()})


@law_step(opposites)
def _cancel_opposites(head, counts, has_a_value, neg):
    for e in list(counts):
        if not e.is_atom and e.head == neg and has_a_value(e):
            pairs = min(counts[e], counts[e.args[0]])
            counts[e] -= pairs
            counts[e.args[0]] -= pairs
    return counts


@law_step(folds)
def _fold_literals(head, counts, has_a_value, combine):
    literals = Counter({e: c for e, c in counts.items() if e.is_literal})
    if sum(literals.values()) < 2:
        return counts
    folded = reduce(combine, (e.value for e in literals.elements()))
    return counts - literals + Counter([head.kind.output(folded)])


def known_x(condition):
    return condition == Ne(x, 0)


def head(name, kind=NumberKind):
    return declare_function(name, Many(kind), returns=kind, domain=true)


neg = declare_function("neg", NumberKind, returns=NumberKind, domain=true)
Xor = head("Xor", BoolKind)
T3 = head("T3")
Sat = head("Sat")
Cyc = head("Cyc")
Gcd = head("Gcd")
M = head("M")
declare_identities(Xor, [associative, commutative, identity(false), torsion(2)])
declare_identities(T3, [associative, commutative, identity(0), torsion(3)])
declare_identities(Sat, [associative, commutative, saturation(2)])
declare_identities(Cyc, [associative, commutative, opposites(neg), torsion(4), identity(0)])
declare_identities(Gcd, [
    associative, commutative, folds(gcd), identity(0), absorbing(1), idempotent,
])
declare_identities(M, [associative, commutative, mystery])


@pytest.mark.parametrize("e, expected", [
    (Xor(p, q, Xor(p, false)), q),
    (Xor(p, p), false),
    (Xor(q, p, p, p), Xor(p, q)),
    (T3(x, y, T3(x, x)), y),
    (T3(x, x, y, y), T3(x, x, y, y)),
    (T3(x, x, x, x), x),
    (Sat(x, Sat(x, x), y), Sat(x, x, y)),
    (Cyc(x, neg(x), y), y),
    (Cyc(x, neg(x), y, y, y, y), 0),
    (Cyc(neg(x), x, x, z, z, z, z, z), Cyc(x, z)),
    (Gcd(4, x, 6), Gcd(2, x)),
    (Gcd(4, x, 6, 3), 1),
    (Gcd(x, 0, x), x),
    (Gcd(12, 18), 6),
])
def test_new_laws_on_new_heads(e, expected):
    expected = expected if not isinstance(expected, int) else e.head.kind.output(expected)
    assert normalise(e) == expected


def test_erasing_steps_need_a_value():
    assert normalise(T3(log(x), log(x), log(x))) == T3(log(x), log(x), log(x))
    assert normalise(T3(log(x), log(x), log(x)), known_x) == T3.kind.output(0)
    assert normalise(Cyc(log(x), neg(log(x)))) == Cyc(log(x), neg(log(x)))
    assert normalise(Cyc(log(x), neg(log(x))), known_x) == Cyc.kind.output(0)


@pytest.mark.parametrize("e", [
    Xor(p, Xor(q, p), q, p),
    T3(x, T3(x, y), x, y, y, z),
    Sat(y, x, Sat(x, x, y)),
    Cyc(neg(y), x, y, neg(x), z, log(x), neg(log(x))),
    Gcd(Gcd(x, 8), 12, y, x),
    M(y, M(x, y)),
])
def test_normalising_twice_changes_nothing(e):
    assert normalise(normalise(e)) == normalise(e)


def test_the_laws_the_routine_uses():
    assert repr(routine_laws(Cyc)) == "[opposites(neg), torsion(4), identity(0)]"
    assert routine_laws(Gcd)[0].args == [gcd]
    assert repr(routine_laws(Gcd)[1:]) == "[identity(0), absorbing(1), idempotent]"
    assert routine_laws(M) == []


def test_a_law_without_a_step_only_gets_the_structure():
    assert normalise(M(y, M(x, x))) == M(x, x, y)


def test_steps_do_not_reach_heads_without_their_law():
    assert normalise(x + x + x) == Add(x, x, x)
    assert repr(routine_laws(Add)) == "[identity(0)]"


def test_a_law_takes_one_step():
    with pytest.raises(ValueError, match="already has a step"):
        law_step(torsion)(_cap_counts)

import doctest

import nary.domains
import nary.relational
from nary import BoolKind, Eq, Equal, Lambda, NumberKind
from nary.domains import Family, domain
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")


def test_doctests():
    assert doctest.testmod(nary.domains).failed == 0
    assert doctest.testmod(nary.relational).failed == 0


def test_a_family_declares_each_combination_of_kinds_once():
    calls = []
    pair = Family("Pair", lambda k: calls.append(k) or ((k, k), k, true))
    assert pair(NumberKind) is pair(NumberKind) and calls == [NumberKind]
    assert pair(BoolKind)(p, p).head in pair and not (Eq in pair)


def test_equal_for_any_kind():
    assert Equal(x, 0) == Equal(x, NumberKind(0)) and Equal(p, true).kind is BoolKind
    assert Equal(x, y).head is Equal(y, x).head is not Equal(p, p).head
    assert Equal(x, y) != Eq(x, y) and domain(Equal(p, p).head) == true
    f = Lambda(x, x)
    assert Equal(f, f).head.kind.inputs == (f.kind, f.kind)


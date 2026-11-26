import doctest

import nary.generic
from nary import BoolKind, Eq, Equal, Lambda, NumberKind
from nary.domains import domain
from nary.functions import is_lambda
from nary.generic import Generic, kind_variable
from nary.logic import Not, false
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")


def test_doctests():
    assert doctest.testmod(nary.generic).failed == 0


def test_a_generic_function_declares_each_filling_once():
    K = kind_variable("K")
    pair = Generic("Pair", K, K, returns=K, domain=true)
    assert pair(x, x).head is pair(y, 1).head and len(pair.specific) == 1
    assert pair(p, p).head in pair and Eq not in pair and len(pair.specific) == 2


def test_lambda_fills_in_its_kinds():
    f = Lambda((x, p), x)
    assert f.kind.inputs == (NumberKind, BoolKind) and is_lambda(f)
    assert Lambda(p, Lambda(x, p)).kind.output.inputs == (NumberKind,)


def test_equal_for_any_kind():
    assert Equal(x, 0) == Equal(x, NumberKind(0)) and Equal(p, true).kind is BoolKind
    assert Equal(x, y).head is Equal(y, x).head is not Equal(p, p).head
    assert Equal(true, Not(false)).kind is BoolKind and Equal(x / x, 1).lhs == x / x
    assert Equal(x, y) != Eq(x, y) and domain(Equal(p, p).head) == true
    f = Lambda(x, x)
    assert Equal(f, f).head.kind.inputs == (f.kind, f.kind)


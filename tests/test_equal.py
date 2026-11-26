import doctest

import pytest

import nary.generic
from nary import AnyEq, AnyNe, BoolKind, Eq, FunctionKind, Lambda, Ne, NumberKind
from nary.domains import domain
from nary.functions import is_lambda
from nary.generic import Generic, kind_variable
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")


def test_doctests():
    assert doctest.testmod(nary.generic).failed == 0


def test_a_generic_function_declares_each_filling_once():
    K = kind_variable("K")
    pair = Generic("Pair", K, K, returns=K, domain=true)
    assert pair(x, x).head is pair(y, 1).head is pair[NumberKind]
    assert pair(p, p).head in pair and Eq not in pair and len(pair.specific) == 2
    with pytest.raises(TypeError, match="K is NumberKind and BoolKind"):
        pair(x, p)
    with pytest.raises(TypeError, match="do not give"):
        pair(1, 1)


def test_lambda_fills_in_its_kinds():
    f = Lambda((x, p), x)
    assert f.kind.inputs == (NumberKind, BoolKind) and is_lambda(f)
    assert Lambda(p, Lambda(x, p)).kind.output.inputs == (NumberKind,)


def test_eq_and_ne_are_the_number_instances_of_any_kind_versions():
    assert AnyEq(x, 0).head is Eq is AnyEq[NumberKind] and AnyNe(x, y).head is Ne
    assert Eq.kind is FunctionKind((NumberKind, NumberKind), BoolKind) and Eq(x, y).lhs == x
    assert domain(Eq) == true and AnyEq(p, true).kind is BoolKind
    f = Lambda(x, x)
    assert AnyEq(f, f).head.kind.inputs == (f.kind, f.kind) and AnyEq(f, f).head in AnyEq

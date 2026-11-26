import doctest

import nary.generic
from nary import AnyEq, AnyNe, BoolKind, Eq, FunctionKind, Lambda, Ne, NumberKind, declare_kind
from nary.domains import domain
from nary.functions import is_lambda
from nary.domains import declare_function
from nary.generic import concretize, generic_of
from nary.relational import K
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")


def test_doctests():
    assert doctest.testmod(nary.generic).failed == 0


def test_concretize_substitutes_kinds_once_per_filling():
    K, L = declare_kind("K"), declare_kind("L")
    pick = declare_function("Pick", K, FunctionKind((K,), L, rest=L), returns=L, domain=true)
    both = concretize(pick, {K: NumberKind, L: BoolKind})
    assert both is concretize(pick, {L: BoolKind, K: NumberKind}) and generic_of(both) is pick
    assert both.kind.inputs[1] == FunctionKind((NumberKind,), BoolKind, rest=BoolKind)
    assert concretize(pick, {K: BoolKind}).kind.output is L and generic_of(Eq) is AnyEq


def test_lambda_fills_in_its_kinds():
    f = Lambda((x, p), x)
    assert f.kind.inputs == (NumberKind, BoolKind) and is_lambda(f)
    assert Lambda(p, Lambda(x, p)).kind.output.inputs == (NumberKind,)


def test_eq_and_ne_are_the_number_instances_of_any_kind_versions():
    assert Eq is concretize(AnyEq, {K: NumberKind}) and Ne is concretize(AnyNe, {K: NumberKind})
    assert Eq.kind is FunctionKind((NumberKind, NumberKind), BoolKind) and Eq(x, y).lhs == x
    assert domain(Eq) == true and concretize(AnyEq, {K: BoolKind})(p, true).kind is BoolKind
    f = Lambda(x, x)
    assert concretize(AnyEq, {K: f.kind})(f, f).lhs == f

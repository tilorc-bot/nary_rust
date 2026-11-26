from functools import cache

import pytest

from nary import BoolKind, FunctionKind, Lambda, NumberKind, Symbol, declare_kind_family
from nary.domains import declare_function
from nary.generic import apply_generic, concretize, generic_of, placeholder
from nary.logic import true
from nary.matrices import Matrix, MatrixKind

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")
K, B = placeholder("K"), placeholder("B")
TupleKind = declare_kind_family("TupleKind")
SetKind = declare_kind_family("SetKind", params=1)
A, C = SetKind(NumberKind)("A"), SetKind(NumberKind)("C")


def kinds(n):
    return tuple(placeholder(f"K{i}") for i in range(1, n + 1))


@cache
def tuple_generic(n):
    return declare_function("Tuple", *kinds(n), returns=TupleKind(*kinds(n)), domain=true)


def Tuple(*items):
    return apply_generic(tuple_generic(len(items)), *items)


@cache
def for_all_generic(n):
    f = FunctionKind(kinds(n), BoolKind)
    return declare_function("ForAll", f, returns=BoolKind, domain=true)


def ForAll(f):
    return apply_generic(for_all_generic(len(f.kind.inputs)), f)


@cache
def integral_generic(n):
    numbers = FunctionKind((NumberKind,) * n, NumberKind)
    return declare_function("Integral", numbers, returns=NumberKind, domain=true)


def Integral(f):
    return apply_generic(integral_generic(len(f.kind.inputs)), f)


@cache
def let_generic(n):
    variables = (Symbol(kind) for kind in kinds(n))
    return declare_function("Let", *variables, *kinds(n), B, returns=B, domain=true)


def Let(pairs, body):
    variables, values = zip(*pairs)
    return apply_generic(let_generic(len(pairs)), *variables, *values, body)


@cache
def set_builder_generic(n):
    sets = (SetKind(kind) for kind in kinds(n))
    f = FunctionKind(kinds(n), B)
    return declare_function("SetBuilder", f, *sets, returns=SetKind(B), domain=true)


def SetBuilder(f, *sets):
    return apply_generic(set_builder_generic(len(sets)), f, *sets)


Contains = declare_function("Contains", SetKind(K), K, returns=BoolKind, domain=true)
FiniteSet = declare_function("FiniteSet", K, rest=K, returns=SetKind(K), domain=true)
Union = declare_function("Union", SetKind(K), rest=SetKind(K), returns=SetKind(K), domain=true)
EmptySet = declare_function("EmptySet", returns=SetKind(K), domain=true)
Transpose = declare_function("Transpose", MatrixKind(K), returns=MatrixKind(K), domain=true)


def test_tuple():
    t = Tuple(x, p, Lambda(x, x))
    assert t.kind is TupleKind(NumberKind, BoolKind, FunctionKind((NumberKind,), NumberKind))
    assert Tuple(y, p).head is Tuple(x, p).head is not Tuple(p, x).head
    assert generic_of(t.head) is tuple_generic(3)


def test_quantifier():
    assert ForAll(Lambda((x, p), p)).kind is BoolKind
    assert ForAll(Lambda(x, p)).head is not ForAll(Lambda(p, p)).head
    with pytest.raises(TypeError):
        ForAll(Lambda(x, x))


def test_integral_varies_in_shape_only():
    assert Integral(Lambda((x, y), x * y)).head is integral_generic(2)
    with pytest.raises(TypeError):
        Integral(Lambda(p, x))


def test_let():
    e = Let([(x, 1), (p, true)], x)
    assert e.kind is NumberKind and e.args == (x, p, NumberKind(1), true, x)
    with pytest.raises(TypeError):
        Let([(x + 1, 1)], x)


def test_set_builder():
    e = SetBuilder(Lambda((x, y), p), A, C)
    assert e.kind is SetKind(BoolKind) and generic_of(e.head) is set_builder_generic(2)


def test_fixed_shapes_over_a_kind_family():
    assert apply_generic(Contains, A, x).kind is BoolKind
    assert apply_generic(FiniteSet, x, y, 1).kind is SetKind(NumberKind)
    assert apply_generic(Union, A, C, A).head is apply_generic(Union, C).head
    assert apply_generic(Transpose, Matrix("M")).kind is MatrixKind(NumberKind)
    with pytest.raises(TypeError, match="K is NumberKind and BoolKind"):
        apply_generic(FiniteSet, x, p)
    with pytest.raises(TypeError):
        apply_generic(Contains, A, p)


def test_a_kind_only_in_the_result_is_filled_explicitly():
    assert concretize(EmptySet, {K: NumberKind})().kind is SetKind(NumberKind)


@pytest.mark.xfail(strict=True, reason="a literal has no kind until a position gives it one")
def test_literals_alone_fill_nothing():
    assert Tuple(1, 2).kind is TupleKind(NumberKind, NumberKind)


@pytest.mark.xfail(strict=True, reason="one generic for all lengths needs a run-of-kinds placeholder")
def test_one_generic_for_every_length():
    assert generic_of(Tuple(x).head) is generic_of(Tuple(x, y).head)

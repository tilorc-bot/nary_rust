import pytest

from nary import (
    BoolKind,
    Bound,
    Eq,
    FunctionKind,
    KindVariable,
    Lambda,
    Many,
    ManyMixed,
    NumberKind,
    concretize,
    declare_kind_family,
    generic_of,
)
from nary import functions, relational, sin
from nary.domains import declare_function
from nary.logic import true
from nary.matrices import Matrix, MatrixKind

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")
K, B = KindVariable("K"), KindVariable("B")
TupleKind = declare_kind_family("TupleKind")
SetKind = declare_kind_family("SetKind", params=1)
A, C = SetKind(NumberKind)("A"), SetKind(NumberKind)("C")
NumToNum = FunctionKind((NumberKind,), NumberKind)

Tuple = declare_function("Tuple", ManyMixed(K("elements")), returns=TupleKind(ManyMixed(K)), domain=true)
ForAll = declare_function("ForAll", FunctionKind((ManyMixed(K),), BoolKind)("predicate"), returns=BoolKind, domain=true)
Let = declare_function("Let", FunctionKind((ManyMixed(K),), B)("function"), ManyMixed(K("values")), returns=B, domain=true)
Contains = declare_function("Contains", SetKind(K)("set"), K("element"), returns=BoolKind, domain=true)
FiniteSet = declare_function("FiniteSet", Many(K("elements")), returns=SetKind(K), domain=true)
Union = declare_function("Union", Many(SetKind(K)("sets")), returns=SetKind(K), domain=true)
EmptySet = declare_function("EmptySet", returns=SetKind(K), domain=true)
Transpose = declare_function("Transpose", MatrixKind(K)("arg"), returns=MatrixKind(K), domain=true)


def test_tuple():
    t = Tuple(x, p, Lambda(x, x))
    assert t.kind is TupleKind(NumberKind, BoolKind, NumToNum)
    assert t.head is Tuple and t.elements == (x, p, Lambda(x, x))
    assert repr(Tuple().kind) == "TupleKind()" and Tuple(p, x).kind is TupleKind(BoolKind, NumberKind)
    assert repr(Tuple.kind) == "FunctionKind((ManyMixed(K),), TupleKind(ManyMixed(K)))"
    assert repr(Tuple.params) == "(ManyMixed(elements),)"


def test_one_generic_for_every_length():
    assert Tuple(x).head is Tuple(x, y).head is Tuple
    assert Lambda(x, x).head is Lambda((x, p), x).head


def test_quantifier():
    assert ForAll(Lambda((x, p), p)).kind is BoolKind
    assert ForAll(Lambda(x, p)).head is ForAll(Lambda(p, p)).head is ForAll
    assert ForAll(concretize(Eq, {relational.K: NumberKind})).kind is BoolKind
    with pytest.raises(TypeError, match=r"^ForAll expects FunctionKind\(\(ManyMixed\(K\),\), BoolKind\), got "):
        ForAll(Lambda(x, x))


def test_let():
    e = Let(Lambda((x, p), x), 1, true)
    assert e.kind is NumberKind and e.args == (Lambda((x, p), x), NumberKind(1), true)
    assert e.values == (NumberKind(1), true)
    with pytest.raises(TypeError, match=r"^Let: K is \(NumberKind, BoolKind\) and \(NumberKind, NumberKind\)$"):
        Let(Lambda((x, p), x), 1, y)
    with pytest.raises(TypeError, match=r"^Let: K is \(NumberKind,\), so ManyMixed\(K\) takes 1 argument, got 2$"):
        Let(Lambda(x, x), 1, 2)


def test_fixed_shapes_over_a_kind_family():
    assert Contains(A, x).kind is BoolKind
    assert FiniteSet(x, y, 1).kind is SetKind(NumberKind) and FiniteSet(x, y, 1).elements == (x, y, NumberKind(1))
    assert Union(A, C, A).head is Union(C).head is Union
    assert Transpose(Matrix("M")).kind is MatrixKind(NumberKind)
    with pytest.raises(TypeError, match=r"^FiniteSet: K is NumberKind and BoolKind$"):
        FiniteSet(x, p)
    with pytest.raises(TypeError, match=r"^Contains: K is NumberKind and BoolKind$"):
        Contains(A, p)


def test_a_kind_only_in_the_result_is_filled_explicitly():
    assert concretize(EmptySet, {K: NumberKind})().kind is SetKind(NumberKind)
    assert concretize(FiniteSet, {K: NumberKind})().kind is SetKind(NumberKind)
    with pytest.raises(TypeError, match=r"^FiniteSet: no argument fills K, since a literal has no kind of its own; use concretize\(FiniteSet, \{K: \.\.\.\}\)$"):
        FiniteSet(1, 2)
    with pytest.raises(TypeError, match=r"^EmptySet: no argument fills K"):
        EmptySet()


def test_concretize_gives_the_same_function_at_given_kinds():
    eq = concretize(Eq, {relational.K: NumberKind})
    assert eq(x, 0) == Eq(x, 0) and eq(x, 0).head is Eq and generic_of(eq) is Eq
    assert eq is concretize(Eq, {relational.K: NumberKind}) and eq.kind is FunctionKind((NumberKind, NumberKind), BoolKind)
    pair = concretize(Tuple, {K: (NumberKind, BoolKind)})
    assert pair(1, true) == Tuple(NumberKind(1), true) and pair.kind is FunctionKind((NumberKind, BoolKind), TupleKind(NumberKind, BoolKind))
    lam = concretize(Lambda(x, x).head, {functions.K: (NumberKind,), functions.B: BoolKind})
    assert lam(y, p) == Lambda(y, p)
    with pytest.raises(TypeError, match=r"^Lambda expects a NumberKind symbol, got 1$"):
        lam(1, p)


def test_concretize_errors():
    with pytest.raises(TypeError, match=r"^concretize: Tuple has ManyMixed\(K\), so K takes a tuple with a kind for each argument, got NumberKind$"):
        concretize(Tuple, {K: NumberKind})
    with pytest.raises(TypeError, match=r"^concretize: K stands for one kind in Eq, got \(NumberKind,\); a tuple of kinds fills only a variable used as ManyMixed\(K\)$"):
        concretize(Eq, {relational.K: (NumberKind,)})
    with pytest.raises(ValueError, match=r"^concretize: B is not a kind variable of Tuple$"):
        concretize(Tuple, {B: (NumberKind,)})
    with pytest.raises(ValueError, match=r"^concretize: Let needs a kind for B$"):
        concretize(Let, {K: (NumberKind,)})
    with pytest.raises(ValueError, match=r"^concretize: K must be filled with kinds without kind variables, got \(B,\)$"):
        concretize(Tuple, {K: (B,)})
    with pytest.raises(TypeError, match=r"^concretize expects a declared function with kind variables, got sin$"):
        concretize(sin, {})


def test_a_kind_variable_is_either_alike_or_mixed_in_one_declaration():
    with pytest.raises(TypeError, match=r"^Bad: K is used both as ManyMixed\(K\) and on its own; ManyMixed\(K\) gives each argument its own K, so use a second kind variable for the other$"):
        declare_function("Bad", ManyMixed(K("elements")), returns=K, domain=true)
    with pytest.raises(TypeError, match=r"^ManyMixed takes a kind variable or a symbol of one, got NumberKind; for any number of arguments of kind NumberKind use Many$"):
        ManyMixed(NumberKind)
    with pytest.raises(TypeError, match=r"^ManyMixed takes a kind variable or a symbol of one, got s; for any number of arguments of kind SetKind\(K\) use Many$"):
        ManyMixed(SetKind(K)("s"))
    with pytest.raises(TypeError, match=r"^SetKind takes 1 parameter, so a parameter cannot be ManyMixed\(K\)$"):
        SetKind(ManyMixed(K))
    with pytest.raises(TypeError, match=r"^TupleKind: a parameter of a kind family cannot be Many\(K\)$"):
        TupleKind(Many(K))
    with pytest.raises(TypeError, match=r"^Tuple cannot tell the kind of 1: a literal takes the kind of its position, and in ManyMixed\(K\) each position has its own kind$"):
        Tuple(x, 1)


@pytest.mark.xfail(strict=True, reason="a literal has no kind of its own and ManyMixed gives each position its own K; concretize(Tuple, {K: (NumberKind, NumberKind)})(1, 2) says it")
def test_literals_alone_fill_nothing():
    assert Tuple(1, 2).kind is TupleKind(NumberKind, NumberKind)


@pytest.mark.xfail(strict=True, reason="no way to say n arguments that are all NumberKind: Many(NumberKind) is a function of any number of them, ManyMixed(K) lets the kinds differ")
def test_integral_over_a_function_of_n_numbers():
    Integral = declare_function("Integral", FunctionKind((Many(NumberKind),), NumberKind)("integrand"), returns=NumberKind, domain=true)
    assert Integral(Lambda((x, y), x * y)).kind is NumberKind


@pytest.mark.xfail(strict=True, reason="ManyMixed takes only a kind variable, so 'each argument is a set of its own K' (ManyMixed(SetKind(K)(...))) cannot be said yet")
def test_set_builder():
    SetBuilder = declare_function("SetBuilder", FunctionKind((ManyMixed(K),), B)("function"), ManyMixed(SetKind(K)("sets")), returns=SetKind(B), domain=true)
    assert SetBuilder(Lambda((x, y), p), A, C).kind is SetKind(BoolKind)

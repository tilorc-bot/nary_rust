"""The kinds of the package, and functions between them.

NumberKind and BoolKind are declared with kind(...). SetKind and MatrixKind
are kind families, and the package has functions for SetKind(NumberKind) and
MatrixKind(NumberKind).
"""

import re

import nary as nr
import pytest
from nary import BoolKind, Expr, Kind, KindFamily, MatrixKind, NumberKind, SetKind, function

NumberSet = SetKind(NumberKind)
NumberMatrix = MatrixKind(NumberKind)
KINDS = (NumberKind, BoolKind, NumberSet, NumberMatrix)


def test_bool_was_renamed():
    assert not hasattr(nr, "Bool")
    assert BoolKind.name == "BoolKind"


def test_sets_and_matrices_are_kind_families():
    for family, name in ((SetKind, "SetKind"), (MatrixKind, "MatrixKind")):
        assert type(family) is KindFamily
        assert (family.name, family.params) == (name, 1)
    assert NumberSet is SetKind(NumberKind)
    assert NumberSet.name == "SetKind(NumberKind)"
    assert (NumberSet.family, NumberSet.params) == (SetKind, (NumberKind,))
    assert NumberMatrix.name == "MatrixKind(NumberKind)"
    assert (NumberMatrix.family, NumberMatrix.params) == (MatrixKind, (NumberKind,))
    assert NumberKind.family is None and BoolKind.params == ()


def test_the_functions_are_for_sets_and_matrices_of_numbers():
    assert nr.Union.returns is NumberSet
    assert nr.Contains.params == (NumberKind, NumberSet)
    assert nr.MatMul.rest == (NumberMatrix,)
    assert nr.Determinant.params == (NumberMatrix,)
    with pytest.raises(TypeError, match=r"^Union expects SetKind\(NumberKind\), got SetKind\(BoolKind\): P$"):
        nr.Union(SetKind(BoolKind)("P"))
    with pytest.raises(TypeError, match=r"^Transpose expects MatrixKind\(NumberKind\), got MatrixKind\(BoolKind\): P$"):
        nr.Transpose(MatrixKind(BoolKind)("P"))
    # Other matrix kinds have no operators.
    with pytest.raises(TypeError, match="unsupported operand"):
        MatrixKind(BoolKind)("P") * MatrixKind(BoolKind)("Q")


def test_a_family_is_not_a_kind():
    with pytest.raises(TypeError, match=r"^MatrixKind takes 1 parameter, got 0$"):
        MatrixKind()
    with pytest.raises(TypeError, match=r"^a signature is made of kinds and Symbol\(kind\), got <kind family SetKind>$"):
        function("f", SetKind, returns=NumberKind)
    with pytest.raises(TypeError):
        MatrixKind("A")


@pytest.mark.parametrize("kind", KINDS)
def test_a_kind_is_an_object(kind):
    assert type(kind) is Kind
    assert repr(kind) == kind.name
    assert [k for k in KINDS if k is kind] == [kind]


@pytest.mark.parametrize("kind", KINDS)
def test_calling_a_kind_makes_a_symbol_of_that_kind(kind):
    s = kind("s")
    assert type(s) is Expr
    assert s.kind is kind
    assert s.is_symbol
    assert s.head == "s"
    assert s.args == ()
    assert repr(s) == "s"


@pytest.mark.parametrize("kind", KINDS)
def test_a_kind_takes_only_a_name(kind):
    with pytest.raises(TypeError):
        kind("f", kind("a"))
    with pytest.raises(TypeError):
        kind(1)


def test_there_is_one_class_of_expression():
    x = NumberKind("x")
    assert type(x + 1) is type(x < 1) is type(nr.Interval(0, 1)) is Expr
    with pytest.raises(TypeError):
        isinstance(x, NumberSet)
    with pytest.raises(TypeError):
        isinstance(x, NumberKind)
    with pytest.raises(TypeError):
        Expr("x")
    with pytest.raises(TypeError):
        class Sub(Expr):
            pass
    with pytest.raises(AttributeError):
        x.kind = BoolKind


@pytest.mark.parametrize("returns", KINDS)
def test_result_is_of_the_declared_kind(returns):
    f = function("f", NumberKind, returns=returns)
    assert f(NumberKind("x")).kind is returns
    assert f.returns is returns


@pytest.mark.parametrize("accepts", KINDS)
def test_every_kind_can_be_an_argument(accepts):
    f = function("f", accepts, returns=NumberKind)
    assert repr(f(accepts("a"))) == "f(a)"
    for other in KINDS:
        if other is not accepts:
            with pytest.raises(TypeError, match="^" + re.escape(f"f expects {accepts.name}, got {other.name}: a") + "$"):
                f(other("a"))


NOT_KINDS = ((int, "<class 'int'>"), (Expr, "<class 'nary.Expr'>"), (Kind, "<class 'nary.Kind'>"), ("NumberKind", "'NumberKind'"), (None, "None"))


@pytest.mark.parametrize("not_a_kind, text", NOT_KINDS)
def test_returns_must_be_a_kind(not_a_kind, text):
    with pytest.raises(ValueError, match=f"^returns must be a kind, got {text}$"):
        function("f", NumberKind, returns=not_a_kind)


@pytest.mark.parametrize("not_a_kind, text", NOT_KINDS)
def test_signature_must_be_made_of_kinds(not_a_kind, text):
    with pytest.raises(TypeError, match=rf"^a signature is made of kinds and Symbol\(kind\), got {text}$"):
        function("f", not_a_kind, returns=NumberKind)
    with pytest.raises(TypeError, match="^a signature is made of kinds"):
        function("f", rest=(NumberKind, not_a_kind), returns=NumberKind)
    with pytest.raises(TypeError, match="^a signature is made of kinds"):
        function("f", rest=not_a_kind, returns=NumberKind) if not_a_kind is not None else function("f", None, returns=NumberKind)
    with pytest.raises(TypeError, match=f"^expected a kind, got {text}$"):
        nr.set_operator(not_a_kind, "+", nr.Add)
    with pytest.raises(TypeError, match=f"^expected a kind, got {text}$"):
        nr.set_integer_kind(not_a_kind)


def test_an_expression_is_not_a_kind():
    x = NumberKind("x")
    with pytest.raises(TypeError, match="^a signature is made of kinds and Symbol\\(kind\\), got x$"):
        function("f", x, returns=NumberKind)
    with pytest.raises(ValueError, match="^returns must be a kind, got x$"):
        function("f", returns=x)


def test_sets():
    x = NumberKind("x")
    s = nr.Interval(0, 1)
    assert s.kind is NumberSet
    assert (s.start, s.end) == (nr.Integer(0), nr.Integer(1))
    u = nr.Union(s, nr.FiniteSet(2, 3, x), NumberSet("S"))
    assert u.kind is NumberSet
    assert repr(u) == "Union(Interval(0, 1), FiniteSet(2, 3, x), S)"
    assert nr.Intersection(s, s).kind is NumberSet
    c = nr.Contains(x, u)
    assert c.kind is BoolKind
    assert c.element == x and c.set == u


def test_set_errors():
    x = NumberKind("x")
    s = nr.Interval(0, 1)
    with pytest.raises(TypeError, match=r"^Contains expects SetKind\(NumberKind\), got NumberKind: x$"):
        nr.Contains(x, x)
    with pytest.raises(TypeError, match=r"^Contains expects NumberKind, got SetKind\(NumberKind\): Interval\(0, 1\)$"):
        nr.Contains(s, s)
    with pytest.raises(TypeError, match=r"^Union expects SetKind\(NumberKind\), got int: 1$"):
        nr.Union(s, 1)
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got SetKind\(NumberKind\)"):
        nr.sin(s)


def test_matrices():
    a, b = NumberMatrix("A"), NumberMatrix("B")
    m = nr.MatMul(a, nr.Transpose(b), nr.Inverse(a))
    assert m.kind is NumberMatrix
    assert repr(m) == "MatMul(A, Transpose(B), Inverse(A))"
    assert nr.MatAdd(a, b, m).kind is NumberMatrix
    assert nr.Determinant(m).kind is NumberKind
    assert repr(nr.sin(nr.Determinant(a))) == "sin(Determinant(A))"


def test_matrix_errors():
    a, x = NumberMatrix("A"), NumberKind("x")
    with pytest.raises(TypeError, match=r"^MatMul expects MatrixKind\(NumberKind\), got NumberKind: x$"):
        nr.MatMul(a, x)
    with pytest.raises(TypeError, match=r"^Mul expects NumberKind, got MatrixKind\(NumberKind\): A$"):
        nr.Mul(x, a)
    with pytest.raises(TypeError, match=r"^MatAdd expects MatrixKind\(NumberKind\), got int: 2$"):
        nr.MatAdd(a, 2)
    with pytest.raises(TypeError, match=r"^Transpose takes 1 argument, got 2$"):
        nr.Transpose(a, a)


def test_logic():
    p, q = BoolKind("p"), BoolKind("q")
    x = NumberKind("x")
    e = nr.And(p, nr.Or(q, x < 1), nr.Not(p))
    assert e.kind is BoolKind
    assert repr(e) == "And(p, Or(q, Lt(x, 1)), Not(p))"
    with pytest.raises(TypeError, match=r"^And expects BoolKind, got NumberKind: x$"):
        nr.And(p, x)
    with pytest.raises(TypeError, match=r"^Not expects BoolKind, got bool: True$"):
        nr.Not(True)


def test_equality_respects_kind():
    assert NumberKind("p") != BoolKind("p")
    assert NumberSet("p") != NumberMatrix("p")
    assert NumberMatrix("p") != MatrixKind(BoolKind)("p")
    f = function("f", NumberKind, returns=NumberKind)
    g = function("f", NumberKind, returns=BoolKind)
    x = NumberKind("x")
    assert f(x) == f(x)
    assert f(x) != g(x)
    assert len({NumberKind("p"), BoolKind("p"), NumberKind("p")}) == 2
    assert hash(NumberKind("p")) != hash(BoolKind("p"))
    assert hash(f(x)) != hash(g(x))

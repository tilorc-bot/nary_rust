"""Kind families: kinds with other kinds as parameters, declared in Python."""

import threading

import nary as nr
import pytest
from nary import (
    BoolKind, Expr, Kind, KindFamily, NumberKind, function, kind, kind_family, set_operator,
)

# Families that nary does not have, declared here. Nothing in Rust knows
# about them.
TupleKind = kind_family("TupleKind")              # one or more parameters
MatrixKind = kind_family("MatrixKind", params=1)  # exactly one parameter

Pair = TupleKind(NumberKind, BoolKind)
Piece = function("Piece", NumberKind, BoolKind, returns=Pair, names=("value", "condition"))

x, y = NumberKind("x"), NumberKind("y")


def test_a_family_is_an_object_declared_with_kind_family():
    assert type(TupleKind) is KindFamily
    assert (TupleKind.name, TupleKind.params) == ("TupleKind", None)
    assert (MatrixKind.name, MatrixKind.params) == ("MatrixKind", 1)
    assert repr(TupleKind) == "<kind family TupleKind>"
    assert repr(MatrixKind) == "<kind family MatrixKind>"


def test_instantiating_a_family_gives_a_kind():
    assert type(Pair) is Kind
    assert type(MatrixKind(NumberKind)) is Kind
    assert Pair.name == repr(Pair) == "TupleKind(NumberKind, BoolKind)"
    assert repr(MatrixKind(NumberKind)) == "MatrixKind(NumberKind)"
    assert repr(TupleKind(NumberKind)) == "TupleKind(NumberKind)"
    assert repr(TupleKind(NumberKind, NumberKind, BoolKind)) == "TupleKind(NumberKind, NumberKind, BoolKind)"


def test_the_same_parameters_give_the_same_kind():
    assert TupleKind(NumberKind, BoolKind) is Pair
    assert MatrixKind(NumberKind) is MatrixKind(NumberKind)
    assert MatrixKind(Pair) is MatrixKind(TupleKind(NumberKind, BoolKind))


def test_different_parameters_give_different_kinds():
    kinds = [
        Pair,
        TupleKind(BoolKind, NumberKind),           # another order
        TupleKind(NumberKind),                     # fewer
        TupleKind(NumberKind, BoolKind, BoolKind), # more
        TupleKind(NumberKind, NumberKind),
        MatrixKind(NumberKind),
        MatrixKind(BoolKind),
    ]
    assert len({id(k) for k in kinds}) == len(kinds)


def test_different_families_give_different_kinds():
    # Even with the same name and the same parameters.
    other = kind_family("TupleKind")
    assert other is not TupleKind
    assert other(NumberKind, BoolKind) is not Pair
    assert other(NumberKind, BoolKind).name == Pair.name
    assert TupleKind(NumberKind) is not MatrixKind(NumberKind)


def test_parameters_can_be_parametrised_kinds():
    nested = TupleKind(MatrixKind(NumberKind), Pair)
    assert nested is TupleKind(MatrixKind(NumberKind), TupleKind(NumberKind, BoolKind))
    assert repr(nested) == "TupleKind(MatrixKind(NumberKind), TupleKind(NumberKind, BoolKind))"
    assert nested.params == (MatrixKind(NumberKind), Pair)
    assert nested.params[1].params == (NumberKind, BoolKind)
    deep = MatrixKind(MatrixKind(MatrixKind(NumberKind)))
    assert deep is MatrixKind(MatrixKind(MatrixKind(NumberKind)))
    assert repr(deep) == "MatrixKind(MatrixKind(MatrixKind(NumberKind)))"


def test_parameters_can_be_plain_kinds_declared_anywhere():
    local = kind("Local")
    assert TupleKind(local, local) is TupleKind(local, local)
    assert TupleKind(local) is not TupleKind(kind("Local"))


def test_a_kind_shows_its_family_and_parameters():
    assert Pair.family is TupleKind
    assert Pair.params == (NumberKind, BoolKind)
    assert MatrixKind(BoolKind).family is MatrixKind
    assert MatrixKind(BoolKind).params == (BoolKind,)
    # A kind declared with kind(name) has neither.
    assert NumberKind.family is None
    assert NumberKind.params == ()
    assert kind("Plain").family is None


def test_calling_an_instantiated_kind_makes_a_leaf():
    A = MatrixKind(NumberKind)("A")
    assert type(A) is Expr
    assert A.kind is MatrixKind(NumberKind)
    assert (A.head, A.args, repr(A)) == ("A", (), "A")
    with pytest.raises(TypeError, match=r"^MatrixKind\(NumberKind\) takes 1 argument, the name of a leaf, got 2; "):
        MatrixKind(NumberKind)("MatMul", A)


def test_an_instantiated_kind_in_signatures():
    p = Piece(x, x < y)
    assert p.kind is Pair
    assert repr(p) == "Piece(x, Lt(x, y))"
    assert (p.value, p.condition) == (x, x < y)
    Matrix = MatrixKind(NumberKind)
    MatAdd = function("MatAdd", rest=Matrix, returns=Matrix)
    Trace = function("Trace", Matrix, returns=NumberKind)
    First = function("First", Pair, returns=NumberKind)
    A, B = Matrix("A"), Matrix("B")
    assert MatAdd(A, B).kind is Matrix
    assert Trace(MatAdd(A, B)).kind is NumberKind
    assert repr(First(p) + x) == "Add(First(Piece(x, Lt(x, y))), x)"
    # A kind made again from the same parameters is accepted.
    assert MatrixKind(NumberKind)("C").kind is Matrix
    assert Trace(MatrixKind(NumberKind)("C")).kind is NumberKind


def test_a_function_shows_what_was_declared():
    Matrix = MatrixKind(NumberKind)
    MatAdd = function("MatAdd", Matrix, rest=Matrix, returns=Matrix)
    assert MatAdd.name == "MatAdd"
    assert len(MatAdd.params) == 1 and MatAdd.params[0] is Matrix
    assert MatAdd.rest == (Matrix,) and MatAdd.returns is Matrix
    assert MatAdd.names == ()
    assert Piece.params == (NumberKind, BoolKind) and Piece.rest == ()
    assert Piece.returns is Pair and Piece.names == ("value", "condition")
    assert nr.Add.params == () and nr.Add.rest == (NumberKind,)
    with pytest.raises(AttributeError):
        Piece.returns = BoolKind


def test_an_instantiated_kind_is_checked():
    Matrix = MatrixKind(NumberKind)
    Trace = function("Trace", Matrix, returns=NumberKind)
    with pytest.raises(TypeError, match=r"^Trace expects MatrixKind\(NumberKind\), got MatrixKind\(BoolKind\): P$"):
        Trace(MatrixKind(BoolKind)("P"))
    with pytest.raises(TypeError, match=r"^Trace expects MatrixKind\(NumberKind\), got NumberKind: x$"):
        Trace(x)
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got TupleKind\(NumberKind, BoolKind\): Piece\(x, Lt\(x, y\)\)$"):
        nr.sin(Piece(x, x < y))
    with pytest.raises(TypeError, match=r"^Piece expects BoolKind, got NumberKind: y$"):
        Piece(x, y)


def test_the_result_kind_is_the_declared_one():
    # Nothing is inferred from the arguments: a function declared to return
    # TupleKind(NumberKind, BoolKind) returns that, whatever it is given.
    Wrap = function("Wrap", rest=MatrixKind(NumberKind), returns=Pair)
    assert Wrap(MatrixKind(NumberKind)("A")).kind is Pair


def test_an_instantiated_kind_has_its_own_operators():
    Matrix = MatrixKind(kind("Scalar"))
    MatMul = function("MatMul", rest=Matrix, returns=Matrix)
    set_operator(Matrix, "*", MatMul)
    A, B = Matrix("A"), MatrixKind(Matrix.params[0])("B")
    assert repr(A * B) == "MatMul(A, B)"
    assert (A * B).kind is Matrix
    with pytest.raises(ValueError, match=r"^the \* operator is already set for MatrixKind\(Scalar\)$"):
        set_operator(MatrixKind(Matrix.params[0]), "*", MatMul)
    # Another instance of the family has no operators.
    with pytest.raises(TypeError, match="unsupported operand"):
        MatrixKind(BoolKind)("P") * MatrixKind(BoolKind)("Q")
    with pytest.raises(TypeError, match="unsupported operand"):
        Pair("p") + Pair("q")


def test_equality_and_hash_distinguish_parameters():
    a, b = MatrixKind(NumberKind)("p"), MatrixKind(BoolKind)("p")
    assert a != b
    assert hash(a) != hash(b)
    assert a == MatrixKind(NumberKind)("p")
    assert hash(a) == hash(MatrixKind(NumberKind)("p"))
    assert TupleKind(NumberKind, BoolKind)("p") != TupleKind(BoolKind, NumberKind)("p")
    assert MatrixKind(NumberKind)("p") != TupleKind(NumberKind)("p")
    assert MatrixKind(NumberKind)("p") != NumberKind("p")
    assert len({a, b, MatrixKind(NumberKind)("p"), NumberKind("p")}) == 3


def test_wrong_number_of_parameters():
    with pytest.raises(TypeError, match=r"^MatrixKind takes 1 parameter, got 2$"):
        MatrixKind(NumberKind, BoolKind)
    with pytest.raises(TypeError, match=r"^MatrixKind takes 1 parameter, got 0$"):
        MatrixKind()
    Map = kind_family("Map", params=2)
    assert repr(Map(NumberKind, BoolKind)) == "Map(NumberKind, BoolKind)"
    with pytest.raises(TypeError, match=r"^Map takes 2 parameters, got 1$"):
        Map(NumberKind)


def test_zero_parameters():
    with pytest.raises(TypeError, match=r"^TupleKind takes at least 1 parameter, got 0$"):
        TupleKind()
    for params in (0, -1):
        with pytest.raises(ValueError, match=f"^Empty: params must be at least 1, got {params}$"):
            kind_family("Empty", params=params)
    with pytest.raises(TypeError):
        kind_family("Bad", params="1")


def test_a_parameter_must_be_a_kind():
    for not_a_kind, text in (
        (1, "1"),
        ("NumberKind", "'NumberKind'"),
        (x, "x"),
        (MatrixKind, "<kind family MatrixKind>"),
        (Kind, "<class 'nary.Kind'>"),
        (None, "None"),
    ):
        with pytest.raises(TypeError, match=f"^expected a kind, got {text}$"):
            TupleKind(NumberKind, not_a_kind)
        with pytest.raises(TypeError, match=f"^expected a kind, got {text}$"):
            MatrixKind(not_a_kind)
    with pytest.raises(TypeError):
        MatrixKind(param=NumberKind)


def test_a_family_is_not_a_kind():
    with pytest.raises(TypeError, match=r"^expected a kind, got <kind family TupleKind>$"):
        function("f", TupleKind, returns=NumberKind)
    with pytest.raises(ValueError, match=r"^returns must be a kind, got <kind family TupleKind>$"):
        function("f", NumberKind, returns=TupleKind)
    with pytest.raises(TypeError, match=r"^expected a kind, got <kind family TupleKind>$"):
        set_operator(TupleKind, "+", nr.Add)


def test_kinds_and_families_are_read_only():
    with pytest.raises(AttributeError):
        Pair.family = MatrixKind
    with pytest.raises(AttributeError):
        Pair.params = ()
    with pytest.raises(AttributeError):
        TupleKind.params = 3


def test_instantiation_from_many_threads_gives_one_kind():
    Family = kind_family("Family")
    barrier = threading.Barrier(8)
    results = []

    def work():
        barrier.wait()
        results.append([Family(NumberKind, MatrixKind(BoolKind)) for _ in range(200)])

    threads = [threading.Thread(target=work) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    first = results[0][0]
    assert all(made is first for batch in results for made in batch)
    assert len(results) == 8

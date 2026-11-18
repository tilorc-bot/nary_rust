"""Functions are expressions of function kinds, Symbol(kind) positions, and
Lambda, defined in nary.functions."""

import nary as nr
import pytest
from nary import (
    BoolKind,
    Expr,
    FunctionKind,
    Lambda,
    NumberKind,
    Symbol,
    declare_function,
    is_lambda,
)

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")
NumToNum = FunctionKind((NumberKind,), NumberKind)
f = NumToNum("f")
# A function that takes a function.
Apply = declare_function("Apply", NumToNum, NumberKind, returns=NumberKind, names=("fn", "point"))
# A function whose second position accepts only a symbol.
Derivative = declare_function("Derivative", NumberKind, Symbol(NumberKind), returns=NumberKind)


def test_a_declared_function_is_an_expression_of_a_function_kind():
    assert type(nr.sin) is Expr
    assert nr.sin.kind is NumToNum
    assert nr.Eq.kind is FunctionKind((NumberKind, NumberKind), BoolKind)
    assert (NumToNum.inputs, NumToNum.rest, NumToNum.output) == ((NumberKind,), None, NumberKind)
    assert (nr.sin.name, nr.sin.head, nr.sin.args, nr.sin.is_symbol) == ("sin", None, (), False)
    assert repr(nr.sin) == "sin"
    assert repr(FunctionKind((), NumberKind, rest=NumberKind)) == "FunctionKind((), NumberKind, rest=NumberKind)"
    assert NumberKind.inputs is None and NumberKind.output is None


def test_function_kinds_are_compared_by_identity_and_nest():
    assert FunctionKind((NumberKind,), NumberKind) is NumToNum
    assert FunctionKind((NumberKind,), BoolKind) is not NumToNum
    assert FunctionKind((), NumberKind, rest=NumberKind) is not FunctionKind((), NumberKind)
    higher = FunctionKind((NumToNum,), NumToNum)
    assert higher.inputs[0] is NumToNum and higher.output is NumToNum
    assert nr.declare_kind_family("Box", params=1)(NumToNum).params == (NumToNum,)
    with pytest.raises(TypeError, match="^FunctionKind: inputs must be a tuple of kinds, got NumberKind$"):
        FunctionKind(NumberKind, NumberKind)


def test_declared_and_unknown_functions_can_be_passed_and_applied():
    assert repr(Apply(nr.sin, x)) == "Apply(sin, x)"
    assert repr(Apply(f, x)) == "Apply(f, x)"
    assert f.is_symbol and f.kind is NumToNum
    assert f(x).head is f and f(x).args == (x,) and f(x).kind is NumberKind
    assert repr(f(f(x)) + y) == "Add(f(f(x)), y)"
    g = FunctionKind((NumToNum,), NumToNum)("g")
    assert repr(g(nr.sin)(x)) == "g(sin)(x)"
    assert g(nr.sin)(x).head.head is g


def test_wrong_kind_wrong_count_and_calling_a_non_function():
    with pytest.raises(TypeError, match=r"^f expects NumberKind, got BoolKind: p$"):
        f(p)
    with pytest.raises(TypeError, match=r"^f takes 1 arguments, got 2$"):
        f(x, y)
    with pytest.raises(TypeError, match=r"^Apply expects FunctionKind\(\(NumberKind,\), NumberKind\), got FunctionKind\(\(NumberKind, NumberKind\), BoolKind\): Lt$"):
        Apply(nr.Lt, x)
    with pytest.raises(TypeError, match=r"^x is of kind NumberKind, which is not a function kind, so it cannot be called$"):
        x(y)
    with pytest.raises(TypeError, match=r"^Add\(x, y\) is of kind NumberKind, "):
        (x + y)(y)


def test_rest_functions():
    Max = declare_function("Max", NumberKind, rest=NumberKind, returns=NumberKind)
    assert Max.kind is FunctionKind((NumberKind,), NumberKind, rest=NumberKind)
    assert repr(Max(x, y, x)) == "Max(x, y, x)"
    with pytest.raises(TypeError, match=r"^Max takes at least 1 arguments, got 0$"):
        Max()
    with pytest.raises(TypeError, match=r"^Max expects NumberKind, got BoolKind: p$"):
        Max(x, p)


def test_two_declarations_with_the_same_name_are_different():
    a = declare_function("a", NumberKind, returns=NumberKind)
    b = declare_function("a", NumberKind, returns=NumberKind)
    assert a.kind is b.kind
    assert a != b and a == a
    assert a(x) != b(x) and a(x) == a(x)
    assert repr(a(x)) == repr(b(x)) == "a(x)"


def test_symbol_positions():
    assert Derivative.kind is FunctionKind((NumberKind, NumberKind), NumberKind)
    assert Derivative.kind.inputs == (NumberKind, NumberKind)
    assert repr(Derivative.params) == "(NumberKind, Symbol(NumberKind))"
    assert Derivative.params[1].kind is NumberKind
    assert nr.sin.params == (NumberKind,) and x.params is None
    assert repr(Derivative(nr.sin(x), x)) == "Derivative(sin(x), x)"
    with pytest.raises(TypeError, match=r"^Derivative expects a NumberKind symbol, got NumberKind: sin\(x\)$"):
        Derivative(x, nr.sin(x))
    with pytest.raises(TypeError, match=r"^Derivative expects NumberKind, got BoolKind: p$"):
        Derivative(x, p)
    # An unknown function of the same kind has no Symbol(kind) positions.
    unknown = Derivative.kind("unknown")
    assert repr(unknown(x, nr.sin(x))) == "unknown(x, sin(x))"


def test_lambda_is_an_application_of_a_function_named_lambda():
    one = Lambda(x, nr.sin(x))
    assert is_lambda(one) and one.kind is NumToNum
    assert one.args == (x, nr.sin(x)) and one.head.name == "Lambda"
    assert repr(one.head.params) == "(Symbol(NumberKind), NumberKind)"
    assert repr(one) == "Lambda(x, sin(x))"
    two = Lambda((x, y), x < y)
    assert two.kind is FunctionKind((NumberKind, NumberKind), BoolKind)
    assert repr(two) == "Lambda(x, y, Lt(x, y))"
    # The function for a combination of kinds is declared once.
    assert Lambda(y, nr.cos(y)).head is one.head
    assert Lambda((x,), x) == Lambda(x, x)
    assert not is_lambda(nr.sin(x)) and not is_lambda(x) and not is_lambda(1)
    assert repr(Apply(Lambda(x, x * x), y)) == "Apply(Lambda(x, Mul(x, x)), y)"


def test_lambda_errors():
    with pytest.raises(TypeError, match=r"^Lambda expects a NumberKind symbol, got NumberKind: Add\(x, y\)$"):
        Lambda(x + y, x)
    with pytest.raises(TypeError, match=r"^Lambda expects a FunctionKind\(\(NumberKind,\), NumberKind\) symbol, "):
        Lambda(nr.sin, x)
    with pytest.raises(ValueError, match=r"^Lambda variables must have different names, got x more than once$"):
        Lambda((x, y, NumberKind("x")), x)
    with pytest.raises(ValueError, match=r"^Lambda variables must have different names"):
        Lambda((x, BoolKind("x")), x)
    with pytest.raises(TypeError, match=r"^Lambda takes at least one variable"):
        Lambda((), x)
    with pytest.raises(TypeError, match=r"^the body of a Lambda must be an expression, got 1$"):
        Lambda(x, 1)


def test_applying_a_lambda_is_inert():
    square = Lambda(x, x * x)
    applied = square(y)
    assert applied.head is square and applied.args == (y,)
    assert applied.kind is NumberKind and not is_lambda(applied)
    assert repr(applied) == "Lambda(x, Mul(x, x))(y)"
    assert applied != y * y
    with pytest.raises(TypeError, match=r"^Lambda\(x, Mul\(x, x\)\) expects NumberKind, got BoolKind: p$"):
        square(p)


def test_equality_and_hash_across_forms():
    named = NumberKind("sin")
    sin_x = nr.sin(x)
    forms = [named, nr.sin, sin_x, Lambda(x, sin_x), NumToNum("sin"), nr.Add(), NumberKind("Add")]
    for i, a in enumerate(forms):
        for j, b in enumerate(forms):
            assert (a == b) is (i == j)
    assert repr(nr.Add()) == repr(NumberKind("Add")) == "Add"
    assert len(set(forms)) == len(forms)
    # Equal expressions have equal hashes.
    assert hash(nr.sin(x)) == hash(sin_x) and hash(NumberKind("sin")) == hash(named)
    assert hash(Lambda(x, sin_x)) == hash(Lambda(NumberKind("x"), nr.sin(x)))
    # Lambdas are compared with their variable names: no renaming.
    assert Lambda(x, x) != Lambda(y, y)
    assert hash(f(x)) == hash(NumToNum("f")(x)) and f(x) == NumToNum("f")(x)


def test_named_arguments_come_from_the_head():
    a = Apply(nr.sin, x)
    assert (a.fn, a.point) == (nr.sin, x)
    assert nr.Eq(x, y).lhs == x
    assert Apply.names == ("fn", "point") and nr.sin.names == ()
    with pytest.raises(AttributeError):
        f(x).lhs


def test_set_operator_takes_any_expression_of_a_function_kind():
    Point = nr.declare_kind("Point")
    join = FunctionKind((Point, Point), Point)("join")
    nr.set_operator(Point, "+", join)
    P, Q = Point("P"), Point("Q")
    assert repr(P + Q) == "join(P, Q)" and (P + Q).head is join
    with pytest.raises(TypeError, match=r"^set_operator expects an expression of a function kind, got x$"):
        nr.set_operator(Point, "*", x)

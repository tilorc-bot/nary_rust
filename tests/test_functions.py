import threading

import nary as nr
import pytest
from nary import (
    BoolKind,
    Bound,
    Expr,
    FunctionKind,
    Lambda,
    Many,
    NumberKind,
    declare_function,
    is_lambda,
)
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")
p = BoolKind("p")
NumToNum = FunctionKind((NumberKind,), NumberKind)
f = NumToNum("f")
Apply = declare_function("Apply", NumToNum("fn"), NumberKind("point"), returns=NumberKind, domain=true)
expr, variable = NumberKind("expr"), NumberKind("variable")
Derivative = declare_function("Derivative", expr, Bound(variable), returns=NumberKind, domain=true)


def test_a_declared_function_is_an_expression_of_a_function_kind():
    assert type(nr.sin) is Expr
    assert nr.sin.kind is NumToNum
    assert repr(nr.Eq.kind) == "FunctionKind((K, K), BoolKind)"
    assert (NumToNum.inputs, NumToNum.output) == ((NumberKind,), NumberKind)
    assert (nr.sin.name, nr.sin.head, nr.sin.args, nr.sin.is_symbol) == ("sin", None, (), False)
    assert repr(nr.sin) == "sin"
    assert repr(FunctionKind((Many(NumberKind),), NumberKind)) == "FunctionKind((Many(NumberKind),), NumberKind)"
    assert NumberKind.inputs is None and NumberKind.output is None


def test_function_kinds_are_compared_by_identity_and_nest():
    assert FunctionKind((NumberKind,), NumberKind) is NumToNum
    assert FunctionKind((NumberKind,), BoolKind) is not NumToNum
    assert FunctionKind((Many(NumberKind),), NumberKind) is not FunctionKind((NumberKind,), NumberKind)
    assert FunctionKind((NumberKind, Many(NumberKind)), NumberKind) is not FunctionKind((Many(NumberKind), NumberKind), NumberKind)
    for kind in (nr.Add.kind, nr.Pow.kind, FunctionKind((NumberKind, Many(BoolKind), NumberKind), BoolKind)):
        assert FunctionKind(kind.inputs, kind.output) is kind
    higher = FunctionKind((NumToNum,), NumToNum)
    assert higher.inputs[0] is NumToNum and higher.output is NumToNum
    assert nr.declare_kind_family("Box", params=1)(NumToNum).params == (NumToNum,)
    with pytest.raises(TypeError, match="^FunctionKind: inputs must be a tuple of kinds, got NumberKind$"):
        FunctionKind(NumberKind, NumberKind)
    with pytest.raises(TypeError, match=r"^FunctionKind: at most one input can be Many or ManyMixed, got \(Many\(NumberKind\), Many\(BoolKind\)\)$"):
        FunctionKind((Many(NumberKind), Many(BoolKind)), NumberKind)
    with pytest.raises(TypeError, match="^expected a kind, got x$"):
        FunctionKind((Many(x),), NumberKind)
    with pytest.raises(TypeError, match="^Many takes a kind or a symbol, got 1$"):
        Many(1)


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


def test_a_run_takes_any_number_of_arguments_and_may_sit_anywhere():
    first, rest = NumberKind("first"), NumberKind("rest")
    Max = declare_function("Max", first, Many(rest), returns=NumberKind, domain=true)
    assert Max.kind is FunctionKind((NumberKind, Many(NumberKind)), NumberKind)
    assert repr(Max(x, y, x)) == "Max(x, y, x)"
    assert (Max(x, y, 1).first, Max(x, y, 1).rest, Max(x).rest) == (x, (y, NumberKind(1)), ())
    with pytest.raises(TypeError, match=r"^Max takes at least 1 arguments, got 0$"):
        Max()
    with pytest.raises(TypeError, match=r"^Max expects NumberKind, got BoolKind: p$"):
        Max(x, p)
    conditions, result = BoolKind("conditions"), NumberKind("result")
    Guard = declare_function("Guard", Many(conditions), result, returns=NumberKind, domain=true)
    g = Guard(x < y, p, 1)
    assert (g.conditions, g.result, Guard(x).conditions) == ((x < y, p), NumberKind(1), ())
    with pytest.raises(TypeError, match=r"^Guard expects NumberKind, got BoolKind: p$"):
        Guard(p, p)
    with pytest.raises(TypeError, match=r"^Guard expects BoolKind, got NumberKind: x$"):
        Guard(x, p, x)


def test_two_declarations_with_the_same_name_are_different():
    a = declare_function("a", x, returns=NumberKind, domain=true)
    b = declare_function("a", x, returns=NumberKind, domain=true)
    assert a.kind is b.kind
    assert a != b and a == a
    assert a(x) != b(x) and a(x) == a(x)
    assert repr(a(x)) == repr(b(x)) == "a(x)"


def test_bound_positions():
    assert Derivative.kind is FunctionKind((NumberKind, NumberKind), NumberKind)
    assert Derivative.params == (expr, Bound(variable))
    assert repr(Derivative.params) == "(expr, Bound(variable))"
    assert Derivative.params[1].of == variable and Bound(variable) != variable
    assert nr.sin.params == (NumberKind("arg"),) and x.params is None
    assert repr(Derivative(nr.sin(x), x)) == "Derivative(sin(x), x)"
    with pytest.raises(TypeError, match=r"^Derivative expects a NumberKind symbol, got sin\(x\)$"):
        Derivative(x, nr.sin(x))
    with pytest.raises(TypeError, match=r"^Derivative expects NumberKind, got BoolKind: p$"):
        Derivative(x, p)
    variables = NumberKind("variables")
    D = declare_function("D", expr, Many(Bound(variables)), returns=NumberKind, domain=true)
    assert D.params == (expr, Many(Bound(variables)))
    assert D(x * y, x, y).variables == (x, y)
    with pytest.raises(TypeError, match=r"^D expects a NumberKind symbol, got Add\(x, y\)$"):
        D(x, y, x + y)
    with pytest.raises(TypeError, match="^Bound takes a symbol, got NumberKind$"):
        Bound(NumberKind)
    unknown = Derivative.kind("unknown")
    assert repr(unknown(x, nr.sin(x))) == "unknown(x, sin(x))"


def test_lambda_is_an_application_of_a_function_named_lambda():
    one = Lambda(x, nr.sin(x))
    assert is_lambda(one) and one.kind is NumToNum
    assert one.args == (x, nr.sin(x)) and one.head.name == "Lambda"
    assert repr(one.head.params) == "(ManyMixed(Bound(variables)), expr)"
    assert one.expr == nr.sin(x) and one.variables == (x,)
    assert repr(one) == "Lambda(x, sin(x))"
    two = Lambda((x, y), x < y)
    assert two.kind is FunctionKind((NumberKind, NumberKind), BoolKind)
    assert repr(two) == "Lambda(x, y, Lt(x, y))"
    assert two.variables == (x, y) and two.head is one.head is Lambda(p, p).head
    assert Lambda((p, x), x).kind is FunctionKind((BoolKind, NumberKind), NumberKind)
    assert Lambda((x,), x) == Lambda(x, x)
    assert not is_lambda(nr.sin(x)) and not is_lambda(x) and not is_lambda(1)
    assert repr(Apply(Lambda(x, x * x), y)) == "Apply(Lambda(x, Mul(x, x)), y)"


def test_lambda_errors():
    with pytest.raises(TypeError, match=r"^Lambda expects a NumberKind symbol, got Add\(x, y\)$"):
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
    assert hash(nr.sin(x)) == hash(sin_x) and hash(NumberKind("sin")) == hash(named)
    assert hash(Lambda(x, sin_x)) == hash(Lambda(NumberKind("x"), nr.sin(x)))
    assert Lambda(x, x) != Lambda(y, y)
    assert hash(f(x)) == hash(NumToNum("f")(x)) and f(x) == NumToNum("f")(x)


def test_named_arguments_come_from_the_head():
    a = Apply(nr.sin, x)
    assert (a.fn, a.point) == (nr.sin, x)
    assert nr.Eq(x, y).lhs == x and nr.sin(y).arg == y
    assert nr.Add(x, y, 1).terms == (x, y, NumberKind(1)) and nr.Mul().factors == ()
    assert Apply.params == (NumToNum("fn"), NumberKind("point"))
    assert Derivative(x, y).variable == y
    with pytest.raises(AttributeError):
        f(x).lhs


def test_every_parameter_is_a_named_symbol():
    with pytest.raises(TypeError, match=r'^f: a parameter must be a symbol, such as NumberKind\("x"\), got NumberKind$'):
        declare_function("f", NumberKind, returns=NumberKind, domain=true)
    for not_a_symbol in (x + 1, nr.sin, 1, Many(NumberKind)):
        with pytest.raises(TypeError, match="^f: a parameter must be a symbol"):
            declare_function("f", not_a_symbol, returns=NumberKind, domain=true)
    with pytest.raises(TypeError, match=r"^f: at most one parameter can be Many or ManyMixed, got \(Many\(x\), Many\(y\)\)$"):
        declare_function("f", Many(x), Many(y), returns=NumberKind, domain=true)
    with pytest.raises(ValueError, match="^f has two parameters named x$"):
        declare_function("f", x, Many(BoolKind("x")), returns=NumberKind, domain=true)


def test_a_parameter_name_cannot_hide_an_attribute_of_an_expression():
    for attribute in ("kind", "args", "value", "head", "name", "params", "is_symbol", "__class__"):
        with pytest.raises(ValueError, match=f"^f: the parameter name {attribute} clashes with the attribute Expr.{attribute}$"):
            declare_function("f", NumberKind(attribute), returns=NumberKind, domain=true)
    assert declare_function("f", NumberKind("names"), returns=NumberKind, domain=true)(x).names == x


def test_set_operator_takes_any_expression_of_a_function_kind():
    Point = nr.declare_kind("Point")
    join = FunctionKind((Point, Point), Point)("join")
    nr.set_operator(Point, "+", join)
    P, Q = Point("P"), Point("Q")
    assert repr(P + Q) == "join(P, Q)" and (P + Q).head is join
    with pytest.raises(TypeError, match=r"^set_operator expects an expression of a function kind, got x$"):
        nr.set_operator(Point, "*", x)


def test_the_same_function_kind_from_many_threads():
    Fresh = nr.declare_kind("Fresh")
    barrier = threading.Barrier(8)
    made = []

    def make():
        barrier.wait()
        made.append([FunctionKind((Fresh, NumberKind, Many(Fresh)), Fresh) for _ in range(200)])

    threads = [threading.Thread(target=make) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(made) == 8 and all(kind is made[0][0] for batch in made for kind in batch)


def test_a_declared_constant_of_a_function_kind_is_a_function_without_params():
    c = nr.declare_constant("c", FunctionKind((NumberKind,), NumberKind))
    x = NumberKind("x")
    assert c.is_constant and c.params is None and c.kind.inputs == (NumberKind,)
    assert repr(c(x)) == "c(x)"


def test_pow_with_a_modulus_is_refused():
    with pytest.raises(TypeError, match="modulus"):
        pow(2, NumberKind("x"), 3)
    with pytest.raises(TypeError, match="modulus"):
        pow(NumberKind("x"), 2, 3)

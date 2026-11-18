"""Integers, reflected operators, and -, / and unary minus."""

import nary as nr
import pytest
from nary import BoolKind, FunctionKind, Integer, NumberKind, Symbol, declare_function

x, y = NumberKind("x"), NumberKind("y")


def test_expressions_with_ints():
    cases = {
        "Add(x, 1)": x + 1, "Add(1, x)": 1 + x,
        "Mul(2, x)": 2 * x, "Pow(x, 2)": x ** 2, "Pow(2, x)": 2 ** x,
        "Add(1, Mul(-1, x))": 1 - x, "Mul(1, Pow(x, -1))": 1 / x,
        "Gt(x, 0)": x > 0, "sin(1)": nr.sin(1), "3": Integer(3),
    }
    for text, e in cases.items():
        assert repr(e) == text
        assert e.kind is (BoolKind if e.head is nr.Gt else NumberKind)


def test_subtraction_division_and_negation_are_add_mul_and_pow():
    minus_one = Integer(-1)
    assert x - y == nr.Add(x, nr.Mul(minus_one, y))
    assert x / y == nr.Mul(x, nr.Pow(y, minus_one))
    assert -x == nr.Mul(minus_one, x)
    assert repr(x - y) == "Add(x, Mul(-1, y))"


def test_a_comparison_with_an_int_on_the_left_is_swapped_by_python():
    assert (1 < x) == nr.Gt(x, 1)
    assert (1 >= x) == nr.Le(x, 1)


def test_an_integer_is_a_leaf_with_a_value():
    big = 10**40
    n = Integer(big)
    assert n.is_integer and not n.is_symbol and not x.is_integer
    assert n.value == big and type(n.value) is int and x.value is None
    assert (n.head, n.name, n.args, repr(n)) == (None, None, (), str(big))
    assert (x + 1).args[1].is_integer


def test_integer_equality_and_hash_follow_the_value():
    assert Integer(2) == Integer(2) and hash(Integer(2)) == hash(Integer(2))
    assert Integer(2) != Integer(3)
    assert Integer(2) != NumberKind("2") and Integer(2) != 2
    assert x + 1 == nr.Add(x, Integer(1))
    assert len({Integer(5), Integer(5), x + 1, 1 + x}) == 3


def test_bool_and_float_are_not_integers():
    with pytest.raises(TypeError, match=r"^Integer expects an int, got bool: True$"):
        Integer(True)
    with pytest.raises(TypeError, match=r"^Integer expects an int, got float: 2.0$"):
        Integer(2.0)
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got bool: True$"):
        x + True
    with pytest.raises(TypeError):
        True + x
    with pytest.raises(TypeError):
        2.0 * x


def test_an_integer_is_rejected_where_a_boolkind_or_a_symbol_is_required():
    from nary.logic import Not

    with pytest.raises(TypeError, match=r"^Not expects BoolKind, got int: 1$"):
        Not(1)
    with pytest.raises(TypeError, match=r"^Not expects BoolKind, got NumberKind: 1$"):
        Not(Integer(1))
    Derivative = declare_function("Derivative", NumberKind, Symbol(NumberKind), returns=NumberKind)
    with pytest.raises(TypeError, match=r"^Derivative expects a NumberKind symbol, got NumberKind: 2$"):
        Derivative(x, 2)
    with pytest.raises(TypeError, match=r"^Lambda expects a NumberKind symbol, got NumberKind: 1$"):
        nr.Lambda(Integer(1), x)


def test_an_integer_cannot_be_called_and_its_kind_is_set_once():
    with pytest.raises(TypeError, match=r"^3 is of kind NumberKind, which is not a function kind"):
        Integer(3)(x)
    with pytest.raises(ValueError, match=r"^integers are already declared to be NumberKind$"):
        nr.set_integer_kind(BoolKind)
    with pytest.raises(ValueError, match=r"^integers cannot be of the function kind"):
        nr.set_integer_kind(FunctionKind((NumberKind,), NumberKind))


def test_an_operator_given_a_python_function():
    Vector = nr.declare_kind("Vector")
    VAdd = declare_function("VAdd", rest=Vector, returns=Vector)
    Scale = declare_function("Scale", NumberKind, Vector, returns=Vector)
    nr.set_operator(Vector, "+", VAdd)
    nr.set_operator(Vector, "-", lambda a, b: VAdd(a, Scale(Integer(-1), b)))
    nr.set_operator(Vector, "neg", lambda a: Scale(Integer(-1), a))
    # The int operand is an Integer by the time the function sees it.
    nr.set_operator(Vector, "*", lambda a, b: Scale(b, a) if b.is_integer else None)
    nr.set_operator(Vector, "/", lambda a, b: "not an expression")
    u, v = Vector("u"), Vector("v")
    assert repr(u - v) == "VAdd(u, Scale(-1, v))" and (u - v).kind is Vector
    assert repr(-u) == "Scale(-1, u)"
    assert repr(u * 3) == "Scale(3, u)"
    with pytest.raises(TypeError, match=r"^the / operator for Vector must build an expression, got str: 'not an expression'$"):
        u / v
    with pytest.raises(TypeError, match=r"^bad operand type for unary -: an expression of kind BoolKind$"):
        -BoolKind("p")
    with pytest.raises(TypeError, match=r"^set_operator expects an expression of a function kind or a Python function, got 'Mul'$"):
        nr.set_operator(Vector, "**", "Mul")

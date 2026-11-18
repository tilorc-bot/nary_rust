"""Kinds are declared in Python. The compiled module defines none."""

import nary as nr
import pytest
from nary import BoolKind, Expr, Kind, NumberKind, _core, declare_function, declare_kind, set_operator

# A kind that nary does not have, declared here with its functions and an
# operator. Nothing in Rust knows about it.
SetKind = declare_kind("SetKind")

Union = declare_function("Union", rest=SetKind, returns=SetKind)
Interval = declare_function("Interval", NumberKind, NumberKind, returns=SetKind, names=("start", "end"))
Contains = declare_function("Contains", NumberKind, SetKind, returns=BoolKind)
set_operator(SetKind, "+", Union)

x, y = NumberKind("x"), NumberKind("y")


def test_the_compiled_module_defines_no_kind_and_no_function():
    public = {name for name in dir(_core) if not name.startswith("_")}
    assert public == {
        "Expr", "FunctionKind", "Kind", "KindFamily", "Symbol",
        "declare_function", "declare_kind", "declare_kind_family", "set_operator",
    }


def test_a_kind_is_an_object_declared_with_declare_kind():
    for declared, name in ((NumberKind, "NumberKind"), (BoolKind, "BoolKind"), (SetKind, "SetKind")):
        assert type(declared) is Kind
        assert declared.name == name
        assert repr(declared) == name
    assert NumberKind is not BoolKind


def test_every_call_of_declare_kind_makes_a_different_kind():
    a, b = declare_kind("Twin"), declare_kind("Twin")
    assert a is not b
    f = declare_function("f", a, returns=a)
    with pytest.raises(TypeError, match=r"^f expects Twin, got Twin: t$"):
        f(b("t"))
    assert a("t") != b("t")


def test_calling_a_kind_makes_a_leaf_of_that_kind():
    s = SetKind("S")
    assert type(s) is Expr
    assert s.kind is SetKind
    assert (s.head, s.name, s.args, repr(s)) == (None, "S", (), "S")
    with pytest.raises(TypeError):
        SetKind(1)
    with pytest.raises(TypeError):
        SetKind()


def test_calling_a_kind_takes_only_the_name():
    # Calling a kind cannot build a node: that would skip every kind check.
    message = r"^{} takes 1 argument, the name of a leaf, got {}; a node is built by calling a function$"
    with pytest.raises(TypeError, match=message.format("NumberKind", 4)):
        NumberKind("Add", x, 1, [2])
    with pytest.raises(TypeError, match=message.format("NumberKind", 3)):
        NumberKind("Add", x, y)
    with pytest.raises(TypeError, match=message.format("NumberKind", 2)):
        NumberKind("sin", x < y)
    with pytest.raises(TypeError, match=message.format("SetKind", 2)):
        SetKind("S", "T")
    with pytest.raises(TypeError):
        NumberKind("x", args=(y,))


def test_a_leaf_has_no_arguments_and_nodes_are_built_by_functions():
    for leaf in (x, NumberKind("x"), BoolKind("p"), SetKind("S")):
        assert leaf.args == ()
    assert nr.Add(x, y) == x + y
    assert nr.Add(x, y).args == (x, y)
    assert nr.sin(x).args == (x,)
    assert Contains(x, SetKind("S")).args == (x, SetKind("S"))
    # Every argument of every node is an expression that passed a kind check.
    stack = [nr.Eq(nr.sin(x) * y + x, nr.Pow(x, y)), Contains(x, Union(Interval(x, y)))]
    while stack:
        node = stack.pop()
        assert type(node) is Expr
        stack.extend(node.args)


def test_expr_cannot_be_called_or_subclassed():
    with pytest.raises(TypeError):
        Expr("x")
    with pytest.raises(TypeError):
        class Sub(Expr):
            pass


def test_kind_is_read_only():
    with pytest.raises(AttributeError):
        x.kind = BoolKind
    with pytest.raises(AttributeError):
        x.head = "y"


def test_a_new_kind_in_signatures():
    s = SetKind("S")
    i = Interval(x, y)
    assert i.kind is SetKind
    assert (i.start, i.end) == (x, y)
    u = Union(i, s, s)
    assert u.kind is SetKind
    assert repr(u) == "Union(Interval(x, y), S, S)"
    c = Contains(x, u)
    assert c.kind is BoolKind
    assert repr(c) == "Contains(x, Union(Interval(x, y), S, S))"


def test_a_new_kind_is_checked_against_the_others():
    s = SetKind("S")
    with pytest.raises(TypeError, match=r"^Union expects SetKind, got NumberKind: x$"):
        Union(s, x)
    with pytest.raises(TypeError, match=r"^Contains expects NumberKind, got SetKind: S$"):
        Contains(s, s)
    with pytest.raises(TypeError, match=r"^sin expects NumberKind, got SetKind: S$"):
        nr.sin(s)
    with pytest.raises(TypeError, match=r"^Contains expects SetKind, got BoolKind: Lt\(x, y\)$"):
        Contains(x, x < y)
    assert SetKind("p") != NumberKind("p")
    assert SetKind("p") != BoolKind("p")
    assert hash(SetKind("p")) != hash(NumberKind("p"))


def test_operators_are_registered_for_each_kind():
    s, t = SetKind("S"), SetKind("T")
    assert repr(s + t) == "Union(S, T)"
    assert repr(x + y) == "Add(x, y)"
    assert (s + t).kind is SetKind
    # The function of the left operand's kind is the one that is built.
    with pytest.raises(TypeError, match=r"^Union expects SetKind, got NumberKind: x$"):
        s + x
    with pytest.raises(TypeError, match=r"^Add expects NumberKind, got SetKind: S$"):
        x + s
    # SetKind has + but not * or <.
    with pytest.raises(TypeError, match="unsupported operand"):
        s * t
    with pytest.raises(TypeError, match="not supported between instances"):
        s < t


def test_set_operator_once_for_each_kind_and_operator():
    with pytest.raises(ValueError, match=r"^the \+ operator is already set for NumberKind$"):
        set_operator(NumberKind, "+", nr.Add)
    with pytest.raises(ValueError, match=r"^the \+ operator is already set for SetKind$"):
        set_operator(SetKind, "+", Union)
    with pytest.raises(ValueError, match='^unknown operator "%"$'):
        set_operator(NumberKind, "%", nr.Add)
    with pytest.raises(TypeError):
        set_operator(NumberKind, "*", "Mul")


def test_only_a_kind_is_accepted_where_a_kind_is_expected():
    for not_a_kind, text in ((Expr, "<class 'nary.Expr'>"), (int, "<class 'int'>"), (x, "x"), ("NumberKind", "'NumberKind'"), (Kind, "<class 'nary.Kind'>")):
        with pytest.raises(TypeError, match=f"^expected a kind, got {text}$"):
            declare_function("f", not_a_kind, returns=NumberKind)
        with pytest.raises(TypeError, match=f"^expected a kind, got {text}$"):
            declare_function("f", rest=not_a_kind, returns=NumberKind)
        with pytest.raises(ValueError, match=f"^returns must be a kind, got {text}$"):
            declare_function("f", NumberKind, returns=not_a_kind)
        with pytest.raises(TypeError, match=f"^expected a kind, got {text}$"):
            set_operator(not_a_kind, "+", nr.Add)


def test_an_argument_must_be_an_expression():
    for value, text in ((1, "int: 1"), ("x", "str: 'x'"), (NumberKind, "Kind: NumberKind"), (None, "NoneType: None")):
        with pytest.raises(TypeError, match=f"^sin expects NumberKind, got {text}$"):
            nr.sin(value)

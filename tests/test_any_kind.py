"""AnyKind: no particular kind, accepted only where it is expected.

A position of kind AnyKind accepts an expression of any kind, and no other
position accepts an expression of kind AnyKind. So an expression whose kind
is not generic contains no AnyKind anywhere, and what gives meaning refuses
generic expressions.
"""

import nary as nr
import pytest
from nary import (
    AnyKind, BoolKind, FunctionKind, Kind, NumberKind, Symbol, declare_constant,
    declare_function, declare_kind_family, sin,
)
from nary import _core
from nary.domains import domain_of
from nary.lean import to_lean, to_lean_example
from nary.logic import And, false, true
from nary.rewriting import rewrite
from nary.rules import flat, is_unordered, rule, unordered

x, p = NumberKind("x"), BoolKind("p")
a, b = AnyKind("a"), AnyKind("b")

# A generic function: any number of arguments of any kind.
Generic = FunctionKind((), AnyKind, rest=AnyKind)
f = Generic("f")
statement = _core.declare_function("statement", AnyKind, AnyKind, returns=AnyKind)


def test_any_kind_is_a_kind_defined_in_rust():
    assert type(AnyKind) is Kind
    assert nr.AnyKind is _core.AnyKind
    assert repr(AnyKind) == AnyKind.name == "AnyKind"
    assert AnyKind.literals == () and AnyKind.params == () and AnyKind.inputs is None


def test_which_kinds_are_generic():
    assert AnyKind.generic and Generic.generic
    assert FunctionKind((NumberKind,), AnyKind).generic
    assert FunctionKind((), FunctionKind((AnyKind,), AnyKind)).generic
    for kind in (NumberKind, BoolKind, FunctionKind((NumberKind,), NumberKind)):
        assert not kind.generic


def test_an_any_kind_position_accepts_an_expression_of_any_kind():
    for arg in (x, p, sin(x) + 1, And(p, true), sin, nr.Add, a):
        e = f(arg)
        assert e.kind is AnyKind and e.args == (arg,)
    assert statement(x, p).args == (x, p)
    # A generic tree may hold several kinds at once.
    assert repr(f(f(a), x, sin)) == "f(f(a), x, sin)"


def test_an_any_kind_position_accepts_no_python_value():
    with pytest.raises(TypeError, match=r"f expects AnyKind, got int: 0; AnyKind accepts .* NumberKind\(0\)"):
        f(0)
    with pytest.raises(TypeError, match="AnyKind takes a name"):
        AnyKind(0)


def test_no_other_position_accepts_any_kind():
    with pytest.raises(TypeError, match="Add expects NumberKind, got AnyKind: a"):
        nr.Add(x, a)
    with pytest.raises(TypeError, match="sin expects NumberKind, got AnyKind: f"):
        sin(f(x))
    with pytest.raises(TypeError, match="And expects BoolKind, got AnyKind"):
        And(p, b)
    # A function position expects its exact function kind.
    apply_number = declare_function(
        "apply_number", FunctionKind((NumberKind,), NumberKind), NumberKind,
        returns=NumberKind, domain=true,
    )
    with pytest.raises(TypeError, match="expects FunctionKind"):
        apply_number(FunctionKind((NumberKind,), AnyKind)("g"), x)


def test_a_function_that_takes_any_kind_must_return_a_generic_kind():
    with pytest.raises(TypeError, match=r"FunctionKind\(\(AnyKind,\), NumberKind\) is refused"):
        FunctionKind((AnyKind,), NumberKind)
    with pytest.raises(TypeError, match="is refused"):
        FunctionKind((), BoolKind, rest=AnyKind)
    with pytest.raises(TypeError, match="is refused"):
        FunctionKind((FunctionKind((AnyKind,), AnyKind),), NumberKind)
    with pytest.raises(TypeError, match="is refused"):
        _core.declare_function("g", AnyKind, returns=NumberKind)
    # Returning AnyKind from fixed kinds is allowed: the result is generic.
    assert FunctionKind((NumberKind,), AnyKind).generic


def test_a_kind_family_refuses_generic_parameters():
    TupleKind = declare_kind_family("TupleKind")
    with pytest.raises(TypeError, match="TupleKind cannot take the generic kind AnyKind"):
        TupleKind(AnyKind)
    with pytest.raises(TypeError, match="cannot take the generic kind"):
        TupleKind(NumberKind, Generic)


def test_symbols_and_constants_of_any_kind():
    assert a == AnyKind("a") and a != NumberKind("a") and hash(a) == hash(AnyKind("a"))
    c = declare_constant("c", AnyKind)
    assert c.kind is AnyKind and f(c).args == (c,)


def test_declaring_a_function_with_a_domain_refuses_generic_kinds():
    with pytest.raises(TypeError, match="g cannot be declared with the generic kind AnyKind"):
        declare_function("g", AnyKind, returns=AnyKind, domain=true)
    with pytest.raises(TypeError, match="generic kind AnyKind"):
        declare_function("g", rest=AnyKind, returns=AnyKind, domain=true)
    with pytest.raises(TypeError, match="generic kind AnyKind"):
        declare_function("g", NumberKind, returns=AnyKind, domain=true)
    with pytest.raises(TypeError, match="generic kind AnyKind"):
        declare_function("g", AnyKind("t"), returns=AnyKind, domain=true)
    with pytest.raises(TypeError, match="generic kind AnyKind"):
        declare_function("g", Symbol(AnyKind), returns=AnyKind, domain=true)


def test_what_gives_meaning_refuses_generic_expressions():
    with pytest.raises(TypeError, match="domain_of cannot give a domain"):
        domain_of(statement(x, p))
    with pytest.raises(TypeError, match="rewrite cannot rewrite"):
        rewrite(f(x), [])
    with pytest.raises(TypeError, match="pattern of a rule cannot be of the generic kind"):
        rule(f(a), a)
    with pytest.raises(TypeError, match="generic kind"):
        unordered(statement)
    with pytest.raises(TypeError, match="generic kind"):
        flat(_core.declare_function("h", rest=AnyKind, returns=AnyKind))
    with pytest.raises(TypeError, match="generic kind"):
        is_unordered(statement)
    with pytest.raises(ValueError, match="generic kind AnyKind, which has no Lean definition"):
        to_lean(f(x))
    with pytest.raises(ValueError, match="no Lean definition"):
        to_lean_example(a)


def test_rewriting_and_printing_are_unchanged_for_other_kinds():
    assert rewrite(And(p, false), []) == And(p, false)
    assert to_lean(sin(x)) == "Nary.sin (some x)"

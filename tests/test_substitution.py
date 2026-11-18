"""Free symbols, substitution and applying a lambda, in nary.substitution."""

import doctest

import nary.substitution
import pytest
from nary import BoolKind, Lambda, NumberKind, Symbol, declare_function, sin
from nary.calculus import Derivative, Integral, NumberFunction
from nary.substitution import apply_lambda, free_symbols, substitute

x, y, z, a, b = (NumberKind(n) for n in "xyzab")
f = NumberFunction("f")


def test_free_symbols_looks_in_heads_and_skips_bound_variables():
    assert free_symbols(sin(x) + y) == {x, y}
    assert free_symbols(Derivative(f)(a)) == {f, a}
    assert free_symbols(Lambda(x, x * y)(z)) == {y, z}
    assert free_symbols(Integral(Lambda(x, x), x, a)) == {x, a}
    assert free_symbols(sin) == set()


def test_substitution_is_simultaneous_and_on_free_occurrences_only():
    assert substitute(x * y, {x: y, y: x}) == y * x
    expr = Integral(Lambda(x, x * y), x, y)
    assert substitute(expr, {x: a, y: b}) == Integral(Lambda(x, x * b), a, b)


def test_capture_is_avoided_by_renaming_the_variable():
    result = substitute(Integral(Lambda(x, x * y), a, b), {y: x})
    x_1 = NumberKind("x_1")
    assert result == Integral(Lambda(x_1, x_1 * x), a, b)
    # The fresh name is not one already in use in the lambda.
    result = substitute(Lambda(x, x * NumberKind("x_1") * y), {y: x})
    x_2 = NumberKind("x_2")
    assert result == Lambda(x_2, x_2 * x_1 * x)


def test_nothing_is_renamed_or_rebuilt_when_not_needed():
    expr = Integral(Lambda(x, x * y), a, b)
    assert substitute(expr, {z: x}) is expr          # z does not occur
    assert substitute(expr, {x: a}) is expr          # x is bound
    assert substitute(expr, {y: z}) == Integral(Lambda(x, x * z), a, b)


def test_a_function_symbol_is_replaced_and_left_unapplied():
    result = substitute(f(a), {f: Lambda(x, sin(x))})
    assert repr(result) == "Lambda(x, sin(x))(a)"
    assert apply_lambda(result) == sin(a)


def test_wrong_keys_and_kinds_are_type_errors():
    with pytest.raises(TypeError, match=r"^only a symbol can be replaced, got Add\(x, y\)$"):
        substitute(x, {x + y: z})
    with pytest.raises(TypeError, match=r"^cannot replace x, of kind NumberKind, with p, of kind BoolKind$"):
        substitute(x, {x: BoolKind("p")})
    # A position that accepts only a symbol is checked again by the core.
    D = declare_function("D", NumberKind, Symbol(NumberKind), returns=NumberKind)
    with pytest.raises(TypeError, match=r"^D expects a NumberKind symbol"):
        substitute(D(sin(x), x), {x: sin(y)})


def test_apply_lambda_substitutes_all_variables_at_once():
    assert apply_lambda(Lambda((x, y), x < y)(y, x)) == (y < x)
    # Applying inside a nested lambda still avoids capture.
    inner = Lambda(y, x * y)
    assert apply_lambda(Lambda(x, inner)(y)) == Lambda(NumberKind("y_1"), y * NumberKind("y_1"))
    for not_applied in (x, sin(x), Lambda(x, x), f(a)):
        with pytest.raises(ValueError, match=r"^apply_lambda expects a lambda applied to arguments"):
            apply_lambda(not_applied)


def test_module_docstring_examples():
    result = doctest.testmod(nary.substitution, optionflags=doctest.ELLIPSIS)
    assert result.attempted > 0
    assert result.failed == 0

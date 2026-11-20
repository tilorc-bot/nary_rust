"""Applying rules with nary.rewriting."""

import doctest

import nary.rewriting
from nary import Add, Lambda, Mul, Ne, NumberKind, cos, log, sin, tan
from nary.arithmetic_rules import rules
from nary.rewriting import rewrite

x, y = NumberKind("x"), NumberKind("y")


def test_docstring_examples():
    result = doctest.testmod(nary.rewriting)
    assert result.attempted > 0 and result.failed == 0


def test_unordered_and_flat_matching():
    assert rewrite(Add(0, x), rules) == x
    assert rewrite(Add(x, 0, y), rules) == Add(x, y)
    assert rewrite(Add(x, y, x), rules) == Add(Mul(2, x), y)


def test_inside_a_larger_expression():
    assert rewrite(sin(x + 0) < y, rules) == (sin(x) < y)


def test_condition():
    assert rewrite(x / x, rules) == x / x
    assert rewrite(x / x, rules, known=lambda condition: condition == Ne(x, 0)) == NumberKind(1)


def test_erased_variable():
    assert rewrite(x * 0, rules) == NumberKind(0)
    assert rewrite(log(x) * 0, rules) == log(x) * 0


def test_erased_variable_with_a_domain():
    # sin and cos have the domain true; log has Ne(x, 0), tan Ne(cos(x), 0).
    assert rewrite(sin(x) * 0, rules) == NumberKind(0)
    assert rewrite(sin(cos(x)) * 0, rules) == NumberKind(0)
    assert rewrite(sin(log(x)) * 0, rules) == sin(log(x)) * 0
    assert rewrite(log(x) * 0, rules, known=lambda condition: condition == Ne(x, 0)) == NumberKind(0)
    assert rewrite(tan(x) * 0, rules, known=lambda condition: condition == Ne(cos(x), 0)) == NumberKind(0)
    # A call of a lambda is not known to have a value.
    assert rewrite(Lambda(y, y)(x) * 0, rules) == Lambda(y, y)(x) * 0


def test_lambda_untouched():
    f = Lambda(x, x + 0)
    assert rewrite(f, rules) == f
    assert rewrite(f(y * 1), rules) == f(y)


def test_several_rules_in_sequence():
    e = (x * 1 + 0) ** 1 - (y + 0) * 0
    assert rewrite(e, rules) == x

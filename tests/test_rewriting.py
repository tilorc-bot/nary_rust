import pytest
import nary.logic_rules  # noqa: F401
from nary import Add, Eq, Gt, Lambda, Many, Mul, Ne, NumberKind, Pow, cos, exp, log, pi, re, sin, tan
from nary.logic import And, BoolKind, Not, Or, false, true
from nary.arithmetic_rules import rules
from nary.domains import declare_function
from nary.calculus import Integral, NumberFunction
from nary.rewriting import beta, has_a_value, holds, rewrite
from nary.rules import rule

x, y, z, a = NumberKind("x"), NumberKind("y"), NumberKind("z"), NumberKind("a")
b = NumberKind("b")
rest = Many(NumberKind)("rest")
f = NumberFunction("f")


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
    assert rewrite(sin(x) * 0, rules) == NumberKind(0)
    assert rewrite(sin(cos(x)) * 0, rules) == NumberKind(0)
    assert rewrite(sin(log(x)) * 0, rules) == sin(log(x)) * 0
    assert rewrite(log(x) * 0, rules, known=lambda condition: condition == Ne(x, 0)) == NumberKind(0)
    assert rewrite(tan(x) * 0, rules, known=lambda condition: condition == Ne(cos(x), 0)) == NumberKind(0)
    assert rewrite(Lambda(y, y)(x) * 0, rules) == Lambda(y, y)(x) * 0


def test_lambda_untouched():
    f = Lambda(x, x + 0)
    assert rewrite(f, rules) == f
    assert rewrite(f(y * 1), rules) == f(y)


def test_several_rules_in_sequence():
    e = (x * 1 + 0) ** 1 - (y + 0) * 0
    assert rewrite(e, rules) == x


def test_the_first_rule_that_applies_is_used():
    assert rewrite(sin(x), [rule(sin(a), 1), rule(sin(a), 2)]) == NumberKind(1)


def test_a_rule_that_changes_nothing_does_not_apply():
    assert rewrite(sin(x), [rule(sin(a), sin(a))]) == sin(x)


def test_nested_flat_arguments_are_merged_only_when_a_rule_applies():
    assert rewrite(Add(Add(x, y), x), rules) == Add(Mul(2, x), y)
    assert rewrite(Add(Add(x, y), z), rules) == Add(Add(x, y), z)


def test_known_must_return_true_itself():
    assert rewrite(x / x, rules, known=lambda condition: 1) == x / x


def test_zero_to_the_zero_has_no_value():
    assert rewrite(x ** 0, rules) == x ** 0
    assert rewrite(x ** 0, rules, known=lambda condition: condition == Ne(x, 0)) == NumberKind(1)


def test_erased_function_without_a_domain():
    assert rewrite(Integral(sin, 0, x) * 0, rules) == Integral(sin, 0, x) * 0


def test_erased_function_variable():
    erase = rule(f(0), 0)
    assert erase.erased == (f,)
    assert rewrite(sin(0), [erase]) == NumberKind(0)
    assert rewrite(Lambda(y, sin(y))(0), [erase]) == NumberKind(0)
    assert rewrite(Lambda(y, log(y))(0), [erase]) == Lambda(y, log(y))(0)


def test_a_conditional_rule_is_not_applied_inside_a_lambda():
    inside = Lambda(x, x / x)
    assert rewrite(inside, rules, known=lambda condition: condition == Ne(x, 0)) == inside


def test_known_is_asked_about_the_variable_of_a_lambda():
    asked = []
    rewrite(Lambda(y, log(y))(0), [rule(f(0), 0)], known=asked.append)
    assert asked[0] == Ne(y, 0)


def test_a_nested_pattern_is_not_flattened():
    assert rewrite(Add(Add(x, y), z), [rule(a + b + a, a)]) == Add(Add(x, y), z)
    cancel = rule(a * b / b, a, when=Ne(b, 0))
    assert rewrite(x * y / y, [cancel], known=lambda condition: True) == x * y / y


def test_a_numeric_condition_is_decided():
    pytest.importorskip("mpmath")
    assert rewrite(log(x) * 0, rules) == log(x) * 0
    assert rewrite(Pow(2, -1) * 0, rules) == NumberKind(0)


def test_the_next_way_of_matching_is_tried():
    assert rewrite(Mul(log(x), 0, 0), rules) == Mul(log(x), 0)


def test_an_erased_variable_is_checked_when_the_condition_holds():
    cancel = rule(Mul(a, b, Pow(b, -1)), a, when=Ne(b, 0))
    e = Mul(x, log(y), Pow(log(y), -1))
    assert rewrite(e, [cancel], known=lambda condition: condition == Ne(log(y), 0)) == e


def test_part_of_the_arguments_is_matched_only_at_the_top_of_a_pattern():
    assert rewrite(sin(Add(x, 0, y)), [rule(sin(a + 0), sin(a))]) == sin(Add(x, 0, y))


def test_the_result_of_a_partial_match_is_flattened():
    assert rewrite(Add(sin(x), cos(x), y), [rule(Add(sin(a), cos(a)), Add(a, 1))]) == Add(x, 1, y)


def test_a_run_variable_takes_the_arguments_that_are_left():
    period = rule(sin(Add(a, Mul(2, pi), rest)), sin(Add(a, rest)))
    assert rewrite(sin(Add(x, y, 2 * pi)), [period]) == sin(Add(x, y))
    assert rewrite(sin(Add(x, 2 * pi)), [period]) == sin(x)
    assert rewrite(cos(sin(Add(2 * pi, x))), [period]) == cos(sin(x))


def test_a_run_variable_in_an_ordered_argument_list():
    Seq = declare_function("Seq", Many(NumberKind)("items"), returns=NumberKind, domain=true)
    assert rewrite(Seq(0, 0, x, 0), [rule(Seq(0, rest), Seq(rest))]) == Seq(x, 0)
    assert rewrite(Seq(x, 0, y, 0), [rule(Seq(a, rest, 0), Seq(rest, a))]) == Seq(0, y, x)


def test_an_erased_run_variable_must_have_values():
    erase = rule(Mul(0, rest), 0)
    assert rewrite(sin(Mul(x, 0, y)), [erase]) == sin(0)
    assert rewrite(sin(Mul(x, 0, log(y))), [erase]) == sin(Mul(x, 0, log(y)))


def test_a_run_variable_in_a_condition():
    cancel = rule(Mul(Pow(Add(rest), -1), Add(rest)), 1, when=Ne(Add(rest), 0))
    e = Mul(Pow(x + y, -1), x + y)
    assert rewrite(e, [cancel]) == e
    assert rewrite(e, [cancel], known=lambda c: c == Ne(x + y, 0)) == NumberKind(1)


def test_normal_is_applied_before_the_rules():
    seen = []
    normal = lambda e, known: seen.append(e) or (x if e == Add(x, 0) else e)
    assert rewrite(sin(Add(x, 0)), [rule(sin(a), cos(a))], normal=normal) == cos(x)
    assert Add(x, 0) in seen


def test_holds():
    assert holds(true) and not holds(Ne(x, 0))
    assert holds(Ne(x, 0), lambda c: c == Gt(x, 0))
    assert holds(Ne(0, x), lambda c: c == Ne(x, 0))
    assert holds(Eq(re(x), x), lambda c: c == Gt(x, 0))
    assert holds(Or(Ne(x, 0), false), lambda c: c == Ne(x, 0))
    assert not holds(And(Ne(x, 0), false), lambda c: c == Ne(x, 0))


def test_a_condition_is_rewritten_with_the_rules():
    rules_ = [rule(Ne(exp(a), 0), true), rule(Mul(a, Pow(a, -1)), 1, when=Ne(a, 0))]
    assert rewrite(exp(x) / exp(x), rules_) == NumberKind(1)


def test_has_a_value():
    assert has_a_value(sin(x)) and not has_a_value(log(x))
    assert has_a_value(log(x), lambda c: c == Gt(x, 0))


def test_beta():
    assert beta(Lambda(y, sin(y) + y)(x)) == sin(x) + x
    inner = Lambda(y, Lambda(x, x + y))(x)
    assert beta(inner) == inner


def test_a_flat_pattern_matches_through_the_identity():
    half_turn = rule(sin(Mul(pi, rest)), cos(Mul(2, rest)))
    assert rewrite(sin(pi), [half_turn]) == cos(2)
    assert rewrite(sin(x), [rule(sin(Add(a, b, z)), cos(a))]) == sin(x)
    assert rewrite(sin(pi), [rule(sin(Mul(b, pi, rest)), cos(b))]) == sin(pi)


def test_through_the_identity_a_run_variable_gets_no_original_argument():
    assert rewrite(sin(x), [rule(sin(Add(b, rest)), cos(Mul(b, Add(rest, 2))))]) == cos(Mul(x, 2))
    assert rewrite(sin(x), [rule(sin(Add(rest)), cos(Add(rest)))]) == sin(x)
    assert rewrite(sin(Add(x, y)), [rule(sin(Add(rest)), cos(Add(rest)))]) == cos(Add(x, y))


def test_a_replacement_is_flattened():
    assert rewrite(sin(x), [rule(sin(a), Add(a, Add(a, Add(a, 1))))]) == Add(x, x, x, 1)
    p, q, r = BoolKind("p"), BoolKind("q"), BoolKind("r")
    assert rewrite(Not(And(p, q, r)), nary.logic_rules.to_nnf) == Or(Not(p), Not(q), Not(r))


def test_a_cycle_stops():
    flip = rule(sin(a), sin(Mul(-1, a)))
    unflip = rule(sin(Mul(-1, a)), sin(a))
    assert rewrite(sin(x), [unflip, flip]) in (sin(x), sin(Mul(-1, x)))

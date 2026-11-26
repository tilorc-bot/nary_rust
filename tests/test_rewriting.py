from nary import Add, Lambda, Mul, Ne, NumberKind, Pow, cos, log, sin, tan
from nary.arithmetic_rules import rules
from nary.calculus import Integral, NumberFunction
from nary.rewriting import rewrite
from nary.rules import rule

x, y, z, a = NumberKind("x"), NumberKind("y"), NumberKind("z"), NumberKind("a")
b = NumberKind("b")
f = NumberFunction("f")
add_self = rules + [rule(a + a, 2 * a, name="add_self")]


def test_unordered_and_flat_matching():
    assert rewrite(Add(0, x), rules) == x
    assert rewrite(Add(x, 0, y), rules) == Add(x, y)
    assert rewrite(Add(x, y, x), add_self) == Add(Mul(2, x), y)


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
    assert rewrite(Add(Add(x, y), x), add_self) == Add(Mul(2, x), y)
    assert rewrite(Add(Add(x, y), z), add_self) == Add(Add(x, y), z)


def test_known_must_return_true_itself():
    assert rewrite(x / x, rules, known=lambda condition: 1) == x / x


def test_zero_to_the_zero_has_no_value():
    pow_zero = [rule(a ** 0, 1, when=Ne(a, 0))]
    assert rewrite(x ** 0, pow_zero) == x ** 0
    assert rewrite(x ** 0, pow_zero, known=lambda condition: condition == Ne(x, 0)) == NumberKind(1)


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
    assert asked == [Ne(y, 0)]


def test_a_nested_pattern_is_not_flattened():
    assert rewrite(Add(Add(x, y), x), [rule(a + b + a, a)]) == Add(Add(x, y), x)
    cancel = rule(a * b / b, a, when=Ne(b, 0))
    assert rewrite(x * y / y, [cancel], known=lambda condition: True) == x * y / y


def test_a_condition_is_not_evaluated():
    assert rewrite(Pow(2, -1) * 0, rules) == Pow(2, -1) * 0


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

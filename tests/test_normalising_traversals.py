import random

import pytest

from nary import Add, BoolKind, Lt, Mul, NumberKind, Pow, log, sin
from nary.logic import And, Not, Or, false, true
from nary.normalising import _normalise_with, normalise
from nary.traversal import bottom_up

x, y, z = (NumberKind(name) for name in "xyz")
p, q = BoolKind("p"), BoolKind("q")
n = NumberKind


def flattening_associative_heads_first(at_node):
    return bottom_up(at_node, flat=lambda head: head.is_associative)


def normalise_flattening_first(e, known=None):
    return _normalise_with(flattening_associative_heads_first, e, known)


def test_both_traversals_remove_an_identity_element_inside_brackets():
    e = (y + 0) + x
    assert normalise(e) == normalise_flattening_first(e) == Add(x, y)


def test_both_traversals_merge_the_brackets_of_one_associative_head():
    e = Add(Add(x, y), Add(y, z))
    assert normalise(e) == normalise_flattening_first(e) == Add(x, y, y, z)


def test_both_traversals_merge_brackets_three_deep():
    e = Mul(x, Mul(y, Mul(z, Mul(x, 1))))
    assert normalise(e) == normalise_flattening_first(e) == Mul(x, x, y, z)


def test_both_traversals_erase_the_arguments_beside_an_absorbing_element_when_all_have_a_value():
    e = Mul(Mul(sin(x), 0), y)
    assert normalise(e) == normalise_flattening_first(e) == n(0)


def test_both_traversals_keep_an_argument_without_a_value_beside_an_absorbing_element():
    e = Mul(log(x), 0)
    assert normalise(e) == normalise_flattening_first(e) == Mul(0, log(x))


def test_both_traversals_evaluate_brackets_that_hold_only_number_literals():
    e = Add(Add(1, 2), Mul(2, 3))
    assert normalise(e) == normalise_flattening_first(e) == n(9)


def test_both_traversals_normalise_a_boolean_expression():
    e = And(q, Or(p, false), And(q, true))
    assert normalise(e) == normalise_flattening_first(e) == And(p, q)


def test_both_traversals_use_what_is_known():
    e = Mul(Mul(log(x), 0), y)
    known = lambda condition: True
    assert normalise(e, known) == normalise_flattening_first(e, known) == n(0)


def generated(rng, depth):
    if depth == 0 or rng.random() < 0.4:
        return rng.choice([x, y, z, n(0), n(1), n(-1), n(2), log(x)])
    head = rng.choice([Add, Add, Mul, Mul, Pow, sin])
    arity = {Pow: 2, sin: 1}.get(head) or rng.randint(0, 4)
    return head(*(generated(rng, depth - 1) for _ in range(arity)))


def generated_boolean(rng, depth):
    if depth == 0 or rng.random() < 0.3:
        return rng.choice([p, q, true, false, Lt(generated(rng, 2), generated(rng, 2))])
    head = rng.choice([And, Or, Not])
    arity = 1 if head == Not else rng.randint(0, 3)
    return head(*(generated_boolean(rng, depth - 1) for _ in range(arity)))


@pytest.mark.xfail(strict=True, reason=(
    "test_number_literals_inside_brackets_are_combined_only_when_every_node_is_handled and "
    "test_an_absorbing_element_inside_brackets_erases_more_when_every_node_is_handled fail"
))
def test_both_traversals_give_the_same_result_for_generated_expressions():
    rng = random.Random(20261128)
    for generate in [generated, generated_boolean] * 1000:
        e = generate(rng, 4)
        assert normalise(e) == normalise_flattening_first(e)


def test_number_literals_inside_brackets_are_combined():
    assert normalise(Mul(Mul(-1, 2), x)) == Mul(-2, x)


def test_number_literals_are_not_combined_once_flattening_has_put_a_symbol_beside_them():
    assert normalise_flattening_first(Mul(Mul(-1, 2), x)) == Mul(-1, 2, x)


@pytest.mark.xfail(strict=True, reason=(
    "normalise evaluates a node only if every argument is a literal: Mul(-1, 2) is one, "
    "Mul(-1, 2, x) is not"
))
def test_number_literals_inside_brackets_are_combined_only_when_every_node_is_handled():
    e = Mul(Mul(-1, 2), x)
    assert normalise(e) == normalise_flattening_first(e)


def test_an_absorbing_element_erases_the_arguments_inside_its_own_brackets():
    assert normalise(Mul(Mul(x, 0), log(y))) == Mul(0, log(y))


def test_an_absorbing_element_erases_nothing_once_flattening_has_put_an_argument_without_a_value_beside_it():
    assert normalise_flattening_first(Mul(Mul(x, 0), log(y))) == Mul(0, log(y), x)


@pytest.mark.xfail(strict=True, reason=(
    "an absorbing element erases all the other arguments or none: Mul(x, 0) is 0, "
    "Mul(x, 0, log(y)) keeps x because log(y) may have no value"
))
def test_an_absorbing_element_inside_brackets_erases_more_when_every_node_is_handled():
    e = Mul(Mul(x, 0), log(y))
    assert normalise(e) == normalise_flattening_first(e)

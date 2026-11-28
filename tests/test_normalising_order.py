from itertools import combinations, permutations, product

import pytest

from nary import (
    Add, BoolKind, Lambda, Many, Mul, Ne, NumberKind, Pow, declare_constant, declare_function,
    log, sin,
)
from nary.property_steps import step
from nary.calculus import NumberFunction
from nary.logic import And, Or, false, true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property

x, y, z = (NumberKind(name) for name in "xyz")
p, q, r = (BoolKind(name) for name in "pqr")
n = NumberKind


def head(name):
    return declare_function(name, Many(NumberKind), returns=NumberKind, domain=true)


Bag = head("OrderBag")
declare_properties(
    Bag, is_associative=True, is_commutative=True, identity_element=0, absorbing_element=9,
    is_idempotent=True,
)
Seq = head("OrderSeq")
declare_properties(
    Seq, is_associative=True, identity_element=0, absorbing_element=9, is_idempotent=True,
)
Pair = declare_function("OrderPair", NumberKind, NumberKind, returns=NumberKind, domain=true)
declare_properties(
    Pair, is_commutative=True, identity_element=0, absorbing_element=1, is_idempotent=True,
)
Plain = head("OrderPlain")
Inert = head("OrderInert")
declare_properties(Inert, identity_element=0, absorbing_element=9, is_idempotent=True)
inv = declare_function("order_inv", NumberKind, returns=NumberKind, domain=true)

declare_property("order_period")
declare_property("order_cancel_neighbours")
declare_property("order_cancel_anywhere")
declare_property("order_unwrap")


@step("order_period", per_argument=True)
def _period(arg, copies, k):
    return copies % k


def _cancels(a, b, neg):
    return b == neg(a) or a == neg(b)


@step("order_cancel_neighbours")
def _cancel_one_neighbouring_pair(head, args, neg):
    for i in range(len(args) - 1):
        if _cancels(args[i], args[i + 1], neg):
            return args[:i] + args[i + 2:]
    return args


@step("order_cancel_anywhere", commutative_only=True)
def _cancel_one_pair_anywhere(head, args, neg):
    for i, j in combinations(range(len(args)), 2):
        if _cancels(args[i], args[j], neg):
            return [a for k, a in enumerate(args) if k not in (i, j)]
    return args


@step("order_unwrap")
def _unwrap(head, args, wrapper):
    return [a.args[0] if not a.is_atom and a.head == wrapper else a for a in args]


Free = head("OrderFree")
declare_properties(Free, is_associative=True, identity_element=0, order_cancel_neighbours=inv)
Abel = head("OrderAbel")
declare_properties(
    Abel, is_associative=True, is_commutative=True, identity_element=0, order_cancel_anywhere=inv,
)
Tri = head("OrderTri")
declare_properties(Tri, is_associative=True, is_commutative=True, order_period=3)
Twice = head("OrderTwice")
declare_properties(Twice, is_associative=True, identity_element=0, order_period=2)
wrap = declare_function("order_wrap", NumberKind, returns=NumberKind, domain=true)
Unwrap = head("OrderUnwrap")
declare_properties(
    Unwrap, is_associative=True, is_commutative=True, is_idempotent=True, order_unwrap=wrap,
)


def compositions(args):
    for cuts in product([False, True], repeat=len(args) - 1):
        parts, start = [], 0
        for i, cut in enumerate(cuts, 1):
            if cut:
                parts.append(args[start:i])
                start = i
        yield parts + [args[start:]]


def bracketings(f, args):
    if len(args) == 1:
        yield args[0]
        return
    for parts in compositions(args):
        if len(parts) > 1 or len(args) == len(parts[0]) == 1:
            for choice in product(*(_part(f, part) for part in parts)):
                yield f(*choice)


def _part(f, part):
    if len(part) == 1:
        return [part[0]]
    return list(bracketings(f, part))


def every_writing(f, args):
    for order in permutations(args):
        yield f(*order)
        if f.is_associative:
            yield from bracketings(f, list(order))


def normal_forms(es, known=None):
    return {normalise(e, known) for e in es}


def shape(e):
    if isinstance(e, int):
        return repr(e)
    if e.is_atom:
        return repr(e)
    args = [shape(arg) for arg in e.args]
    if getattr(e.head, "is_commutative", False):
        args.sort()
    return f"{shape(e.head)}({', '.join(args)})"


def normalises_to(e, expected, known=None):
    return shape(normalise(e, known)) == shape(expected)


def test_shape_ignores_only_the_order_of_commutative_arguments():
    assert shape(Add(y, Seq(x, z))) == shape(Add(Seq(x, z), y))
    assert shape(Seq(y, Add(x, z))) == shape(Seq(y, Add(z, x)))
    assert shape(Seq(y, x)) != shape(Seq(x, y))
    assert shape(Add(x, x, y)) != shape(Add(x, y, y))


def test_bracketings_of_four_arguments():
    assert len(set(bracketings(Seq, [x, y, z, n(2)]))) == 11


@pytest.mark.parametrize("f, args, expected", [
    (Add, [x, y, x, n(0)], Add(x, x, y)),
    (Mul, [sin(x), n(0), y, n(1)], n(0)),
    (Mul, [Add(y, x), x, Add(x, y)], Mul(x, Add(x, y), Add(x, y))),
    (And, [p, q, true, Or(q, p)], And(p, q, Or(p, q))),
    (And, [p, q, p, false], false),
    (Or, [p, And(q, r), And(r, q), false], Or(p, And(q, r))),
    (Bag, [x, n(9), sin(x), n(0)], n(9)),
    (Bag, [x, y, x, n(0)], Bag(x, y)),
    (Abel, [x, y, inv(x), inv(y)], n(0)),
    (Abel, [x, inv(y), x, inv(x)], Abel(x, inv(y))),
    (Tri, [x, y, x, x], y),
    (Tri, [x, y, x, y], Tri(x, x, y, y)),
])
def test_every_order_and_bracketing_of_a_multiset_has_one_normal_form(f, args, expected):
    forms = normal_forms(every_writing(f, args))
    assert len(forms) == 1
    assert normalises_to(forms.pop(), expected)


@pytest.mark.parametrize("e, expected", [
    (And(Or(p, q), Or(q, p)), Or(p, q)),
    (And(Or(p, Or(q, r)), Or(Or(r, p), q)), Or(p, q, r)),
    (Or(And(p, Or(q, r)), And(Or(r, q), p)), And(p, Or(q, r))),
    (Bag(Mul(y, x), Mul(x, y, 1)), Mul(x, y)),
    (Bag(Seq(x, y), Seq(x, Seq(y, 0))), Seq(x, y)),
    (Pair(Add(x, y), Add(y, x)), Add(x, y)),
    (Pair(Pair(y, x), Pair(x, y)), Pair(x, y)),
    (Seq(Add(y, x), Add(x, y)), Add(x, y)),
    (Seq(Add(y, x), Add(x, y), z), Seq(Add(x, y), z)),
])
def test_arguments_equal_after_their_own_normalising_combine(e, expected):
    assert normalises_to(e, expected)


def test_arguments_equal_after_normalising_still_count_without_idempotence():
    assert normalise(Mul(Add(x, y), Add(y, x))) == normalise(Mul(Add(x, y), Add(x, y)))
    assert normalises_to(Mul(Add(x, y), Add(y, x)), Mul(Add(x, y), Add(x, y)))


@pytest.mark.parametrize("i", range(3))
def test_an_identity_or_absorbing_element_in_any_position(i):
    def put(element, args):
        return args[:i] + [element] + args[i:]

    assert normalise(Seq(*put(n(0), [x, y]))) == Seq(x, y)
    assert normalise(Seq(*put(n(9), [x, y]))) == n(9)
    assert normalise(Seq(*put(Seq(0, 0), [x, y]))) == Seq(x, y)
    assert normalise(Seq(*put(n(9), [x, log(y)]))) == Seq(*put(n(9), [x, log(y)]))
    assert normalises_to(Bag(*put(n(0), [x, y])), Bag(x, y))
    assert normalise(Mul(*put(n(0), [sin(x), y]))) == n(0)
    assert normalises_to(Mul(*put(n(0), [log(x), y])), Mul(0, y, log(x)))
    assert normalises_to(Mul(*put(n(1), [x, y])), Mul(x, y))
    assert normalise(And(*put(false, [p, q]))) == false
    assert normalises_to(Or(*put(false, [p, q])), Or(p, q))


def test_identity_and_absorbing_elements_of_a_pair_in_either_position():
    assert normalise(Pair(0, x)) == normalise(Pair(x, 0)) == x
    assert normalise(Pair(1, x)) == normalise(Pair(x, 1)) == n(1)
    assert normalise(Pair(1, log(x))) == normalise(Pair(log(x), 1))
    assert normalises_to(Pair(1, log(x)), Pair(1, log(x)))


@pytest.mark.parametrize("e, expected", [
    (Seq(x, y), Seq(x, y)),
    (Seq(y, x), Seq(y, x)),
    (Seq(x, y, x), Seq(x, y, x)),
    (Seq(x, y, x, y), Seq(x, y, x, y)),
    (Seq(x, 0, y, 0, x), Seq(x, y, x)),
    (Seq(Seq(x, y), x), Seq(x, y, x)),
    (Seq(x, Seq(y, x)), Seq(x, y, x)),
    (Seq(x, Seq(y, 0, y), x), Seq(x, y, x)),
    (Seq(x, Seq(0, x)), x),
    (Seq(x, Seq(y, x), Seq(x, y)), Seq(x, y, x, y)),
    (Seq(x, y, Seq(9)), n(9)),
    (Seq(Bag(y, x), Bag(x, y), z), Seq(Bag(x, y), z)),
    (Seq(Pow(x, y), Pow(y, x)), Seq(Pow(x, y), Pow(y, x))),
])
def test_a_sequence_keeps_its_order_and_merges_only_neighbours(e, expected):
    assert normalises_to(e, expected)


def test_a_sequence_of_distinct_arguments_differs_in_every_order():
    forms = normal_forms(Seq(*order) for order in permutations([x, y, z, sin(x)]))
    assert len(forms) == 24


def test_a_multiset_inside_a_sequence_and_a_sequence_inside_a_multiset():
    assert normalise(Seq(Add(y, x), z)) == normalise(Seq(Add(x, y), z))
    assert normalise(Seq(Add(y, x), z)) != normalise(Seq(z, Add(x, y)))
    assert normalise(Add(Seq(x, y), z)) == normalise(Add(z, Seq(x, y)))
    assert normalise(Add(Seq(x, y), z)) != normalise(Add(Seq(y, x), z))
    assert normalises_to(Bag(Seq(y, x), Seq(x, y)), Bag(Seq(y, x), Seq(x, y)))


@pytest.mark.parametrize("e", [
    Pair(x, y),
    Pair(x, Pair(y, z)),
    Pair(Pair(x, y), z),
    Pair(x, Pair(x, y)),
    Pair(Add(x, y), Add(y, x, 1)),
])
def test_a_pair_that_does_not_collapse_keeps_both_arguments(e):
    normal = normalise(e)
    assert normal.head == Pair
    assert set(normal.args) == {normalise(a) for a in e.args}


def test_a_pair_is_not_associative():
    assert normalise(Pair(x, Pair(y, z))) != normalise(Pair(Pair(x, y), z))
    assert normalise(Pair(Pair(y, x), z)) == normalise(Pair(z, Pair(x, y)))


def test_a_head_with_nothing_declared_keeps_its_arguments_in_place():
    assert normalise(Plain(y, Add(y, x), 0)) == Plain(y, normalise(Add(x, y)), 0)
    assert normalise(Plain(x, Plain(y))) == Plain(x, Plain(y))
    assert normalise(Plain()) == Plain()


def test_a_head_neither_associative_nor_commutative_uses_its_properties_only_on_two_arguments():
    assert normalise(Inert(x, 0)) == x and normalise(Inert(0, x)) == x
    assert normalise(Inert(x, x)) == x
    assert normalise(Inert(9, x)) == n(9) and normalise(Inert(x, 9)) == n(9)
    for e in [Inert(9, log(x)), Inert(y, x), Inert(x), Inert(x, 0, y), Inert(x, x, x), Inert(Inert(x, y), z)]:
        assert normalise(e) == e


def test_a_head_that_is_not_a_declared_function():
    f = NumberFunction("order_f")
    assert normalise(f(Add(y, x))) == normalise(f(Add(x, y)))
    assert normalise(f(y) + f(x)) == normalise(f(x) + f(y))
    swap = Lambda((x, y), x)
    assert normalise(swap(Add(y, x, 0), z)) == swap(normalise(Add(x, y)), z)
    assert normalise(swap(Add(y, x, 0), z)) != normalise(swap(z, Add(x, y)))


def test_known_conditions_in_any_order():
    both = lambda c: c in (Ne(x, 0), Ne(y, 0))
    only_x = lambda c: c == Ne(x, 0)
    orders = [Mul(*order) for order in permutations([log(x), n(0), log(y), z])]
    assert normal_forms(orders, only_x) == {normalise(Mul(0, z, log(x), log(y)))}
    assert normal_forms(orders, both) == {n(0)}
    assert normal_forms(every_writing(Mul, [log(x), n(0), log(y)]), both) == {n(0)}


def test_known_sees_conditions_whose_commutative_arguments_are_normalised():
    nonzero_sum = lambda c: c == normalise(Ne(x + y, 0))
    for e in [Mul(log(Add(y, x)), 0), Mul(0, log(Add(x, y, 0)))]:
        assert normalise(e, nonzero_sum) == n(0)


@pytest.mark.parametrize("e, expected", [
    (Free(x, inv(x), y), y),
    (Free(y, x, inv(x)), y),
    (Free(x, y, inv(x)), Free(x, y, inv(x))),
    (Free(x, y, inv(y), inv(x)), 0),
    (Free(x, Free(y, inv(y)), inv(x)), 0),
    (Free(x, Free(inv(x), y)), y),
    (Free(inv(y), x, 0, inv(x), y), 0),
    (Free(x, inv(y), y, inv(x), z), z),
])
def test_a_step_that_cancels_neighbours_on_a_sequence(e, expected):
    assert normalises_to(e, expected)


def test_a_multiset_step_sees_every_argument_whatever_the_order():
    forms = normal_forms(every_writing(Abel, [x, z, y, inv(x)]))
    assert forms == {normalise(Abel(y, z))}
    assert normalise(Abel(x, Abel(y, inv(x)))) == y


@pytest.mark.parametrize("e, expected", [
    (Twice(x, y, x), Twice(x, y, x)),
    (Twice(x, x, y), y),
    (Twice(y, x, Twice(x, z)), Twice(y, z)),
    (Twice(x, 0, x), 0),
    (Twice(x, y, y, x), 0),
])
def test_a_per_argument_step_on_a_sequence_counts_only_neighbours(e, expected):
    assert normalises_to(e, expected)


def test_a_per_argument_step_on_a_multiset_counts_across_brackets():
    assert normal_forms(every_writing(Tri, [x, x, y, x])) == {y}
    assert normalise(Tri(x, Tri(x, Tri(x, y)))) == y


@pytest.mark.parametrize("bracketed, flat", [
    (Mul(log(x), Mul(0, y)), Mul(log(x), 0, y)),
    (Mul(log(y), Mul(0, log(z))), Mul(log(y), 0, log(z))),
    (Seq(Seq(x, 9), log(x)), Seq(x, 9, log(x))),
    (Bag(log(x), Bag(x, 9)), Bag(log(x), x, 9)),
])
@pytest.mark.xfail(strict=True, reason=(
    "the absorbing element erases the arguments inside its own brackets, "
    "and all or none of the arguments once the brackets are gone"
))
def test_an_absorbing_element_beside_an_argument_without_a_value_ignores_brackets(bracketed, flat):
    known = lambda c: c == Ne(z, 0)
    assert normalise(bracketed, known) == normalise(flat, known)


def test_a_step_that_adds_an_argument_with_the_associative_head_of_the_node_is_an_error():
    with pytest.raises(ValueError, match="_unwrap put OrderUnwrap\\(y, z\\) among the arguments"):
        normalise(Unwrap(x, wrap(Unwrap(y, z))))


def test_a_step_that_keeps_the_number_of_arguments():
    once = normalise(Unwrap(x, wrap(x)))
    assert normalise(once) == once


@pytest.mark.xfail(
    strict=True, reason="two constants with the same name tie in the order of a commutative head",
)
def test_two_constants_with_one_name_in_either_order():
    k1, k2 = declare_constant("order_k", NumberKind), declare_constant("order_k", NumberKind)
    assert normalise(k1 + k2) == normalise(k2 + k1)


def test_a_per_argument_step_erases_only_arguments_with_a_value_whatever_the_order():
    writings = list(every_writing(Tri, [log(x), y, log(x), log(x)]))
    assert {shape(e) for e in normal_forms(writings)} == {shape(Tri(y, log(x), log(x), log(x)))}
    assert normal_forms(writings, lambda c: c == Ne(x, 0)) == {y}
    assert normalises_to(Twice(log(x), Twice(log(x), y)), Twice(log(x), log(x), y))
    assert normalises_to(Twice(log(x), Twice(log(x), y)), y, lambda c: c == Ne(x, 0))

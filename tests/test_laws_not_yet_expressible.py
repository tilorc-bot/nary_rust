from collections import Counter

import pytest

from nary import (
    BoolKind, Many, Ne, NumberKind, declare_constant, declare_function, declare_kind,
)
from nary.arithmetic import Add, Mul
from nary.property_steps import step
from nary.logic import true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property

x, y, z = (NumberKind(name) for name in "xyz")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a one-argument head")
def test_an_involution_undoes_itself():
    Polarity = declare_kind("Polarity")
    Invert = declare_function("Invert", Polarity, returns=Polarity, domain=true)
    declare_property("is_involution")

    @step("is_involution")
    def undo_twice(head, args):
        (arg,) = args
        return list(arg.args) if not arg.is_atom and arg.head == head else args

    declare_properties(Invert, is_involution=True)
    p = Polarity("p")

    assert normalise(Invert(Invert(p))) == p


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a one-argument head")
def test_a_function_applied_twice_is_applied_once():
    Magnitude = declare_function("Magnitude", NumberKind, returns=NumberKind, domain=true)
    declare_property("is_projection")

    @step("is_projection")
    def apply_once(head, args):
        (arg,) = args
        return [arg] if not arg.is_atom and arg.head == head else args

    declare_properties(Magnitude, is_projection=True)

    assert normalise(Magnitude(Magnitude(x))) == Magnitude(x)


def test_an_odd_function_takes_the_negation_outside():
    flip = declare_function("flip", NumberKind, returns=NumberKind, domain=true)
    Odd = declare_function("Odd", NumberKind, returns=NumberKind, domain=true)
    declare_property("odd_under")

    @step("odd_under")
    def take_negation_outside(head, args, negation):
        (arg,) = args
        if not arg.is_atom and arg.head == negation:
            return negation(head(*arg.args))
        return args

    declare_properties(Odd, odd_under=flip)

    assert normalise(Odd(flip(x))) == flip(Odd(x))


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a one-argument head")
def test_a_function_has_a_known_value_at_a_special_argument():
    Wave = declare_kind("Wave")
    flat = declare_constant("flat", Wave)
    Damp = declare_function("Damp", Wave, returns=Wave, domain=true)
    declare_property("fixed_point")

    @step("fixed_point")
    def keep_the_fixed_point(head, args, fixed):
        return [fixed] if args == [fixed] else args

    declare_properties(Damp, fixed_point=flat)

    assert normalise(Damp(flat)) == flat
    assert normalise(Damp(Wave("w"))) == Damp(Wave("w"))


@pytest.mark.xfail(strict=True, raises=TypeError, reason="an element is bound by applying the head to two arguments")
def test_an_element_property_on_a_one_argument_head():
    Signal = declare_kind("Signal")
    quiet = declare_constant("quiet", Signal)
    Filter = declare_function("Filter", Signal, returns=Signal, domain=true)
    declare_property("rest_element", element=True)

    declare_properties(Filter, rest_element=quiet)

    assert Filter.rest_element == quiet


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a head with three fixed arguments")
def test_a_choice_between_equal_branches_is_that_branch():
    Pick = declare_function("Pick", BoolKind, NumberKind, NumberKind, returns=NumberKind, domain=true)
    declare_property("is_choice")

    @step("is_choice")
    def same_branches(head, args):
        condition, then, otherwise = args
        return [then] if then == otherwise else args

    declare_properties(Pick, is_choice=True)

    assert normalise(Pick(BoolKind("c"), x, x)) == x


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps cannot ask whether a condition holds")
def test_a_step_that_needs_a_condition_beyond_the_values_of_what_it_erases():
    one = NumberKind(1)
    declare_property("is_self_cancelling_ratio")

    @step("is_self_cancelling_ratio")
    def cancel(head, args):
        return [one] if len(args) == 2 and args[0] == args[1] else args

    Over = declare_function("Over", NumberKind, NumberKind, returns=NumberKind, domain=true)
    declare_properties(Over, is_self_cancelling_ratio=True)

    assert normalise(Over(x, x), lambda c: c == Ne(x, 0)) == one
    assert normalise(Over(x, x)) == Over(x, x)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="a whole-list step erases all or nothing")
def test_pairs_with_values_cancel_beside_a_pair_that_may_have_none():
    Turn = declare_kind("Turn")
    t = Turn("t")
    undo = declare_function("undo", Turn, returns=Turn, domain=true)
    Halvable = declare_function("Halvable", Turn, returns=BoolKind, domain=true)
    Halve = declare_function("Halve", t, returns=Turn, domain=Halvable(t))
    declare_property("cancelled_by")

    @step("cancelled_by", commutative_only=True)
    def cancel_opposites(head, args, opposite):
        counts = Counter(args)
        for e in list(counts):
            if not e.is_atom and e.head == opposite:
                pairs = min(counts[e], counts[e.args[0]])
                counts[e] -= pairs
                counts[e.args[0]] -= pairs
        return list(counts.elements())

    Turns = declare_function("Turns", Many(Turn), returns=Turn, domain=true)
    declare_properties(Turns, is_associative=True, is_commutative=True, cancelled_by=undo)
    a = Turn("a")

    assert Counter(normalise(Turns(a, undo(a), Halve(a), undo(Halve(a)))).args) == Counter(
        [Halve(a), undo(Halve(a))]
    )


def test_without_a_step_a_ratio_of_equal_arguments_stays():
    Ratio = declare_function("Ratio", NumberKind, NumberKind, returns=NumberKind, domain=true)

    assert normalise(Ratio(x, x)) == Ratio(x, x)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="nothing decides an order between arguments")
def test_a_maximum_drops_an_argument_another_one_dominates():
    declare_property("is_maximum")

    @step("is_maximum", commutative_only=True)
    def drop_dominated(head, args):
        return [
            a for a in args if not any(normalise(a < b) == true for b in args if b is not a)
        ]

    Top = declare_function("Top", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Top, is_associative=True, is_commutative=True, is_idempotent=True, is_maximum=True,
    )

    assert normalise(Top(x, x + 1)) == normalise(x + 1)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="no law relates two different heads without a hand-written match")
def test_lattice_absorption():
    Hierarchy = declare_kind("Hierarchy")
    Lower = declare_function("Lower", Many(Hierarchy), returns=Hierarchy, domain=true)
    Upper = declare_function("Upper", Many(Hierarchy), returns=Hierarchy, domain=true)
    for head in (Lower, Upper):
        declare_properties(head, is_associative=True, is_commutative=True, is_idempotent=True)
    p, q = Hierarchy("p"), Hierarchy("q")

    assert normalise(Lower(p, Upper(p, q))) == p


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="no law relates two different heads without a hand-written match")
def test_de_morgan():
    Grade = declare_kind("Grade")
    Both = declare_function("Both", Many(Grade), returns=Grade, domain=true)
    Either = declare_function("Either", Many(Grade), returns=Grade, domain=true)
    Compl = declare_function("Compl", Grade, returns=Grade, domain=true)
    for head in (Both, Either):
        declare_properties(head, is_associative=True, is_commutative=True)
    p, q = Grade("p"), Grade("q")

    assert normalise(Compl(Both(p, q))) == normalise(Either(Compl(p), Compl(q)))


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="normalise collects and never expands; expand does")
def test_distribution():
    assert normalise(x * (y + z)) == normalise(x * y + x * z)


def test_a_positional_law_on_a_two_argument_head():
    Track = declare_kind("Track")
    silence = declare_constant("silence", Track)
    declare_property("right_unit_element", element=True)

    @step("right_unit_element")
    def drop_on_the_right(head, args, unit):
        return [args[0]] if len(args) == 2 and args[1] == unit else args

    Then = declare_function("Then", Track, Track, returns=Track, domain=true)
    declare_properties(Then, right_unit_element=silence)
    a = Track("a")

    assert normalise(Then(a, silence)) == a
    assert normalise(Then(silence, a)) == Then(silence, a)


def test_a_two_argument_head_rewritten_to_another_head_by_returning_one_argument():
    Above = declare_function("Above", NumberKind, NumberKind, returns=BoolKind, domain=true)
    Below = declare_function("Below", NumberKind, NumberKind, returns=BoolKind, domain=true)
    declare_property("mirrored_by")

    @step("mirrored_by")
    def mirror(head, args, other):
        return [other(*reversed(args))] if len(args) == 2 else args

    declare_properties(Above, mirrored_by=Below)

    assert normalise(Above(x, y)) == Below(y, x)

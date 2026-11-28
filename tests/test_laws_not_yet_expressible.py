from collections import Counter

import pytest

from nary import (
    BoolKind, Many, Ne, NumberKind, declare_constant, declare_function, declare_kind,
)
from nary.arithmetic import Add, Mul
from nary.argument_collections import collection_step
from nary.logic import true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property

x, y, z = (NumberKind(name) for name in "xyz")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a one-argument head")
def test_an_involution_undoes_itself():
    Polarity = declare_kind("Polarity")
    Invert = declare_function("Invert", Polarity, returns=Polarity, domain=true)
    declare_property("is_involution")

    @collection_step("is_involution")
    def undo_twice(head, args, has_a_value):
        (arg,) = args
        return list(arg.args) if not arg.is_atom and arg.head == head else args

    declare_properties(Invert, is_involution=True)
    p = Polarity("p")

    assert normalise(Invert(Invert(p))) == p


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a one-argument head")
def test_a_function_applied_twice_is_applied_once():
    Magnitude = declare_function("Magnitude", NumberKind, returns=NumberKind, domain=true)
    declare_property("is_projection")

    @collection_step("is_projection")
    def apply_once(head, args, has_a_value):
        (arg,) = args
        return [arg] if not arg.is_atom and arg.head == head else args

    declare_properties(Magnitude, is_projection=True)

    assert normalise(Magnitude(Magnitude(x))) == Magnitude(x)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a one-argument head")
def test_an_odd_function_takes_the_negation_outside():
    flip = declare_function("flip", NumberKind, returns=NumberKind, domain=true)
    Odd = declare_function("Odd", NumberKind, returns=NumberKind, domain=true)
    declare_property("odd_under")

    @collection_step("odd_under")
    def take_negation_outside(head, args, has_a_value, negation):
        (arg,) = args
        if not arg.is_atom and arg.head == negation:
            return [negation(head(*arg.args))]
        return args

    declare_properties(Odd, odd_under=flip)

    assert normalise(Odd(flip(x))) == flip(Odd(x))


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="steps never run on a one-argument head")
def test_a_function_has_a_known_value_at_a_special_argument():
    Wave = declare_kind("Wave")
    flat = declare_constant("flat", Wave)
    Damp = declare_function("Damp", Wave, returns=Wave, domain=true)
    declare_property("fixed_point")

    @collection_step("fixed_point")
    def keep_the_fixed_point(head, args, has_a_value, fixed):
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

    @collection_step("is_choice")
    def same_branches(head, args, has_a_value):
        condition, then, otherwise = args
        return [then] if then == otherwise else args

    declare_properties(Pick, is_choice=True)

    assert normalise(Pick(BoolKind("c"), x, x)) == x


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="what a step builds is not normalised")
def test_a_step_that_merges_arguments_into_a_new_sum():
    Total = declare_function("Total", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Total, is_associative=True, is_commutative=True, identity_element=0)
    Ex = declare_function("Ex", NumberKind, returns=NumberKind, domain=true)
    declare_property("merges_exponents")

    @collection_step("merges_exponents", multiset_only=True)
    def merge(head, args, has_a_value, exp):
        powers = [e for e in args if not e.is_atom and e.head == exp]
        if len(powers) < 2:
            return args
        merged = exp(Total(*(e.args[0] for e in powers)))
        return [e for e in args if e not in powers] + [merged]

    Prd = declare_function("Prd", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Prd, is_associative=True, is_commutative=True, merges_exponents=Ex)

    assert normalise(Prd(Ex(x), Ex(Total(y, z)))) == normalise(Ex(Total(x, y, z)))


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="what a step builds is not normalised")
def test_a_step_that_collects_repeats_into_a_product():
    Times = declare_function("Times", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Times, is_associative=True, is_commutative=True, identity_element=1)
    declare_property("collects_into")

    @collection_step("collects_into", multiset_only=True)
    def collect(head, args, has_a_value, times):
        counts = Counter(args)
        return [arg if n == 1 else times(n, arg) for arg, n in counts.items()]

    Gather = declare_function("Gather", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Gather, is_associative=True, is_commutative=True, collects_into=Times)

    assert normalise(Gather(x, x)) == Times(2, x)
    assert normalise(Gather(Times(3, y), Times(3, y))) == normalise(Times(2, 3, y))


def test_a_step_can_ask_a_condition_only_through_a_function_whose_domain_it_is():
    one = NumberKind(1)
    r = NumberKind("r")
    Recip = declare_function("Recip", r, returns=NumberKind, domain=Ne(r, 0))
    declare_property("is_self_cancelling_ratio")

    @collection_step("is_self_cancelling_ratio")
    def cancel(head, args, has_a_value):
        if len(args) == 2 and args[0] == args[1] and has_a_value(Recip(args[1])):
            return [one]
        return args

    Over = declare_function("Over", NumberKind, NumberKind, returns=NumberKind, domain=true)
    declare_properties(Over, is_self_cancelling_ratio=True)

    assert normalise(Over(x, x)) == Over(x, x)
    assert normalise(Over(x, x), lambda c: c == Ne(x, 0)) == one


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Add and Mul have no step that evaluates literals")
def test_the_package_adds_and_multiplies_literals():
    assert normalise(Add(2, 3)) == NumberKind(5)
    assert normalise(Mul(2, 3)) == NumberKind(6)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="nothing decides an order between arguments")
def test_a_maximum_drops_an_argument_another_one_dominates():
    declare_property("is_maximum")

    @collection_step("is_maximum", multiset_only=True)
    def drop_dominated(head, args, has_a_value):
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


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="no law relates two different heads without a hand-written match")
def test_distribution():
    assert normalise(x * (y + z)) == normalise(x * y + x * z)


def test_a_positional_law_on_a_two_argument_head():
    Track = declare_kind("Track")
    silence = declare_constant("silence", Track)
    declare_property("right_unit_element", element=True)

    @collection_step("right_unit_element")
    def drop_on_the_right(head, args, has_a_value, unit):
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

    @collection_step("mirrored_by")
    def mirror(head, args, has_a_value, other):
        return [other(*reversed(args))] if len(args) == 2 else args

    declare_properties(Above, mirrored_by=Below)

    assert normalise(Above(x, y)) == Below(y, x)

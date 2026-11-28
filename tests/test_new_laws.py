from collections import Counter
from functools import reduce
from itertools import permutations
from math import gcd
from operator import or_

import pytest

from nary import (
    BoolKind, Many, Ne, NumberKind, declare_constant, declare_function, declare_kind, log,
)
from nary.arithmetic import Add
from nary.property_steps import step
from nary.logic import false, true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property

x, y, z = (NumberKind(name) for name in "xyz")
p, q = BoolKind("p"), BoolKind("q")
zero = NumberKind(0)


def test_arguments_repeated_n_times_cancel():
    declare_property("cancel_after")

    @step("cancel_after", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    T3 = declare_function("T3", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        T3, is_associative=True, is_commutative=True, identity_element=0, cancel_after=3,
    )

    assert normalise(T3(x, y, T3(x, x))) == y
    assert normalise(T3(x, x, x, x)) == x
    assert normalise(T3(x, x, y)) == normalise(T3(y, x, x))
    assert Counter(normalise(T3(x, x, y, y)).args) == Counter([x, x, y, y])
    assert normalise(T3(log(x), log(x), log(x))) == T3(log(x), log(x), log(x))
    assert normalise(T3(log(x), log(x), log(x)), lambda c: c == Ne(x, 0)) == zero
    e = T3(x, T3(x, y), x, y, y, z)
    assert normalise(normalise(e)) == normalise(e)

    Xor = declare_function("Xor", Many(BoolKind), returns=BoolKind, domain=true)
    declare_properties(
        Xor, is_associative=True, is_commutative=True, identity_element=false, cancel_after=2,
    )

    assert normalise(Xor(p, q, Xor(p, false))) == q
    assert normalise(Xor(p, p)) == false
    assert normalise(Xor(q, p, p, p)) == normalise(Xor(p, q))
    e = Xor(p, Xor(q, p), q, p)
    assert normalise(normalise(e)) == normalise(e)


def test_arguments_repeated_more_than_k_times_are_capped():
    declare_property("saturate_at")

    @step("saturate_at", per_argument=True)
    def cap(arg, copies, k):
        return min(copies, k)

    Sat = declare_function("Sat", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Sat, is_associative=True, is_commutative=True, saturate_at=2)

    assert normalise(Sat(x, Sat(x, x), y)) == normalise(Sat(x, x, y))
    e = Sat(y, x, Sat(x, x, y))
    assert normalise(normalise(e)) == normalise(e)


def test_arguments_in_pairs_cancel_in_a_symmetric_difference_of_regions():
    Region = declare_kind("Region")
    nowhere = declare_constant("nowhere", Region)
    r = Region("r")
    Bounded = declare_function("Bounded", Region, returns=BoolKind, domain=true)
    Interior = declare_function("Interior", r, returns=Region, domain=Bounded(r))
    declare_property("is_cancelled_in_pairs")

    @step("is_cancelled_in_pairs", per_argument=True)
    def cancel(arg, copies):
        return copies % 2

    SymDiff = declare_function("SymDiff", Many(Region), returns=Region, domain=true)
    declare_properties(
        SymDiff, is_associative=True, is_commutative=True,
        identity_element=nowhere, is_cancelled_in_pairs=True,
    )
    a, b = Region("a"), Region("b")

    assert normalise(SymDiff(a, b, SymDiff(a, nowhere))) == b
    assert normalise(SymDiff(a, b, a)).kind is Region
    assert normalise(SymDiff(a, a)) == nowhere
    assert normalise(SymDiff(a, a)).kind is Region
    assert normalise(SymDiff(b, a, a, a)) == normalise(SymDiff(a, b))
    assert normalise(SymDiff(Interior(a), Interior(a))) == SymDiff(Interior(a), Interior(a))
    assert normalise(SymDiff(Interior(a), Interior(a)), lambda c: c == Bounded(a)) == nowhere


def test_a_turn_and_its_undoing_cancel():
    Turn = declare_kind("Turn")
    still = declare_constant("still", Turn)
    t = Turn("t")
    undo = declare_function("undo", Turn, returns=Turn, domain=true)
    Halvable = declare_function("Halvable", Turn, returns=BoolKind, domain=true)
    Halve = declare_function("Halve", t, returns=Turn, domain=Halvable(t))
    declare_property("opposite")

    @step("opposite", commutative_only=True)
    def cancel_opposites(head, args, opposite):
        counts = Counter(args)
        for e in list(counts):
            if not e.is_atom and e.head == opposite:
                pairs = min(counts[e], counts[e.args[0]])
                counts[e] -= pairs
                counts[e.args[0]] -= pairs
        return list(counts.elements())

    Compose = declare_function("Compose", Many(Turn), returns=Turn, domain=true)
    declare_properties(
        Compose, is_associative=True, is_commutative=True, identity_element=still, opposite=undo,
    )
    a, b, c = Turn("a"), Turn("b"), Turn("c")

    assert normalise(Compose(a, undo(a), b)) == b
    assert normalise(Compose(undo(a), a)) == still
    assert normalise(Compose(undo(a), a)).kind is Turn
    assert normalise(Compose(Halve(a), undo(Halve(a)))) == Compose(Halve(a), undo(Halve(a)))
    assert normalise(Compose(Halve(a), undo(Halve(a))), lambda c: c == Halvable(a)) == still
    e = Compose(undo(b), a, b, undo(a), c, Halve(a), undo(Halve(a)))
    assert normalise(normalise(e)) == normalise(e)


def test_literal_flag_sets_are_combined_by_union():
    FlagSet = declare_kind("FlagSet", literals=frozenset)
    declare_property("fold")

    @step("fold", commutative_only=True)
    def fold_literals(head, args, combine):
        literals = [e for e in args if e.is_literal]
        if len(literals) < 2:
            return args
        folded = head.kind.output(reduce(combine, (e.value for e in literals)))
        return [e for e in args if not e.is_literal] + [folded]

    Merge = declare_function("Merge", Many(FlagSet), returns=FlagSet, domain=true)
    declare_properties(Merge, is_associative=True, is_commutative=True, fold=or_)
    s = FlagSet("s")

    assert normalise(Merge(frozenset({1}), s, frozenset({2}))) == normalise(
        Merge(s, frozenset({1, 2}))
    )
    assert normalise(Merge(frozenset({1}), frozenset({2, 3}))) == FlagSet(frozenset({1, 2, 3}))
    assert normalise(Merge(frozenset({1}), frozenset({1}))).kind is FlagSet


def test_two_new_laws_on_one_head():
    declare_property("negated_by")
    declare_property("cycle_length")

    @step("negated_by", commutative_only=True)
    def cancel_opposites(head, args, minus):
        counts = Counter(args)
        for e in list(counts):
            if not e.is_atom and e.head == minus:
                pairs = min(counts[e], counts[e.args[0]])
                counts[e] -= pairs
                counts[e.args[0]] -= pairs
        return list(counts.elements())

    @step("cycle_length", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    minus = declare_function("minus", NumberKind, returns=NumberKind, domain=true)
    Cyc = declare_function("Cyc", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Cyc, is_associative=True, is_commutative=True,
        negated_by=minus, cycle_length=4, identity_element=0,
    )

    assert normalise(Cyc(x, minus(x), y, y, y, y)) == zero
    assert normalise(Cyc(minus(x), x, x, z, z, z, z, z)) == normalise(Cyc(x, z))
    e = Cyc(minus(y), x, y, minus(x), z, log(x), minus(log(x)))
    assert normalise(normalise(e)) == normalise(e)


def test_a_new_law_with_the_built_in_ones():
    declare_property("fold_with")

    @step("fold_with", commutative_only=True)
    def fold_literals(head, args, combine):
        literals = [e for e in args if e.is_literal]
        if len(literals) < 2:
            return args
        folded = head.kind.output(reduce(combine, (e.value for e in literals)))
        return [e for e in args if not e.is_literal] + [folded]

    Gcf = declare_function("Gcf", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Gcf, is_associative=True, is_commutative=True,
        fold_with=gcd, identity_element=0, absorbing_element=1, is_idempotent=True,
    )

    assert normalise(Gcf(4, x, 6, 3)) == NumberKind(1)
    assert normalise(Gcf(x, 0, x)) == x
    e = Gcf(Gcf(x, 8), 12, y, x)
    assert normalise(normalise(e)) == normalise(e)


def test_one_law_on_two_new_kinds_in_one_expression():
    Switch, Light = declare_kind("Switch"), declare_kind("Light")
    untouched = declare_constant("untouched", Switch)
    unlit = declare_constant("unlit", Light)
    wire = declare_function("wire", Switch, returns=Light, domain=true)
    declare_property("is_toggle")

    @step("is_toggle", per_argument=True)
    def toggle(arg, copies):
        return copies % 2

    Press = declare_function("Press", Many(Switch), returns=Switch, domain=true)
    declare_properties(
        Press, is_associative=True, is_commutative=True, identity_element=untouched, is_toggle=True,
    )
    Flip = declare_function("Flip", Many(Light), returns=Light, domain=true)
    declare_properties(
        Flip, is_associative=True, is_commutative=True, identity_element=unlit, is_toggle=True,
    )
    s, t, m = Switch("s"), Switch("t"), Light("m")

    assert normalise(Flip(wire(Press(s, s, t)), m, m)) == wire(t)
    assert Counter(normalise(Flip(wire(Press(s, s)), m)).args) == Counter([wire(untouched), m])
    assert normalise(Flip(m, m)) == unlit and normalise(Flip(m, m)).kind is Light
    assert normalise(Press(s, s)) == untouched and normalise(Press(s, s)).kind is Switch


def test_a_property_whose_value_is_an_element_of_a_new_kind():
    Edit = declare_kind("Edit")
    clear = declare_constant("clear", Edit)
    declare_property("reset_element", element=True)

    @step("reset_element")
    def forget_before_the_last_reset(head, args, reset):
        if reset not in args:
            return args
        last = len(args) - 1 - args[::-1].index(reset)
        return args[last:]

    History = declare_function("History", Many(Edit), returns=Edit, domain=true)
    with pytest.raises(TypeError, match="History expects Edit, got int: 0"):
        declare_properties(History, is_associative=True, reset_element=0)
    with pytest.raises(TypeError, match="History expects Edit, got BoolKind: true"):
        declare_properties(History, is_associative=True, reset_element=true)
    declare_properties(History, is_associative=True, reset_element=clear)
    a, b, c = Edit("a"), Edit("b"), Edit("c")

    assert History.reset_element == clear and History.reset_element.kind is Edit
    assert normalise(History(a, b, clear, c)) == History(clear, c)
    assert normalise(History(a, History(clear, b), clear, c)) == History(clear, c)
    assert normalise(History(a, clear)) == clear
    assert normalise(History(c, b, a)) == History(c, b, a)


def test_a_count_law_on_a_sequence_acts_on_adjacent_runs():
    Swap = declare_kind("Swap")
    noop = declare_constant("noop", Swap)
    s = Swap("s")
    Known = declare_function("Known", Swap, returns=BoolKind, domain=true)
    Guess = declare_function("Guess", s, returns=Swap, domain=Known(s))
    declare_property("cancel_runs_of")

    @step("cancel_runs_of", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    Shuffle = declare_function("Shuffle", Many(Swap), returns=Swap, domain=true)
    declare_properties(Shuffle, is_associative=True, cancel_runs_of=2, identity_element=noop)
    a, b, c = Swap("a"), Swap("b"), Swap("c")

    assert normalise(Shuffle(a, b, b, a)) == noop
    assert normalise(Shuffle(a, b, b, a)).kind is Swap
    assert normalise(Shuffle(a, Shuffle(b, noop, b), c)) == Shuffle(a, c)
    assert normalise(Shuffle(a, b, a)) == Shuffle(a, b, a)
    assert normalise(Shuffle(b, a, c, c)) == Shuffle(b, a)
    assert normalise(Shuffle(Guess(a), Guess(a))) == Shuffle(Guess(a), Guess(a))


def test_a_commutative_only_step_does_not_run_where_order_matters():
    declare_property("undone_by")
    declare_property("plait_cancel_after")

    @step("undone_by", commutative_only=True)
    def cancel_opposites(head, args, inv):
        counts = Counter(args)
        for e in list(counts):
            if not e.is_atom and e.head == inv:
                pairs = min(counts[e], counts[e.args[0]])
                counts[e] -= pairs
                counts[e.args[0]] -= pairs
        return list(counts.elements())

    @step("plait_cancel_after", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    inv = declare_function("inv", NumberKind, returns=NumberKind, domain=true)
    Plait = declare_function("Plait", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Plait, is_associative=True, undone_by=inv, plait_cancel_after=2, identity_element=0,
    )

    assert normalise(Plait(y, x, x, 0)) == y
    assert normalise(Plait(inv(x), x)) == Plait(inv(x), x)
    e = Plait(x, Plait(y, x, x), inv(y), y)
    assert normalise(normalise(e)) == normalise(e)


def test_a_count_law_on_a_two_argument_commutative_head():
    Key = declare_kind("Key")
    blank = declare_constant("blank", Key)
    k = Key("k")
    Seeded = declare_function("Seeded", Key, returns=BoolKind, domain=true)
    Derive = declare_function("Derive", k, returns=Key, domain=Seeded(k))
    declare_property("duo_cancel_after")

    @step("duo_cancel_after", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    Combine = declare_function("Combine", Key, Key, returns=Key, domain=true)
    declare_properties(Combine, is_commutative=True, identity_element=blank, duo_cancel_after=2)
    a, b = Key("a"), Key("b")

    assert normalise(Combine(a, a)) == blank
    assert normalise(Combine(a, blank)) == a
    assert normalise(Combine(a, blank)).kind is Key
    assert normalise(Combine(b, a)) == normalise(Combine(a, b))
    assert normalise(Combine(Derive(a), Derive(a))) == Combine(Derive(a), Derive(a))


def test_a_property_without_a_step_only_gets_the_structure():
    declare_property("is_mysterious")
    Mystery = declare_function("Mystery", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Mystery, is_associative=True, is_commutative=True, is_mysterious=True)

    assert normalise(Mystery(y, Mystery(x, x))) == Mystery(x, x, y)
    e = Mystery(y, Mystery(x, y))
    assert normalise(normalise(e)) == normalise(e)


def test_a_property_declared_false_takes_no_step():
    Even = declare_function("Even", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Even, is_associative=True, is_commutative=False, is_idempotent=False)

    assert normalise(Even(y, Even(x, x))) == Even(y, x, x)


def test_a_step_cannot_erase_an_argument_that_may_have_no_value():
    declare_property("is_forgetting_logs")

    @step("is_forgetting_logs")
    def forget_logs(head, args):
        return [e for e in args if e.is_atom or e.head != log]

    Forget = declare_function("Forget", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Forget, is_associative=True, is_forgetting_logs=True)

    assert normalise(Forget(x, log(y))) == Forget(x, log(y))
    assert normalise(Forget(x, log(y)), lambda c: c == Ne(y, 0)) == x
    assert normalise(Forget(x, log(y), log(z)), lambda c: c == Ne(y, 0)) == Forget(x, log(y), log(z))


def test_a_per_argument_step_is_held_back_only_for_arguments_that_may_have_no_value():
    declare_property("is_thinned_in_pairs")

    @step("is_thinned_in_pairs", per_argument=True)
    def thin(arg, copies):
        return copies % 2

    Thin = declare_function("Thin", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Thin, is_associative=True, is_thinned_in_pairs=True)

    assert normalise(Thin(x, x, log(y), log(y), z)) == Thin(log(y), log(y), z)


def test_a_step_may_leave_fewer_copies_of_an_argument_that_may_have_no_value():
    declare_property("is_deduplicating")

    @step("is_deduplicating")
    def deduplicate(head, args):
        return list(dict.fromkeys(args))

    Dedup = declare_function("Dedup", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Dedup, is_associative=True, is_deduplicating=True)

    assert normalise(Dedup(log(y), x, log(y))) == Dedup(log(y), x)


def test_a_step_may_add_an_argument():
    stamp = declare_constant("stamp", NumberKind)
    declare_property("is_stamped")

    @step("is_stamped")
    def add_the_stamp(head, args):
        return args if stamp in args else args + [stamp]

    Stamped = declare_function("Stamped", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Stamped, is_associative=True, is_stamped=True)

    assert normalise(Stamped(log(y), x)) == Stamped(log(y), x, stamp)


def test_a_step_does_not_reach_heads_without_its_property():
    declare_property("add_cancel_after")

    @step("add_cancel_after", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    assert normalise(x + x + x) == Add(x, x, x)


def test_a_property_takes_one_step():
    declare_property("one_step_only")

    @step("one_step_only", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    with pytest.raises(ValueError, match="one_step_only already has a step"):
        step("one_step_only")(cancel)
    with pytest.raises(ValueError, match="one_step_only already has a step"):
        step("one_step_only")(lambda head, args, n: args)


def test_a_step_needs_a_declared_property():
    with pytest.raises(ValueError, match="is_unheard_of is not a property"):
        step("is_unheard_of")
    with pytest.raises(ValueError, match="unheard_of is not a property"):
        step("unheard_of")


def test_a_head_declared_after_it_was_normalised():
    declare_property("late_cancel_after")

    @step("late_cancel_after", per_argument=True)
    def cancel(arg, copies, n):
        return copies % n

    Late = declare_function("Late", Many(NumberKind), returns=NumberKind, domain=true)
    assert normalise(Late(x, 0, x)) == Late(x, 0, x)

    declare_properties(
        Late, is_associative=True, is_commutative=True, identity_element=0, late_cancel_after=2,
    )
    assert normalise(Late(x, 0, x)) == zero


def test_a_step_registered_after_a_head_was_normalised():
    declare_property("is_late_step")
    Early = declare_function("Early", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Early, is_associative=True, is_commutative=True, identity_element=0, is_late_step=True,
    )
    assert normalise(Early(x, x, 0)) == normalise(Early(x, x))

    step("is_late_step", per_argument=True)(lambda arg, copies: min(copies, 1))
    assert normalise(Early(x, x, 0)) == x


def test_the_order_of_the_keywords_does_not_change_the_result():
    declare_property("fold_in_any_order")

    @step("fold_in_any_order", commutative_only=True)
    def fold_literals(head, args, combine):
        literals = [e for e in args if e.is_literal]
        if len(literals) < 2:
            return args
        folded = head.kind.output(reduce(combine, (e.value for e in literals)))
        return [e for e in args if not e.is_literal] + [folded]

    given = [
        ("fold_in_any_order", gcd), ("identity_element", 0),
        ("absorbing_element", 1), ("is_idempotent", True),
    ]
    for order in permutations(range(4)):
        G = declare_function(
            f"Gcd{''.join(map(str, order))}", Many(NumberKind), returns=NumberKind, domain=true,
        )
        declare_properties(
            G, is_associative=True, is_commutative=True, **dict(given[i] for i in order),
        )
        assert normalise(G(4, x, 6, 3)) == NumberKind(1)
        assert normalise(G(x, 0, G(x, x))) == x
        assert normalise(G(4, x, 6, x, 0)) == normalise(G(2, x))


def test_steps_that_never_stop_changing_the_arguments_raise():
    declare_property("is_kept_in_reverse")

    @step("is_kept_in_reverse")
    def reverse(head, args):
        return args[::-1]

    Shelf = declare_function("Shelf", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Shelf, is_associative=True, is_commutative=True, is_kept_in_reverse=True)

    assert normalise(Shelf(x)) == x
    with pytest.raises(RuntimeError, match="never stop changing"):
        normalise(Shelf(x, y))

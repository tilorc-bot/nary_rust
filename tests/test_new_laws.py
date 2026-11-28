from collections import Counter
from functools import reduce
from itertools import permutations
from math import gcd

import pytest

from nary import BoolKind, Many, Ne, NumberKind, declare_function, log
from nary.arithmetic import Add
from nary.argument_collections import acting_properties, collection_step, count_step
from nary.logic import false, true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property

x, y, z = (NumberKind(name) for name in "xyz")
p, q = BoolKind("p"), BoolKind("q")
zero = NumberKind(0)


def test_arguments_repeated_n_times_cancel():
    declare_property("cancel_after")

    @count_step("cancel_after")
    def cancel(arg, count, n):
        return count % n

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

    @count_step("saturate_at")
    def cap(arg, count, k):
        return min(count, k)

    Sat = declare_function("Sat", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Sat, is_associative=True, is_commutative=True, saturate_at=2)

    assert normalise(Sat(x, Sat(x, x), y)) == normalise(Sat(x, x, y))
    e = Sat(y, x, Sat(x, x, y))
    assert normalise(normalise(e)) == normalise(e)


def test_an_argument_and_its_opposite_cancel():
    declare_property("opposite")

    @collection_step("opposite", multiset_only=True)
    def cancel_opposites(head, args, has_a_value, neg):
        counts = Counter(args)
        for e in list(counts):
            if not e.is_atom and e.head == neg and has_a_value(e):
                pairs = min(counts[e], counts[e.args[0]])
                counts[e] -= pairs
                counts[e.args[0]] -= pairs
        return list(counts.elements())

    neg = declare_function("neg", NumberKind, returns=NumberKind, domain=true)
    Opp = declare_function("Opp", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Opp, is_associative=True, is_commutative=True, identity_element=0, opposite=neg,
    )

    assert normalise(Opp(x, neg(x), y)) == y
    assert normalise(Opp(log(x), neg(log(x)))) == Opp(log(x), neg(log(x)))
    assert normalise(Opp(log(x), neg(log(x))), lambda c: c == Ne(x, 0)) == zero
    e = Opp(neg(y), x, y, neg(x), z, log(x), neg(log(x)))
    assert normalise(normalise(e)) == normalise(e)


def test_literal_arguments_are_combined_by_a_python_function():
    declare_property("fold")

    @collection_step("fold", multiset_only=True)
    def fold_literals(head, args, has_a_value, combine):
        literals = [e for e in args if e.is_literal]
        if len(literals) < 2:
            return args
        folded = head.kind.output(reduce(combine, (e.value for e in literals)))
        return [e for e in args if not e.is_literal] + [folded]

    Gcd = declare_function("Gcd", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Gcd, is_associative=True, is_commutative=True, fold=gcd)

    assert normalise(Gcd(4, x, 6)) == normalise(Gcd(2, x))
    assert normalise(Gcd(12, 18)) == NumberKind(6)


def test_two_new_laws_on_one_head():
    declare_property("negated_by")
    declare_property("cycle_length")

    @collection_step("negated_by", multiset_only=True)
    def cancel_opposites(head, args, has_a_value, minus):
        counts = Counter(args)
        for e in list(counts):
            if not e.is_atom and e.head == minus and has_a_value(e):
                pairs = min(counts[e], counts[e.args[0]])
                counts[e] -= pairs
                counts[e.args[0]] -= pairs
        return list(counts.elements())

    @count_step("cycle_length")
    def cancel(arg, count, n):
        return count % n

    minus = declare_function("minus", NumberKind, returns=NumberKind, domain=true)
    Cyc = declare_function("Cyc", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Cyc, is_associative=True, is_commutative=True,
        negated_by=minus, cycle_length=4, identity_element=0,
    )

    assert Counter(acting_properties(Cyc)) == Counter(
        ["negated_by", "cycle_length", "identity_element"]
    )
    assert normalise(Cyc(x, minus(x), y, y, y, y)) == zero
    assert normalise(Cyc(minus(x), x, x, z, z, z, z, z)) == normalise(Cyc(x, z))
    e = Cyc(minus(y), x, y, minus(x), z, log(x), minus(log(x)))
    assert normalise(normalise(e)) == normalise(e)


def test_a_new_law_with_the_built_in_ones():
    declare_property("fold_with")

    @collection_step("fold_with", multiset_only=True)
    def fold_literals(head, args, has_a_value, combine):
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

    assert Counter(acting_properties(Gcf)) == Counter(
        ["fold_with", "identity_element", "absorbing_element", "is_idempotent"]
    )
    assert normalise(Gcf(4, x, 6, 3)) == NumberKind(1)
    assert normalise(Gcf(x, 0, x)) == x
    e = Gcf(Gcf(x, 8), 12, y, x)
    assert normalise(normalise(e)) == normalise(e)


def test_a_count_law_on_a_sequence_acts_on_adjacent_runs():
    declare_property("cancel_runs_of")

    @count_step("cancel_runs_of")
    def cancel(arg, count, n):
        return count % n

    Braid = declare_function("Braid", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Braid, is_associative=True, cancel_runs_of=2, identity_element=0)

    assert normalise(Braid(x, y, y, x)) == zero
    assert normalise(Braid(x, Braid(y, 0, y), z)) == Braid(x, z)
    assert normalise(Braid(x, y, x)) == Braid(x, y, x)
    assert normalise(Braid(y, x, z, z)) == Braid(y, x)
    assert normalise(Braid(log(x), log(x))) == Braid(log(x), log(x))


def test_a_multiset_step_does_not_run_on_a_sequence():
    declare_property("undone_by")
    declare_property("plait_cancel_after")

    @collection_step("undone_by", multiset_only=True)
    def cancel_opposites(head, args, has_a_value, inv):
        counts = Counter(args)
        for e in list(counts):
            if not e.is_atom and e.head == inv and has_a_value(e):
                pairs = min(counts[e], counts[e.args[0]])
                counts[e] -= pairs
                counts[e.args[0]] -= pairs
        return list(counts.elements())

    @count_step("plait_cancel_after")
    def cancel(arg, count, n):
        return count % n

    inv = declare_function("inv", NumberKind, returns=NumberKind, domain=true)
    Plait = declare_function("Plait", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Plait, is_associative=True, undone_by=inv, plait_cancel_after=2, identity_element=0,
    )

    assert Counter(acting_properties(Plait)) == Counter(["plait_cancel_after", "identity_element"])
    assert normalise(Plait(inv(x), x)) == Plait(inv(x), x)
    e = Plait(x, Plait(y, x, x), inv(y), y)
    assert normalise(normalise(e)) == normalise(e)


def test_a_count_law_on_a_two_argument_commutative_head():
    declare_property("duo_cancel_after")

    @count_step("duo_cancel_after")
    def cancel(arg, count, n):
        return count % n

    Duo = declare_function("Duo", NumberKind, NumberKind, returns=NumberKind, domain=true)
    declare_properties(Duo, is_commutative=True, identity_element=0, duo_cancel_after=2)

    assert normalise(Duo(x, x)) == zero
    assert normalise(Duo(x, 0)) == x
    assert normalise(Duo(y, x)) == normalise(Duo(x, y))
    assert normalise(Duo(log(x), log(x))) == Duo(log(x), log(x))


def test_a_property_without_a_step_only_gets_the_structure():
    declare_property("is_mysterious")
    Mystery = declare_function("Mystery", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Mystery, is_associative=True, is_commutative=True, is_mysterious=True)

    assert acting_properties(Mystery) == []
    assert normalise(Mystery(y, Mystery(x, x))) == normalise(Mystery(x, y, x))
    e = Mystery(y, Mystery(x, y))
    assert normalise(normalise(e)) == normalise(e)


def test_a_step_does_not_reach_heads_without_its_property():
    declare_property("add_cancel_after")

    @count_step("add_cancel_after")
    def cancel(arg, count, n):
        return count % n

    assert normalise(x + x + x) == normalise(Add(x, x, x))
    assert acting_properties(Add) == ["identity_element"]


def test_a_property_takes_one_step():
    declare_property("one_step_only")

    @count_step("one_step_only")
    def cancel(arg, count, n):
        return count % n

    with pytest.raises(ValueError, match="one_step_only already has a step"):
        count_step("one_step_only")(cancel)
    with pytest.raises(ValueError, match="one_step_only already has a step"):
        collection_step("one_step_only")(lambda head, args, has_a_value, n: args)


def test_a_step_needs_a_declared_property():
    with pytest.raises(ValueError, match="is_unheard_of is not a property"):
        count_step("is_unheard_of")
    with pytest.raises(ValueError, match="unheard_of is not a property"):
        collection_step("unheard_of")


def test_a_head_declared_after_it_was_normalised():
    declare_property("late_cancel_after")

    @count_step("late_cancel_after")
    def cancel(arg, count, n):
        return count % n

    Late = declare_function("Late", Many(NumberKind), returns=NumberKind, domain=true)
    assert normalise(Late(x, 0, x)) == Late(x, 0, x)
    assert acting_properties(Late) == []

    declare_properties(
        Late, is_associative=True, is_commutative=True, identity_element=0, late_cancel_after=2,
    )
    assert normalise(Late(x, 0, x)) == zero
    assert Counter(acting_properties(Late)) == Counter(["identity_element", "late_cancel_after"])


def test_a_step_registered_after_a_head_was_normalised():
    declare_property("is_late_step")
    Early = declare_function("Early", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(
        Early, is_associative=True, is_commutative=True, identity_element=0, is_late_step=True,
    )
    assert normalise(Early(x, x, 0)) == normalise(Early(x, x))

    count_step("is_late_step")(lambda arg, count: min(count, 1))
    assert normalise(Early(x, x, 0)) == x


def test_the_order_of_the_keywords_does_not_change_the_result():
    declare_property("fold_in_any_order")

    @collection_step("fold_in_any_order", multiset_only=True)
    def fold_literals(head, args, has_a_value, combine):
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

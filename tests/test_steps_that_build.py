from collections import Counter
from fractions import Fraction

from nary import Add, Many, Mul, Ne, NumberKind, Pow, declare_function, log, normalising, sin
from nary.logic import true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property
from nary.property_steps import step

x, y, z = (NumberKind(name) for name in "xyz")


def number_head(name, **properties):
    head = declare_function(name, Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(head, **properties)
    return head


declare_property("merges_equal_bases")


@step("merges_equal_bases", merges=True)
def _equal_bases_merged(head, args, power):
    by_base = {}
    for arg in args:
        if not arg.is_atom and arg.head == power:
            by_base.setdefault(arg.args[0], []).append(arg)
    return [
        (group, power(base, Add(*(arg.args[1] for arg in group))))
        for base, group in by_base.items() if len(group) > 1
    ]


Product = number_head(
    "BuildProduct", is_associative=True, is_commutative=True, identity_element=1,
    merges_equal_bases=Pow,
)


def test_a_step_that_merges_arguments_into_a_new_sum():
    Total = declare_function("Total", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Total, is_associative=True, is_commutative=True, identity_element=0)
    Ex = declare_function("Ex", NumberKind, returns=NumberKind, domain=true)
    declare_property("merges_exponents")

    @step("merges_exponents", commutative_only=True)
    def merge(head, args, exp):
        powers = [e for e in args if not e.is_atom and e.head == exp]
        if len(powers) < 2:
            return args
        merged = exp(Total(*(e.args[0] for e in powers)))
        return [e for e in args if e not in powers] + [merged]

    Prd = declare_function("Prd", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Prd, is_associative=True, is_commutative=True, merges_exponents=Ex)

    assert normalise(Prd(Ex(x), Ex(Total(y, z)))) == normalise(Ex(Total(x, y, z)))


def test_a_step_that_collects_repeats_into_a_product():
    Times = declare_function("Times", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Times, is_associative=True, is_commutative=True, identity_element=1)
    declare_property("collects_into")

    @step("collects_into", commutative_only=True)
    def collect(head, args, times):
        counts = Counter(args)
        return [arg if n == 1 else times(n, arg) for arg, n in counts.items()]

    Gather = declare_function("Gather", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(Gather, is_associative=True, is_commutative=True, collects_into=Times)

    assert normalise(Gather(x, x)) == Times(2, x)
    assert normalise(Gather(Times(3, y), Times(3, y))) == normalise(Times(2, 3, y))



def test_a_merged_argument_is_normalised():
    assert normalise(Product(Pow(x, 2), Pow(x, 3))) == Pow(x, 5)


def test_groups_with_different_bases_are_merged_separately():
    assert normalise(Product(Pow(x, 2), Pow(y, 1), Pow(x, 3), Pow(y, 2))) == Product(
        Pow(x, 5), Pow(y, 3)
    )


def test_a_group_whose_merge_could_give_a_value_where_there_was_none_is_left():
    assert normalise(Product(Pow(y, -1), Pow(y, 2))) == Product(Pow(y, -1), Pow(y, 2))


def test_a_group_that_is_left_does_not_stop_another_group_from_merging():
    assert normalise(Product(Pow(x, 2), Pow(y, -1), Pow(x, 3), Pow(y, 2))) == Product(
        Pow(x, 5), Pow(y, -1), Pow(y, 2)
    )


def test_a_group_whose_merge_has_a_value_only_where_the_group_has_one_is_merged():
    assert normalise(Product(Pow(y, -1), Pow(y, -2))) == Pow(y, -3)


def test_a_group_whose_merge_could_give_a_value_is_merged_where_known_says_it_has_one():
    assert normalise(Product(Pow(y, -1), Pow(y, 2)), lambda c: c == Ne(y, 0)) == Pow(y, 1)


def test_a_merged_argument_with_the_same_head_is_spread_into_the_arguments():
    declare_property("spreads_into_itself")

    @step("spreads_into_itself", merges=True)
    def wrapped_unwrapped(head, args, wrap):
        group = [arg for arg in args if not arg.is_atom and arg.head == wrap]
        return [(group, head(*(arg.args[0] for arg in group)))] if group else []

    Wrap = declare_function("BuildWrap", NumberKind, returns=NumberKind, domain=true)
    Bag = number_head(
        "BuildBag", is_associative=True, is_commutative=True, spreads_into_itself=Wrap,
    )

    assert normalise(Bag(Wrap(x), z, Wrap(y))) == Bag(x, y, z)


def test_an_argument_that_may_have_no_value_may_be_removed_when_it_is_inside_what_replaces_it():
    declare_property("collects_logarithms_into")

    @step("collects_logarithms_into", commutative_only=True)
    def collect(head, args, times):
        counts = Counter(args)
        return [arg if n == 1 else times(n, arg) for arg, n in counts.items()]

    Times = number_head("BuildTimes", is_associative=True, is_commutative=True)
    Gather = number_head(
        "BuildGather", is_associative=True, is_commutative=True, collects_logarithms_into=Times,
    )

    assert normalise(Gather(log(x), log(x), y)) == Gather(Times(2, log(x)), y)


def test_the_order_of_the_arguments_does_not_change_the_result():
    e = Product(Pow(y, 2), Pow(x, z), Pow(y, -1), Pow(x, 1))
    assert normalise(e) == normalise(Product(*reversed(e.args)))


def test_normalising_twice_is_normalising_once():
    once = normalise(Product(Pow(x, 2), Pow(x, z), Pow(y, -1), Pow(y, 2), Pow(x, 1)))
    assert normalise(once) == once


def value(e, at):
    if e.is_literal:
        return Fraction(e.value)
    if e.is_symbol:
        return at[e]
    args = [value(arg, at) for arg in e.args]
    if e.head == Product:
        result = Fraction(1)
        for arg in args:
            result *= arg
        return result
    if e.head == Pow:
        return args[0] ** int(args[1])
    if e.head == Add:
        return sum(args, Fraction(0))
    raise ValueError(e)


def test_merging_keeps_the_value():
    e = Product(Pow(x, 2), Pow(y, -1), Pow(x, 3), Pow(y, -2), Pow(z, 1), Pow(z, 1))
    points = [(2, -3, 5), (Fraction(1, 2), 7, -1), (-4, 1, 0)]
    for at in ({x: Fraction(a), y: Fraction(b), z: Fraction(c)} for a, b, c in points):
        assert value(normalise(e), at) == value(e, at)


def test_an_expression_a_step_returns_in_place_of_the_arguments_is_normalised():
    Half = declare_function("BuildHalf", NumberKind, returns=NumberKind, domain=true)
    declare_property("halves_into")

    @step("halves_into")
    def half_as_a_product(head, args, product):
        return product(Fraction(1, 2), args[0], 1)

    declare_properties(Half, halves_into=Product)

    assert normalise(Half(x)) == Product(Fraction(1, 2), x)


def test_a_node_whose_steps_change_nothing_is_visited_once(monkeypatch):
    visited = []
    apply_property_steps = normalising.apply_property_steps

    def recording(head, args, *rest):
        visited.append(head(*args))
        return apply_property_steps(head, args, *rest)

    monkeypatch.setattr(normalising, "apply_property_steps", recording)
    assert normalise(Add(sin(z), Mul(y, x), x)) == Add(Mul(x, y), sin(z), x)
    assert visited == [sin(z), Mul(x, y), Add(Mul(x, y), sin(z), x)]

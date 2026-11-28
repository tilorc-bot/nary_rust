from fractions import Fraction
from itertools import groupby, product

import pytest

from nary import Add, BoolKind, Lt, Many, Mul, NumberKind, Pow, declare_function, log, sin
from nary.property_steps import step
from nary.logic import And, Not, Or, false, true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property

pytestmark = pytest.mark.fuzz

x, y, z = (NumberKind(name) for name in "xyz")
p, q, r = (BoolKind(name) for name in "pqr")
n = NumberKind


def head(name, kind=NumberKind):
    return declare_function(name, Many(kind), returns=kind, domain=true)


declare_property("fuzz_period")


@step("fuzz_period", per_argument=True)
def _period(arg, copies, k):
    return copies % k


Bag = head("FuzzBag")
declare_properties(
    Bag, is_associative=True, is_commutative=True, identity_element=0, absorbing_element=9,
    is_idempotent=True,
)
Seq = head("FuzzSeq")
declare_properties(
    Seq, is_associative=True, identity_element=0, absorbing_element=9, is_idempotent=True,
)
Cat = head("FuzzCat")
declare_properties(Cat, is_associative=True, identity_element=0)
Pair = declare_function("FuzzPair", NumberKind, NumberKind, returns=NumberKind, domain=true)
declare_properties(
    Pair, is_commutative=True, identity_element=0, absorbing_element=1, is_idempotent=True,
)
Plain = head("FuzzPlain")
Max = head("FuzzMax")
declare_properties(
    Max, is_associative=True, is_commutative=True, identity_element=0, is_idempotent=True,
)
Xor = head("FuzzXor", BoolKind)
declare_properties(Xor, is_associative=True, is_commutative=True, identity_element=false, fuzz_period=2)


def tree(rng, depth, leaf, heads):
    if depth == 0 or rng.random() < 0.25:
        return leaf(rng)
    f = rng.choice(heads)
    arity = len(f.kind.inputs) if f.kind.inputs[0].family is not Many else rng.choice([0, 1, 2, 2, 3, 3, 4])
    return f(*(tree(rng, depth - 1, leaf, heads) for _ in range(arity)))


def number_leaf(rng):
    return rng.choice([x, y, z, x, y, n(0), n(1), n(2), n(9)])


def partial_leaf(rng):
    return rng.choice([x, y, z, n(0), n(1), n(2), n(9), log(x), log(y), sin(x)])


total_heads = [Add, Mul, Bag, Seq, Cat, Pair, Plain, Max, sin]
number_heads = [*total_heads, Pow]


def anything(rng):
    if rng.random() < 0.3:
        return tree(rng, 3, boolean_leaf, [And, Or, Xor, Not])
    return tree(rng, 4, partial_leaf, number_heads)


def boolean_leaf(rng):
    if rng.random() < 0.15:
        return Lt(tree(rng, 2, partial_leaf, number_heads), tree(rng, 1, partial_leaf, number_heads))
    return rng.choice([p, q, r, true, false])


def total(rng):
    return tree(rng, 4, number_leaf, total_heads)


def flat_args(f, e):
    if e.is_atom or e.head != f:
        return [e]
    return [leaf for arg in e.args for leaf in flat_args(f, arg)]


def shuffled(e, rng):
    if e.is_atom:
        return e
    args = [shuffled(arg, rng) for arg in e.args]
    if e.head.is_commutative:
        rng.shuffle(args)
    return e.head(*args)


def bracketed(f, args, rng):
    if len(args) <= 2 or rng.random() < 0.3:
        return f(*args)
    i = rng.randrange(len(args) - 1)
    j = rng.randrange(i + 2, len(args) + 1)
    if j - i == len(args):
        return f(*args)
    return bracketed(f, [*args[:i], f(*args[i:j]), *args[j:]], rng)


def rebracketed(e, rng):
    if e.is_atom:
        return e
    if e.head.is_associative:
        args = [rebracketed(arg, rng) for arg in flat_args(e.head, e)]
        if rng.random() < 0.2:
            args.insert(rng.randrange(len(args) + 1), e.head())
        return bracketed(e.head, args, rng)
    return e.head(*(rebracketed(arg, rng) for arg in e.args))


def same_normal_form(e, other):
    a, b = normalise(e), normalise(other)
    return a == b or f"{other!r} normalises to {b!r}, not {a!r}"


def test_shuffling_commutative_arguments_keeps_the_normal_form(fuzz):
    fuzz.check(anything, lambda e, rng: same_normal_form(e, shuffled(e, rng)))


@pytest.mark.xfail(reason="test_number_literals_inside_brackets_are_combined_only_when_every_node_is_handled fails")
def test_rebracketing_associative_arguments_keeps_the_normal_form(fuzz):
    fuzz.check(total, lambda e, rng: same_normal_form(e, rebracketed(shuffled(e, rng), rng)))


@pytest.mark.xfail(reason=(
    "test_number_literals_inside_brackets_are_combined_only_when_every_node_is_handled and "
    "test_an_absorbing_element_inside_brackets_erases_more_when_every_node_is_handled fail"
))
def test_rebracketing_keeps_the_normal_form_with_arguments_without_a_value(fuzz):
    fuzz.check(anything, lambda e, rng: same_normal_form(e, rebracketed(e, rng)))


def test_normalising_twice_is_normalising_once(fuzz):
    def holds(e, rng):
        once = normalise(e)
        twice = normalise(once)
        return twice == once or f"{once!r} normalises again to {twice!r}"

    fuzz.check(anything, holds)


def sequence_leaf(rng):
    return tree(rng, 2, number_leaf, [Add, Mul, Bag, Pair, Plain, sin])


def cat_and_leaves(rng):
    leaves = [sequence_leaf(rng) for _ in range(rng.randint(0, 6))]
    for _ in range(rng.randint(0, 2)):
        if leaves:
            leaves.insert(rng.randrange(len(leaves)), rng.choice(leaves))
    return bracketed(Cat, leaves, rng)


def test_a_sequence_without_steps_keeps_every_argument_in_order(fuzz):
    def holds(e, rng):
        kept = [normalise(leaf) for leaf in flat_args(Cat, e) if normalise(leaf) != n(0)]
        expected = n(0) if not kept else kept[0] if len(kept) == 1 else Cat(*kept)
        return normalise(e) == expected or f"{normalise(e)!r}, expected {expected!r}"

    fuzz.check(cat_and_leaves, holds)


def seq_and_leaves(rng):
    leaves = [rng.choice([x, y, z, n(0), n(9), sin(x), Add(x, y)]) for _ in range(rng.randint(0, 7))]
    return bracketed(Seq, leaves, rng)


def test_an_idempotent_sequence_merges_only_neighbours(fuzz):
    def holds(e, rng):
        kept = [normalise(leaf) for leaf in flat_args(Seq, e) if leaf != n(0)]
        kept = [arg for arg, _ in groupby(kept)]
        if n(9) in kept:
            expected = n(9)
        else:
            expected = n(0) if not kept else kept[0] if len(kept) == 1 else Seq(*kept)
        return normalise(e) == expected or f"{normalise(e)!r}, expected {expected!r}"

    fuzz.check(seq_and_leaves, holds)


def boolean_value(e, at):
    if e in at:
        return at[e]
    if e == true or e == false:
        return e == true
    args = [boolean_value(arg, at) for arg in e.args]
    if e.head == And:
        return all(args)
    if e.head == Or:
        return any(args)
    if e.head == Xor:
        return sum(args) % 2 == 1
    if e.head == Not:
        return not args[0]
    raise ValueError(f"no value for {e!r}")


def test_normalising_keeps_the_value_of_a_boolean_expression(fuzz):
    def boolean(rng):
        return tree(rng, 4, lambda rng: rng.choice([p, q, r, true, false]), [And, Or, Xor, Not])

    def holds(e, rng):
        normal = normalise(e)
        for values in product([False, True], repeat=3):
            at = dict(zip([p, q, r], values))
            if boolean_value(normal, at) != boolean_value(e, at):
                return f"normalises to {normal!r}, which differs at {at}"
        return True

    fuzz.check(boolean, holds)


def number_value(e, at, pair=None):
    if e.is_literal:
        return Fraction(e.value)
    if e.is_symbol:
        return at[e]
    args = [number_value(arg, at, pair) for arg in e.args]
    if e.head == Add:
        return sum(args, Fraction(0))
    if e.head == Mul:
        product_ = Fraction(1)
        for arg in args:
            product_ *= arg
        return product_
    if e.head == Max:
        return max(args, default=Fraction(0))
    if e.head == Pair:
        return pair[int(args[0])][int(args[1])]
    raise ValueError(f"no value for {e!r}")


def test_normalising_keeps_the_value_of_a_polynomial(fuzz):
    def polynomial(rng):
        return tree(rng, 4, lambda rng: rng.choice([x, y, z, n(0), n(1), n(-1), n(2)]), [Add, Mul])

    def holds(e, rng):
        normal = normalise(e)
        for _ in range(3):
            at = {s: Fraction(rng.randint(-9, 9), rng.randint(1, 4)) for s in (x, y, z)}
            if number_value(normal, at) != number_value(e, at):
                return f"normalises to {normal!r}, which differs at {at}"
        return True

    fuzz.check(polynomial, holds)


def pair_table(rng, size=5):
    table = [[None] * size for _ in range(size)]
    for a in range(size):
        for b in range(a, size):
            if a == b:
                value = a
            elif a == 0:
                value = b
            elif a == 1 or b == 1:
                value = 1
            else:
                value = rng.randrange(size)
            table[a][b] = table[b][a] = Fraction(value)
    return table


def test_normalising_keeps_the_value_of_a_pair_and_a_maximum(fuzz):
    def expression(rng):
        return tree(rng, 4, lambda rng: rng.choice([x, y, z, *map(n, range(5))]), [Pair, Max])

    def holds(e, rng):
        normal = normalise(e)
        for _ in range(4):
            table = pair_table(rng)
            at = {s: Fraction(rng.randrange(5)) for s in (x, y, z)}
            if number_value(normal, at, table) != number_value(e, at, table):
                return f"normalises to {normal!r}, which differs at {at} with {table}"
        return True

    fuzz.check(expression, holds)

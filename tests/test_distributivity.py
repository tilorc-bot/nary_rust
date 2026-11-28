import cmath
from fractions import Fraction
from functools import reduce

import pytest

from distributivity_support import (
    cases, check_different_normal_form, check_same_normal_form, check_shape_kept, every_writing,
    knowing, pairs, shape, unequal_pairs,
)
from nary import (
    Add, BoolKind, Lt, Many, Mul, Ne, NumberKind, Pow, cos, declare_constant, declare_function,
    declare_kind, log, sin,
)
from nary.logic import And, Not, Or, false, true
from nary.normalising import normalise
from nary.properties import declare_properties, declare_property, is_property

if not is_property("distributes_over"):
    declare_property("distributes_over")

COLLECT = "like terms are not collected"
EXPONENTS = "exponents are not merged"
ABSORPTION = "absorption is not derived"
POWER_DOMAIN = "re of a number is not evaluated"

x, y, z = (NumberKind(name) for name in "xyz")
p, q, r = (BoolKind(name) for name in "pqr")
n = NumberKind

DistSet = declare_kind("DistSet")
dist_empty = declare_constant("dist_empty", DistSet)
dist_everything = declare_constant("dist_everything", DistSet)
DistUnion = declare_function("DistUnion", Many(DistSet), returns=DistSet, domain=true)
DistInter = declare_function("DistInter", Many(DistSet), returns=DistSet, domain=true)
declare_properties(
    DistUnion, is_associative=True, is_commutative=True, identity_element=dist_empty,
    absorbing_element=dist_everything, is_idempotent=True, distributes_over=DistInter,
)
declare_properties(
    DistInter, is_associative=True, is_commutative=True, identity_element=dist_everything,
    absorbing_element=dist_empty, is_idempotent=True, distributes_over=DistUnion,
)
a, b, c = (DistSet(name) for name in "abc")

DistMax = declare_function("DistMax", Many(NumberKind), returns=NumberKind, domain=true)
DistPlus = declare_function("DistPlus", Many(NumberKind), returns=NumberKind, domain=true)
declare_properties(DistMax, is_associative=True, is_commutative=True, is_idempotent=True)
declare_properties(
    DistPlus, is_associative=True, is_commutative=True, identity_element=0,
    distributes_over=DistMax,
)

DistLang = declare_kind("DistLang")
dist_eps = declare_constant("dist_eps", DistLang)
dist_none = declare_constant("dist_none", DistLang)
DistCat = declare_function("DistCat", Many(DistLang), returns=DistLang, domain=true)
DistAlt = declare_function("DistAlt", Many(DistLang), returns=DistLang, domain=true)
declare_properties(
    DistAlt, is_associative=True, is_commutative=True, identity_element=dist_none,
    is_idempotent=True,
)
declare_properties(
    DistCat, is_associative=True, identity_element=dist_eps, absorbing_element=dist_none,
    distributes_over=DistAlt,
)
s, t, w = (DistLang(name) for name in "stw")

DistVec = declare_kind("DistVec")
dist_origin = declare_constant("dist_origin", DistVec)
DistVAdd = declare_function("DistVAdd", Many(DistVec), returns=DistVec, domain=true)
DistScale = declare_function("DistScale", NumberKind, DistVec, returns=DistVec, domain=true)
declare_properties(
    DistVAdd, is_associative=True, is_commutative=True, identity_element=dist_origin,
)
declare_properties(DistScale, distributes_over=DistVAdd)
u, v = DistVec("u"), DistVec("v")
j, k = NumberKind("j"), NumberKind("k")

EVERYTHING = frozenset({0, 1, 2})


def _power(base, exponent):
    if isinstance(exponent, Fraction) and exponent.denominator == 1:
        return base ** int(exponent)
    return complex(base) ** complex(exponent)


def _product(*factors):
    return reduce(lambda left, right: left * right, factors, Fraction(1))


MODEL = {
    Add: lambda *terms: sum(terms, Fraction(0)),
    Mul: _product,
    Pow: _power,
    sin: lambda e: cmath.sin(complex(e)),
    cos: lambda e: cmath.cos(complex(e)),
    log: lambda e: cmath.log(complex(e)),
    Lt: lambda left, right: left < right,
    And: lambda *args: all(args),
    Or: lambda *args: any(args),
    Not: lambda arg: not arg,
    true: True,
    false: False,
    DistUnion: lambda *sets: frozenset().union(*sets),
    DistInter: lambda *sets: reduce(frozenset.intersection, sets, EVERYTHING),
    dist_empty: frozenset(),
    dist_everything: EVERYTHING,
    DistMax: lambda *args: max(args),
    DistPlus: lambda *terms: sum(terms, Fraction(0)),
    DistCat: lambda *langs: reduce(
        lambda left, right: frozenset(l + r for l in left for r in right), langs, frozenset({""}),
    ),
    DistAlt: lambda *langs: frozenset().union(*langs),
    dist_eps: frozenset({""}),
    dist_none: frozenset(),
    DistVAdd: lambda *vecs: tuple(sum(parts, Fraction(0)) for parts in zip((0, 0), *vecs)),
    DistScale: lambda factor, vec: tuple(factor * part for part in vec),
    dist_origin: (Fraction(0), Fraction(0)),
}

NONZERO = [Fraction(-3), Fraction(-1, 2), Fraction(1, 3), Fraction(2), Fraction(5, 2), Fraction(7)]


def _sample(kind, rng):
    if kind == NumberKind:
        return rng.choice(NONZERO)
    if kind == DistSet:
        return frozenset(e for e in EVERYTHING if rng.random() < 0.5)
    if kind == DistLang:
        return frozenset(rng.sample(["", "a", "b", "ba"], rng.randint(0, 2)))
    if kind == DistVec:
        return (rng.choice(NONZERO), rng.choice(NONZERO))
    raise ValueError(f"no values for {kind!r}")


def unequal(table):
    return unequal_pairs(table, MODEL, _sample)


COLLECTING_IN_SUMS = [
    (x + x, 2 * x, COLLECT),
    (x + x + x, 3 * x, COLLECT),
    (Add(x, x, x, x), 4 * x, COLLECT),
    (Add(x, Add(x, x)), 3 * x, COLLECT),
    (2 * x + 3 * x, 5 * x, COLLECT),
    (x + 2 * x, 3 * x, COLLECT),
    (2 * x + x, 3 * x, COLLECT),
    (Add(x, y, x), 2 * x + y, COLLECT),
    (Add(x, y, x, y), 2 * x + 2 * y, COLLECT),
    (Add(x, y, x, z, y, x), 3 * x + 2 * y + z, COLLECT),
    (2 * x + 3 * x + 4 * y + y, 5 * x + 5 * y, COLLECT),
    (x * y + y * x, 2 * x * y, COLLECT),
    (Add(x * y, y * x, x * y), 3 * x * y, COLLECT),
    (Add(x * y * z, z * y * x, y * Mul(x, z)), 3 * x * y * z, COLLECT),
    (2 * x * y + 3 * y * x, 5 * x * y, COLLECT),
    (Mul(x, 2) + Mul(x, 3), Mul(x, 5), COLLECT),
    (Mul(x, y, 2) + Mul(3, y, x), 5 * x * y, COLLECT),
    (Mul(y, 2, x) + x * y, 3 * x * y, COLLECT),
    (sin(x) + sin(x), 2 * sin(x), COLLECT),
    (sin(x) + 2 * sin(x), 3 * sin(x), COLLECT),
    (sin(x + y) + sin(y + x), 2 * sin(x + y), COLLECT),
    (Add(2 * sin(x), cos(x), 3 * sin(x)), 5 * sin(x) + cos(x), COLLECT),
    (sin(x) * cos(x) + cos(x) * sin(x), 2 * sin(x) * cos(x), COLLECT),
    (Add(Add(x, y), Add(y, x)), 2 * x + 2 * y, COLLECT),
    (Add(x, Add(y, Add(x, y))), 2 * x + 2 * y, COLLECT),
    (Add(Add(2 * x, y), Add(Add(3 * x), z)), 5 * x + y + z, COLLECT),
    (Mul(2, x + y) + Mul(3, y + x), 5 * (x + y), COLLECT),
    (x + x * y + x, 2 * x + x * y, COLLECT),
    (x - x, n(0), COLLECT),
    (sin(x) - sin(x), n(0), COLLECT),
    (Add(x, y, Mul(-1, x)), y, COLLECT),
    (Add(x, x, Mul(-1, x)), x, COLLECT),
    (Add(2 * x, Mul(-1, x)), x, COLLECT),
    (sin(x + x), sin(2 * x), COLLECT),
    (cos(Add(y, y, y)), cos(3 * y), COLLECT),
    (Pow(x + x, 2), Pow(2 * x, 2), COLLECT),
    (Mul(x + x, y), 2 * x * y, COLLECT),
    (Mul(sin(x), y + y), 2 * y * sin(x), COLLECT),
    (Lt(x + x, y), Lt(2 * x, y), COLLECT),
    (And(Lt(x, y + y), Lt(z, y)), And(Lt(x, 2 * y), Lt(z, y)), COLLECT),
]


def test_collecting_terms_in_sums_keeps_the_value():
    assert unequal(COLLECTING_IN_SUMS) == []


@pytest.mark.parametrize("e, expected", cases(COLLECTING_IN_SUMS))
def test_collecting_terms_in_sums(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


WITH_IDENTITY_AND_ABSORBING = [
    (Mul(1, x) + x, 2 * x, COLLECT),
    (Add(x, 0, x), 2 * x, COLLECT),
    (Add(x, Mul(1, x), 0), 2 * x, COLLECT),
    (Mul(1, Add(x, x)), 2 * x, COLLECT),
    (x * Add(y, 0) + x * y, 2 * x * y, COLLECT),
    (Add(Mul(3, x), Mul(-2, x)), x, COLLECT),
    (Add(Mul(3, x, y), Mul(-2, y, x), z), x * y + z, COLLECT),
    (Mul(0, x) + x + x, 2 * x, COLLECT),
    (Add(Mul(0, log(y)), x, x), Mul(0, log(y)) + 2 * x, COLLECT),
    (Add(Mul(0, y), 2 * x, 3 * x), 5 * x, COLLECT),
    (Mul(0, x) + x, x, None),
    (2 * x + Mul(0, y + z), 2 * x, None),
    (Mul(0, x + y), n(0), None),
    (Mul(0, sin(x + y), x), n(0), None),
    (Add(x, Mul(y, 0), Mul(1, z)), x + z, None),
]


def test_collecting_with_identity_and_absorbing_elements_keeps_the_value():
    assert unequal(WITH_IDENTITY_AND_ABSORBING) == []


@pytest.mark.parametrize("e, expected", cases(WITH_IDENTITY_AND_ABSORBING))
def test_collecting_with_identity_and_absorbing_elements(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


def test_an_absorbing_element_erases_a_sum_only_where_it_has_a_value():
    e = Mul(0, log(x + y))
    assert shape(normalise(e)) == shape(e)
    assert normalise(e, knowing(Ne(x + y, 0))) == n(0)


SAME_CONDITION_BEFORE_AND_AFTER = [
    (2 * log(y) + 3 * log(y), 5 * log(y), COLLECT),
    (log(y) + log(y), 2 * log(y), COLLECT),
    (log(y) + 2 * log(y), 3 * log(y), COLLECT),
    (Add(log(y), x, log(y)), 2 * log(y) + x, COLLECT),
    (Add(log(x + y), log(y + x)), 2 * log(x + y), COLLECT),
    (log(y) * x + x * log(y), 2 * x * log(y), COLLECT),
    (Add(log(y), log(y), Mul(-1, log(y))), log(y), COLLECT),
    (Add(Mul(3, log(y)), Mul(-2, log(y))), log(y), COLLECT),
]


def test_collecting_terms_with_the_same_condition_keeps_the_value():
    assert unequal(SAME_CONDITION_BEFORE_AND_AFTER) == []


@pytest.mark.parametrize("e, expected", cases(SAME_CONDITION_BEFORE_AND_AFTER))
def test_collecting_terms_with_the_same_condition_needs_nothing_known(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


ONLY_WHEN_KNOWN = [
    (log(y) - log(y), (Ne(y, 0),), n(0), COLLECT),
    (Add(x, log(y), Mul(-1, log(y))), (Ne(y, 0),), x, COLLECT),
    (Add(2 * log(y), Mul(-2, log(y))), (Ne(y, 0),), n(0), COLLECT),
    (Add(log(x), log(y), Mul(-1, log(x))), (Ne(x, 0),), log(y), COLLECT),
    (Add(log(x + y), Mul(-1, log(y + x)), z), (Ne(x + y, 0),), z, COLLECT),
    (Pow(x, 2) * Pow(x, -1), (Ne(x, 0),), x, EXPONENTS),
    (Mul(x, Pow(x, -1), y), (Ne(x, 0),), y, EXPONENTS),
    (Mul(Pow(x, 3), Pow(x, -3)), (Ne(x, 0),), n(1), EXPONENTS),
]


def test_a_rewrite_that_drops_a_condition_keeps_the_value_where_it_holds():
    assert unequal([(e, expected) for e, _, expected, _ in ONLY_WHEN_KNOWN]) == []


@pytest.mark.parametrize(
    "e, expected", pairs([(e, expected) for e, _, expected, _ in ONLY_WHEN_KNOWN]),
)
def test_a_rewrite_that_drops_a_condition_does_not_happen_unless_it_is_known(e, expected):
    __tracebackhide__ = True
    check_different_normal_form(e, expected)


@pytest.mark.parametrize("e, conditions, expected", cases(ONLY_WHEN_KNOWN))
def test_a_rewrite_that_drops_a_condition_happens_when_it_is_known(e, conditions, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected, knowing(*conditions))


MERGING_EXPONENTS = [
    (x * x, Pow(x, 2), EXPONENTS),
    (x * x * x, Pow(x, 3), EXPONENTS),
    (Mul(x, Mul(x, x)), Pow(x, 3), EXPONENTS),
    (Pow(x, 2) * Pow(x, 3), Pow(x, 5), EXPONENTS),
    (x * Pow(x, 2), Pow(x, 3), EXPONENTS),
    (Pow(x, 2) * x, Pow(x, 3), EXPONENTS),
    (Mul(x, y, x), Pow(x, 2) * y, EXPONENTS),
    (Mul(2, x, x), 2 * Pow(x, 2), EXPONENTS),
    (Mul(x, y, x, y), Pow(x, 2) * Pow(y, 2), EXPONENTS),
    (Mul(x * y, y * x), Pow(x, 2) * Pow(y, 2), EXPONENTS),
    (Mul(Pow(x, 2), y, Mul(x, Pow(y, 3))), Pow(x, 3) * Pow(y, 4), EXPONENTS),
    (sin(x) * sin(x), Pow(sin(x), 2), EXPONENTS),
    (Mul(x + y, y + x), Pow(x + y, 2), EXPONENTS),
    (log(y) * log(y), Pow(log(y), 2), EXPONENTS),
    (Pow(x, -1) * Pow(x, -1), Pow(x, -2), EXPONENTS),
    (Mul(x, Pow(x, -1), Pow(x, -1)), Pow(x, -1), EXPONENTS),
    (Pow(x, -2) * Pow(x, 3), x, EXPONENTS),
    (Mul(Pow(x, -1), Pow(x, 2), y), x * y, EXPONENTS),
    (Pow(x * x, 2), Pow(Pow(x, 2), 2), EXPONENTS),
    (sin(x * x), sin(Pow(x, 2)), EXPONENTS),
    (x * x + x * x, 2 * Pow(x, 2), EXPONENTS),
    (Pow(x, 2) + x * x, 2 * Pow(x, 2), EXPONENTS),
    (Mul(Mul(1, x), x), Pow(x, 2), EXPONENTS),
]


def test_merging_exponents_keeps_the_value():
    assert unequal(MERGING_EXPONENTS) == []


@pytest.mark.parametrize("e, expected", cases(MERGING_EXPONENTS))
def test_merging_exponents(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


EVERY_WRITING = [
    (Add(x, x, y), 2 * x + y, COLLECT),
    (Add(2 * x, y, 3 * x), 5 * x + y, COLLECT),
    (Add(x * y, z, y * x), 2 * x * y + z, COLLECT),
    (Add(x, Mul(-1, x), y, 2 * y), 3 * y, COLLECT),
    (Add(sin(x), 0, sin(x)), 2 * sin(x), COLLECT),
    (Mul(x, y, x), Pow(x, 2) * y, EXPONENTS),
    (Mul(Pow(x, 2), y, x), Pow(x, 3) * y, EXPONENTS),
    (Mul(x, 1, x, 2), 2 * Pow(x, 2), EXPONENTS),
]


def test_every_writing_keeps_the_value():
    assert unequal(EVERY_WRITING) == []


@pytest.mark.parametrize("e, expected", cases(EVERY_WRITING))
def test_every_order_and_bracketing_collects_to_one_normal_form(e, expected):
    __tracebackhide__ = True
    for writing in every_writing(e.head, list(e.args)):
        check_same_normal_form(writing, expected)


AND_OR_ABSORPTION = [
    (And(p, Or(p, q)), p, ABSORPTION),
    (Or(p, And(p, q)), p, ABSORPTION),
    (And(p, Or(q, p, r)), p, ABSORPTION),
    (Or(And(q, p, r), p), p, ABSORPTION),
    (Or(p, And(p, q), And(r, p)), p, ABSORPTION),
    (And(p, Or(p, q), Or(r, p)), p, ABSORPTION),
    (And(p, q, Or(p, r)), And(p, q), ABSORPTION),
    (Or(p, q, And(q, r)), Or(p, q), ABSORPTION),
    (Or(And(p, q), And(q, p, r)), And(p, q), ABSORPTION),
    (And(Or(p, q), Or(q, r, p)), Or(p, q), ABSORPTION),
    (And(p, Or(p, q), true), p, ABSORPTION),
    (Or(p, And(p, q), false), p, ABSORPTION),
    (And(p, Or(false, p, q)), p, ABSORPTION),
    (Or(And(p, true), And(p, q)), p, ABSORPTION),
    (And(Or(p, And(p, q)), r), And(p, r), ABSORPTION),
    (Or(q, And(Or(p, q), q)), q, ABSORPTION),
    (And(p, Or(And(p, q), p)), p, ABSORPTION),
    (And(p, Or(p, true)), p, None),
    (Or(p, And(q, false)), p, None),
    (Or(And(p, Or(q, true)), p), p, None),
    (Not(And(p, Or(p, q))), Not(p), ABSORPTION),
]


def test_and_or_absorption_keeps_the_value():
    assert unequal(AND_OR_ABSORPTION) == []


@pytest.mark.parametrize("e, expected", cases(AND_OR_ABSORPTION))
def test_and_or_absorption(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


NEITHER_SIDE_SMALLER = [
    (Or(And(p, q), And(p, r)), And(p, Or(q, r))),
    (And(Or(p, q), Or(p, r)), Or(p, And(q, r))),
    (Or(And(p, q), And(p, r), And(p, Not(q))), And(p, Or(q, r, Not(q)))),
    (DistUnion(DistInter(a, b), DistInter(a, c)), DistInter(a, DistUnion(b, c))),
    (DistInter(DistUnion(a, b), DistUnion(a, c)), DistUnion(a, DistInter(b, c))),
    (DistAlt(DistCat(s, t), DistCat(s, w)), DistCat(s, DistAlt(t, w))),
    (DistAlt(DistCat(t, s), DistCat(w, s)), DistCat(DistAlt(t, w), s)),
    (DistMax(DistPlus(x, y), DistPlus(x, z)), DistPlus(x, DistMax(y, z))),
    (DistVAdd(DistScale(j, v), DistScale(k, v)), DistScale(j + k, v)),
    (DistVAdd(DistScale(k, u), DistScale(k, v)), DistScale(k, DistVAdd(u, v))),
    (x * y + x * z, x * (y + z)),
    (2 * x + 2 * y, 2 * (x + y)),
    (Add(x, y, 2 * (x + y)), 3 * (x + y)),
]


def test_a_distributed_and_a_factored_form_are_equal_in_value():
    assert unequal(NEITHER_SIDE_SMALLER) == []


def test_normalising_either_form_keeps_its_value():
    forms = [form for pair in NEITHER_SIDE_SMALLER for form in pair]
    assert unequal([(normalise(e), e) for e in forms]) == []


SETS = [
    (DistUnion(a, DistInter(a, b)), a, ABSORPTION),
    (DistInter(a, DistUnion(a, b)), a, ABSORPTION),
    (DistUnion(a, DistInter(b, a, c)), a, ABSORPTION),
    (DistInter(a, DistUnion(b, a), DistUnion(a, c)), a, ABSORPTION),
    (DistUnion(DistInter(a, b), DistInter(b, a, c)), DistInter(a, b), ABSORPTION),
    (DistUnion(a, DistInter(a, b), dist_empty), a, ABSORPTION),
    (DistInter(dist_everything, a, DistUnion(dist_empty, a, b)), a, ABSORPTION),
    (DistUnion(b, DistInter(DistUnion(a, b), b)), b, ABSORPTION),
    (DistUnion(DistInter(a, b), DistInter(b, a)), DistInter(a, b), None),
    (DistUnion(a, DistInter(dist_everything, a)), a, None),
    (DistInter(a, DistUnion(b, dist_everything)), a, None),
    (DistUnion(a, DistInter(b, dist_empty)), a, None),
    (DistInter(DistUnion(a, b), DistUnion(b, a, dist_empty)), DistUnion(a, b), None),
]


def test_union_and_intersection_keep_the_value():
    assert unequal(SETS) == []


@pytest.mark.parametrize("e, expected", cases(SETS))
def test_union_and_intersection_distribute_over_each_other(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


MAX_PLUS = [
    (DistMax(DistPlus(2, x), DistPlus(3, x)), DistPlus(3, x), COLLECT),
    (DistMax(x, DistPlus(2, x)), DistPlus(2, x), COLLECT),
    (DistMax(x, DistPlus(-1, x)), x, COLLECT),
    (DistMax(DistPlus(2, x, y), DistPlus(y, 3, x)), DistPlus(3, x, y), COLLECT),
    (DistMax(DistPlus(2, x), z, DistPlus(x, 5)), DistMax(DistPlus(5, x), z), COLLECT),
    (DistMax(DistPlus(x, 0), x), x, None),
    (DistMax(DistPlus(x, y), DistPlus(y, x)), DistPlus(x, y), None),
    (DistPlus(DistMax(x, x), y), DistPlus(x, y), None),
]


def test_plus_over_max_keeps_the_value():
    assert unequal(MAX_PLUS) == []


@pytest.mark.parametrize("e, expected", cases(MAX_PLUS))
def test_plus_distributes_over_max(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


LANGUAGES = [
    (DistCat(s, DistAlt(t, t)), DistCat(s, t), None),
    (DistAlt(DistCat(s, t), DistCat(s, t)), DistCat(s, t), None),
    (DistCat(s, DistAlt(), t), dist_none, None),
    (DistCat(s, DistAlt(dist_none, t)), DistCat(s, t), None),
    (DistAlt(DistCat(s, dist_eps, t), DistCat(s, t)), DistCat(s, t), None),
    (DistCat(DistAlt(t, w), DistAlt(w, t)), DistCat(DistAlt(t, w), DistAlt(t, w)), None),
]


def test_concatenation_and_alternation_keep_the_value():
    assert unequal(LANGUAGES) == []


@pytest.mark.parametrize("e, expected", cases(LANGUAGES))
def test_concatenation_with_alternation(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


VECTORS = [
    (DistVAdd(DistScale(2, v), DistScale(3, v)), DistScale(5, v), COLLECT),
    (DistVAdd(v, v), DistScale(2, v), COLLECT),
    (DistVAdd(v, DistScale(2, v)), DistScale(3, v), COLLECT),
    (DistVAdd(DistScale(2, v), u, DistScale(-1, v)), DistVAdd(u, v), COLLECT),
    (DistVAdd(DistScale(x + x, v), u), DistVAdd(DistScale(2 * x, v), u), COLLECT),
    (DistVAdd(DistScale(2, v), dist_origin, DistScale(3, v)), DistScale(5, v), COLLECT),
    (DistScale(Mul(0, x), v), DistScale(0, v), None),
    (DistVAdd(u, dist_origin), u, None),
]


def test_scaling_vectors_keeps_the_value():
    assert unequal(VECTORS) == []


@pytest.mark.parametrize("e, expected", cases(VECTORS))
def test_scaling_distributes_over_adding_vectors(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


MUST_STAY = [
    2 * (x + y),
    x * (y + z),
    Mul(2, x + y, z),
    sin(x) * (x + y),
    (x + y) * (x - y),
    2 + x * y,
    x + y,
    2 * x + 3 * y,
    x * y + x * z,
    x * y + y * z,
    x + x * y,
    x * y + Mul(x, y, z),
    2 * x + 2 * y,
    Pow(x, 2) + x,
    sin(x) + cos(x),
    sin(x) + sin(y),
    sin(2 * x) + sin(x),
    Pow(x, 2) * Pow(y, 3),
    Pow(2, x) * Pow(3, x),
    Pow(x, y) * Pow(z, y),
    Pow(x + y, 2),
    Pow(x, y + z),
    Mul(x, y) + Mul(x, Pow(y, 2)),
    DistPlus(2, DistMax(x, y)),
    DistMax(2, DistPlus(x, y)),
    DistMax(DistPlus(2, x), DistPlus(3, y)),
    DistUnion(a, DistInter(b, c)),
    DistCat(s, DistAlt(t, w)),
    DistCat(DistAlt(t, w), s),
    DistAlt(DistCat(s, t), DistCat(t, s)),
    DistScale(2, DistVAdd(u, v)),
    DistScale(j + k, v),
    DistVAdd(DistScale(2, u), DistScale(3, v)),
    And(p, Or(q, r)),
    Or(p, And(q, r)),
]


@pytest.mark.parametrize("e", [pytest.param(e, id=repr(e)) for e in MUST_STAY])
def test_must_stay_as_it_is(e):
    __tracebackhide__ = True
    check_shape_kept(e)


NOT_EXPANDED_BY_NORMALISE = [
    ((x + y) * (x + y), x * x + x * y + y * x + y * y),
    ((x + y) * (x + y), Pow(x, 2) + 2 * x * y + Pow(y, 2)),
    (2 * (x + y), 2 * x + 2 * y),
    (x * (y + z), x * y + x * z),
    (Pow(x, 2) * (x + 1), Pow(x, 3) + Pow(x, 2)),
    (DistPlus(2, DistMax(x, y)), DistMax(DistPlus(2, x), DistPlus(2, y))),
    (DistInter(a, DistUnion(b, c)), DistUnion(DistInter(a, b), DistInter(a, c))),
    (DistCat(s, DistAlt(t, w)), DistAlt(DistCat(s, t), DistCat(s, w))),
    (DistScale(2, DistVAdd(u, v)), DistVAdd(DistScale(2, u), DistScale(2, v))),
    (DistScale(j + k, v), DistVAdd(DistScale(j, v), DistScale(k, v))),
]


def test_an_expansion_has_the_same_value():
    assert unequal(NOT_EXPANDED_BY_NORMALISE) == []


@pytest.mark.parametrize("e, expanded", pairs(NOT_EXPANDED_BY_NORMALISE))
def test_normalise_does_not_expand(e, expanded):
    __tracebackhide__ = True
    check_different_normal_form(e, expanded)


MUST_NOT_BECOME = [
    (2 + x * y, (2 + x) * (2 + y)),
    (DistMax(2, DistPlus(x, y)), DistPlus(DistMax(2, x), DistMax(2, y))),
    (DistAlt(DistCat(s, w), DistCat(t, w)), DistCat(w, DistAlt(s, t))),
    (DistAlt(DistCat(w, s), DistCat(w, t)), DistCat(DistAlt(s, t), w)),
    (DistCat(s, t), DistCat(t, s)),
    (DistAlt(DistCat(s, t), DistCat(t, s)), DistCat(s, t)),
    (DistScale(2, DistVAdd(u, v)), DistVAdd(DistScale(2, u), v)),
    (x * y + y, 2 * x * y),
    (Pow(x, 2) * Pow(y, 2), Pow(x, 4)),
    (Pow(2, x) * Pow(3, x), Pow(5, x)),
    (Pow(x, 2) * Pow(x, 3), Pow(x, 6)),
    (Or(p, And(q, r)), And(Or(p, q), r)),
]


def test_a_form_it_must_not_become_differs_in_value():
    assert unequal(MUST_NOT_BECOME) == MUST_NOT_BECOME


@pytest.mark.parametrize("e, wrong", pairs(MUST_NOT_BECOME))
def test_must_not_become(e, wrong):
    __tracebackhide__ = True
    check_different_normal_form(e, wrong)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=POWER_DOMAIN)
def test_zero_times_a_power_with_a_positive_integer_exponent_is_zero():
    __tracebackhide__ = True
    check_same_normal_form(Mul(0, Pow(x, 2)), n(0))


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=POWER_DOMAIN)
def test_zero_times_a_reciprocal_is_zero_when_the_base_is_known_to_be_nonzero():
    __tracebackhide__ = True
    check_same_normal_form(Mul(0, Pow(x, -1)), n(0), knowing(Ne(x, 0)))

import cmath
from fractions import Fraction
from functools import reduce

import pytest

from distributivity_support import (
    cases, check_different_normal_form, check_same_normal_form, check_shape_kept, knowing, pairs,
    unequal_pairs,
)
from nary import (
    Add, BoolKind, Gt, Many, Mul, Ne, NumberKind, Pow, declare_constant, declare_function,
    declare_kind, exp, log, sin,
)
from nary.logic import And, Not, Or, false, true
from nary.normalising import normalise
from nary.property_steps import step
from nary.properties import declare_properties, declare_property, is_property

if not is_property("distributes_over"):
    declare_property("distributes_over")

NUMBERS = "numbers are not added or multiplied"
COLLECT = "like terms are not collected"
INVERSES = "inverses do not cancel"
SIGN = "undecided: -1 is not distributed over a sum"
POW = "Pow laws are not applied"
PASS_THROUGH = "a function is not passed through an operation"
INVERSE_FUNCTION = "a function and its inverse do not cancel"
INVOLUTION = "an involution is not undone"
COMPLEMENT = "complements do not cancel"
DE_MORGAN = "De Morgan is not applied"
CONDITION = "a step cannot ask for a condition"
CANCEL_BY_DISTRIBUTING = "a product is not distributed to cancel terms"

x, y, z = (NumberKind(name) for name in "xyz")
p, q, r = (BoolKind(name) for name in "pqr")
n = NumberKind

declare_property("soon_passes_through")
declare_property("is_soon_involution")
declare_property("is_soon_cancelled_in_pairs")


@step("is_soon_cancelled_in_pairs", per_argument=True)
def _cancel_in_pairs(arg, copies):
    return copies % 2


SoonMat = declare_kind("SoonMat")
soon_zero_mat = declare_constant("soon_zero_mat", SoonMat)
SoonMAdd = declare_function("SoonMAdd", Many(SoonMat), returns=SoonMat, domain=true)
declare_properties(
    SoonMAdd, is_associative=True, is_commutative=True, identity_element=soon_zero_mat,
)
SoonT = declare_function("SoonT", SoonMat, returns=SoonMat, domain=true)
declare_properties(SoonT, soon_passes_through=SoonMAdd, is_soon_involution=True)
A, B, C = (SoonMat(name) for name in "ABC")

SoonPoly = declare_kind("SoonPoly")
soon_zero_poly = declare_constant("soon_zero_poly", SoonPoly)
SoonPAdd = declare_function("SoonPAdd", Many(SoonPoly), returns=SoonPoly, domain=true)
declare_properties(
    SoonPAdd, is_associative=True, is_commutative=True, identity_element=soon_zero_poly,
)
SoonD = declare_function("SoonD", SoonPoly, returns=SoonPoly, domain=true)
declare_properties(SoonD, soon_passes_through=SoonPAdd)
f, g, h = (SoonPoly(name) for name in "fgh")

soon_neg = declare_function("soon_neg", NumberKind, returns=NumberKind, domain=true)
declare_properties(soon_neg, is_soon_involution=True)

SoonXor = declare_function("SoonXor", Many(BoolKind), returns=BoolKind, domain=true)
declare_properties(
    SoonXor, is_associative=True, is_commutative=True, identity_element=false,
    is_soon_cancelled_in_pairs=True,
)
SoonMeet = declare_function("SoonMeet", Many(BoolKind), returns=BoolKind, domain=true)
declare_properties(
    SoonMeet, is_associative=True, is_commutative=True, identity_element=true,
    absorbing_element=false, is_idempotent=True, distributes_over=SoonXor,
)


def _power(base, exponent):
    if isinstance(exponent, Fraction) and exponent.denominator == 1:
        return base ** int(exponent)
    return complex(base) ** complex(exponent)


def _product(*factors):
    return reduce(lambda left, right: left * right, factors, Fraction(1))


def _matrix_sum(*matrices):
    zero = ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0)))
    return reduce(
        lambda m, k: tuple(tuple(a + b for a, b in zip(rm, rk)) for rm, rk in zip(m, k)),
        matrices, zero,
    )


MODEL = {
    Add: lambda *terms: sum(terms, Fraction(0)),
    Mul: _product,
    Pow: _power,
    sin: lambda e: cmath.sin(complex(e)),
    exp: lambda e: cmath.exp(complex(e)),
    log: lambda e: cmath.log(complex(e)),
    And: lambda *args: all(args),
    Or: lambda *args: any(args),
    Not: lambda arg: not arg,
    true: True,
    false: False,
    SoonMAdd: _matrix_sum,
    soon_zero_mat: _matrix_sum(),
    SoonT: lambda m: tuple(zip(*m)),
    SoonPAdd: lambda *polys: tuple(sum(cs, Fraction(0)) for cs in zip((0, 0, 0), *polys)),
    soon_zero_poly: (Fraction(0),) * 3,
    SoonD: lambda poly: (poly[1], 2 * poly[2], Fraction(0)),
    soon_neg: lambda e: -e,
    SoonXor: lambda *args: sum(args) % 2 == 1,
    SoonMeet: lambda *args: all(args),
}

NONZERO = [Fraction(-3), Fraction(-1, 2), Fraction(1, 3), Fraction(2), Fraction(5, 2), Fraction(7)]
POSITIVE = [Fraction(1, 3), Fraction(1, 2), Fraction(2), Fraction(5, 2), Fraction(3), Fraction(7)]


def _sample_from(numbers):
    def sample(kind, rng):
        if kind == NumberKind:
            return rng.choice(numbers)
        if kind == SoonMat:
            return tuple(tuple(rng.choice(numbers) for _ in range(2)) for _ in range(2))
        if kind == SoonPoly:
            return tuple(rng.choice(numbers) for _ in range(3))
        raise ValueError(f"no values for {kind!r}")

    return sample


def unequal(table, numbers=NONZERO):
    return unequal_pairs(table, MODEL, _sample_from(numbers))


NUMBER_ARITHMETIC = [
    (Add(2, x, 3), x + 5, NUMBERS),
    (Mul(2, x, 3), 6 * x, NUMBERS),
    (Add(1, Add(x, 1)), x + 2, NUMBERS),
    (Add(-1, x, 1), x, NUMBERS),
    (Add(x, 3, -3), x, NUMBERS),
    (Add(-2, 2), n(0), NUMBERS),
    (Add(5, Mul(-1, 5)), n(0), NUMBERS),
    (Mul(-1, -1), n(1), NUMBERS),
    (Mul(2, 3, 4), n(24), NUMBERS),
    (Add(1, 2, 3, 4), n(10), NUMBERS),
    (Mul(2, Add(3, 4)), n(14), NUMBERS),
    (Add(Mul(2, 3), 4), n(10), NUMBERS),
    (Add(x, Mul(2, 3)), x + 6, NUMBERS),
    (Mul(2, x, -1), Mul(-2, x), NUMBERS),
    (sin(Add(1, 1)), sin(2), NUMBERS),
    (Pow(2, Add(1, 2)), Pow(2, 3), NUMBERS),
    (Mul(Add(2, 3), x), 5 * x, NUMBERS),
    (Mul(Add(1, 1), x, y), 2 * x * y, NUMBERS),
    (Mul(Add(2, -2), x), n(0), NUMBERS),
    (Mul(Add(3, -3), sin(x)), n(0), NUMBERS),
    (Mul(Add(2, -2), log(y)), Mul(0, log(y)), NUMBERS),
    (Add(Mul(2, 3, x), x), 7 * x, NUMBERS),
    (Add(Mul(-1, 2, x), Mul(5, x)), 3 * x, NUMBERS),
    (Add(2, 3) * x + Mul(-5, x), n(0), NUMBERS),
    (Add(Mul(0, 7), x), x, None),
    (Mul(Mul(1, 1), x), x, None),
]


def test_number_arithmetic_keeps_the_value():
    assert unequal(NUMBER_ARITHMETIC) == []


@pytest.mark.parametrize("e, expected", cases(NUMBER_ARITHMETIC))
def test_number_arithmetic(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


NEGATION = [
    (2 * x - 2 * x, n(0), NUMBERS),
    (x - 2 * x, -x, NUMBERS),
    (-(-x), x, NUMBERS),
    (Add(-(-x), Mul(-1, x)), n(0), NUMBERS),
    (2 * (x + y) - 2 * (x + y), n(0), NUMBERS),
    (x + y - x, y, COLLECT),
    (Add(x, Mul(-1, y), y), x, COLLECT),
    (Mul(-1, x) + Mul(-1, x), Mul(-2, x), COLLECT),
    (Add(Mul(3, x), Mul(-1, x), Mul(-1, x), Mul(-1, x)), n(0), COLLECT),
    (Mul(-1, x + y) + Mul(-1, y + x), Mul(-2, x + y), COLLECT),
    (Add(sin(x), y, Mul(-1, sin(x)), Mul(-1, y)), n(0), COLLECT),
    (x + y - (x + y), n(0), SIGN),
    (Add(Mul(-1, Add(x, y)), y, x), n(0), SIGN),
    (Add(x, Mul(-1, Add(x, y))), -y, SIGN),
    (Add(Mul(-1, x), Mul(-1, y), x + y), n(0), SIGN),
]


def test_negation_keeps_the_value():
    assert unequal(NEGATION) == []


@pytest.mark.parametrize("e, expected", cases(NEGATION))
def test_negation(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


POW_LAWS = [
    (Pow(x, 1), x, POW),
    (Pow(x + y, 1), x + y, POW),
    (Pow(1, x), n(1), POW),
    (Pow(Pow(x, 2), 3), Pow(x, 6), POW),
    (Pow(Pow(x, -1), 2), Pow(x, -2), POW),
    (Pow(Pow(x, 2), -1), Pow(x, -2), POW),
    (Pow(2, x) * Pow(2, y), Pow(2, x + y), POW),
    (Mul(Pow(3, x), Pow(3, Mul(-1, x))), n(1), POW),
    (Pow(Mul(x, y), 2), Pow(x, 2) * Pow(y, 2), POW),
    (Pow(Mul(2, x), 2), Mul(4, Pow(x, 2)), POW),
    (Pow(x, 2) * Pow(y, 2) * Pow(z, 2), Pow(x * y * z, 2), POW),
    (Pow(Pow(x, y), 2), Pow(x, 2 * y), POW),
]


def test_pow_laws_keep_the_value():
    assert unequal(POW_LAWS) == []


@pytest.mark.parametrize("e, expected", cases(POW_LAWS))
def test_pow_laws(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


FUNCTIONS_THROUGH_OPERATIONS = [
    (exp(x) * exp(y), exp(x + y), PASS_THROUGH),
    (Mul(exp(x), exp(y), exp(z)), exp(x + y + z), PASS_THROUGH),
    (exp(x) * exp(x), exp(2 * x), PASS_THROUGH),
    (Pow(exp(x), 2), exp(2 * x), PASS_THROUGH),
    (exp(x) * exp(Mul(-1, x)), n(1), PASS_THROUGH),
    (Mul(exp(x), exp(y), exp(Mul(-1, y))), exp(x), PASS_THROUGH),
    (SoonT(SoonMAdd(A, B)), SoonMAdd(SoonT(A), SoonT(B)), PASS_THROUGH),
    (SoonT(SoonMAdd(A, B, C)), SoonMAdd(SoonT(A), SoonT(B), SoonT(C)), PASS_THROUGH),
    (SoonT(SoonMAdd(SoonT(A), SoonT(B))), SoonMAdd(A, B), PASS_THROUGH),
    (SoonT(SoonMAdd(A, SoonT(B))), SoonMAdd(SoonT(A), B), PASS_THROUGH),
    (SoonD(SoonPAdd(f, g)), SoonPAdd(SoonD(f), SoonD(g)), PASS_THROUGH),
    (SoonD(SoonPAdd(f, SoonD(g))), SoonPAdd(SoonD(f), SoonD(SoonD(g))), PASS_THROUGH),
    (SoonPAdd(SoonD(SoonPAdd(f, g)), SoonD(h)), SoonD(SoonPAdd(f, g, h)), PASS_THROUGH),
    (SoonT(SoonT(A)), A, INVOLUTION),
    (SoonT(SoonT(SoonT(A))), SoonT(A), INVOLUTION),
    (SoonMAdd(SoonT(SoonT(A)), B), SoonMAdd(A, B), INVOLUTION),
    (soon_neg(soon_neg(x)), x, INVOLUTION),
    (soon_neg(soon_neg(x)) + y, x + y, INVOLUTION),
    (SoonT(SoonMAdd(A, soon_zero_mat)), SoonT(A), None),
    (SoonT(SoonMAdd(B, A)), SoonT(SoonMAdd(A, B)), None),
    (SoonD(SoonPAdd(f, soon_zero_poly)), SoonD(f), None),
]


def test_functions_through_operations_keep_the_value():
    assert unequal(FUNCTIONS_THROUGH_OPERATIONS) == []


@pytest.mark.parametrize("e, expected", cases(FUNCTIONS_THROUGH_OPERATIONS))
def test_functions_through_operations(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


AND_OR_WITH_NOT = [
    (And(p, Not(p)), false, COMPLEMENT),
    (Or(p, Not(p)), true, COMPLEMENT),
    (And(p, q, Not(p)), false, COMPLEMENT),
    (Or(q, Not(p), p), true, COMPLEMENT),
    (And(Not(p), Or(q, r), p), false, COMPLEMENT),
    (Not(true), false, COMPLEMENT),
    (Not(false), true, COMPLEMENT),
    (Not(Not(p)), p, INVOLUTION),
    (Not(Not(Not(p))), Not(p), INVOLUTION),
    (And(Not(Not(p)), q), And(p, q), INVOLUTION),
    (Not(And(p, q)), Or(Not(p), Not(q)), DE_MORGAN),
    (Not(Or(p, q)), And(Not(p), Not(q)), DE_MORGAN),
    (Not(And(p, q, r)), Or(Not(p), Not(q), Not(r)), DE_MORGAN),
    (Not(Or(p, Not(q))), And(Not(p), q), DE_MORGAN),
    (And(p, Or(Not(p), q)), And(p, q), COMPLEMENT),
    (Or(p, And(Not(p), q)), Or(p, q), COMPLEMENT),
    (And(Or(p, q), Or(Not(p), q)), q, COMPLEMENT),
    (Or(And(p, q), And(Not(p), q)), q, COMPLEMENT),
    (Or(And(p, Not(q)), And(p, q)), p, COMPLEMENT),
    (Or(And(p, q), Not(p)), Or(q, Not(p)), COMPLEMENT),
    (And(Or(p, q), Not(p)), And(q, Not(p)), COMPLEMENT),
    (And(p, Not(And(p, q))), And(p, Not(q)), DE_MORGAN),
    (Or(p, Not(Or(p, q))), Or(p, Not(q)), DE_MORGAN),
    (And(p, Not(Or(p, q))), false, DE_MORGAN),
    (And(p, Not(q), Not(q)), And(p, Not(q)), None),
    (Or(Not(p), false), Not(p), None),
    (And(Not(p), Or(Not(p), q)), Not(p), "absorption is not derived"),
]


def test_and_or_with_not_keep_the_value():
    assert unequal(AND_OR_WITH_NOT) == []


@pytest.mark.parametrize("e, expected", cases(AND_OR_WITH_NOT))
def test_and_or_with_not(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


ONLY_WHEN_KNOWN = [
    (x / x, (Ne(x, 0),), n(1), INVERSES),
    (x * y / x, (Ne(x, 0),), y, INVERSES),
    (Mul(2, x, Pow(x, -1)), (Ne(x, 0),), n(2), INVERSES),
    (Mul(x, x, Pow(x, -1)), (Ne(x, 0),), x, INVERSES),
    (sin(x) / sin(x), (Ne(sin(x), 0),), n(1), INVERSES),
    (log(y) / log(y), (Ne(y, 0), Ne(log(y), 0)), n(1), INVERSES),
    (Mul(Pow(x, -1), Pow(y, -1), y), (Ne(y, 0),), Pow(x, -1), INVERSES),
    (Pow(x, 0), (Ne(x, 0),), n(1), POW),
    (Pow(Pow(x, -1), -1), (Ne(x, 0),), x, POW),
    (Pow(x, y) * Pow(x, z), (Ne(x, 0),), Pow(x, y + z), POW),
    (Pow(x, 2) * Pow(x, y), (Ne(x, 0),), Pow(x, y + 2), POW),
    (Pow(x, y) * Pow(x, Mul(-1, y)), (Ne(x, 0),), n(1), POW),
    (exp(log(x)), (Ne(x, 0),), x, INVERSE_FUNCTION),
    (exp(log(x)) + exp(log(x)), (Ne(x, 0),), 2 * x, INVERSE_FUNCTION),
    (log(x) + log(y), (Gt(x, 0), Gt(y, 0)), log(x * y), CONDITION),
    (Pow(Mul(x, y), z), (Gt(x, 0), Gt(y, 0)), Pow(x, z) * Pow(y, z), CONDITION),
    (Pow(Pow(x, y), z), (Gt(x, 0),), Pow(x, y * z), CONDITION),
]


def test_a_rewrite_that_needs_a_condition_keeps_the_value_where_it_holds():
    table = [(e, expected) for e, _, expected, _ in ONLY_WHEN_KNOWN]
    assert unequal(table, POSITIVE) == []


@pytest.mark.parametrize(
    "e, expected", pairs([(e, expected) for e, _, expected, _ in ONLY_WHEN_KNOWN]),
)
def test_a_rewrite_that_needs_a_condition_does_not_happen_unless_it_is_known(e, expected):
    __tracebackhide__ = True
    check_different_normal_form(e, expected)


@pytest.mark.parametrize("e, conditions, expected", cases(ONLY_WHEN_KNOWN))
def test_a_rewrite_that_needs_a_condition_happens_when_it_is_known(e, conditions, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected, knowing(*conditions))


REPEATS_THAT_CANCEL_IN_PAIRS = [
    (SoonXor(p, p), false, None),
    (SoonXor(SoonMeet(p, q), SoonMeet(q, p)), false, None),
    (SoonMeet(SoonXor(p, p), q), false, None),
    (SoonXor(SoonMeet(p, q), r, SoonMeet(q, p)), r, None),
    (SoonMeet(SoonXor(p, q), SoonXor(q, p)), SoonXor(p, q), None),
    (SoonXor(SoonMeet(p, SoonXor(q, q)), r), r, None),
    (SoonXor(SoonMeet(p, q), SoonMeet(q, p), SoonMeet(p, q)), SoonMeet(p, q), None),
    (SoonMeet(p, p, SoonXor(q, q, q)), SoonMeet(p, q), None),
    (SoonMeet(p, SoonXor(p, true)), false, CANCEL_BY_DISTRIBUTING),
    (SoonMeet(SoonXor(p, true), SoonXor(p, q, true), p), false, CANCEL_BY_DISTRIBUTING),
    (SoonXor(SoonMeet(p, SoonXor(q, r)), SoonMeet(p, q)), SoonMeet(p, r), CANCEL_BY_DISTRIBUTING),
]


def test_repeats_that_cancel_in_pairs_keep_the_value():
    assert unequal(REPEATS_THAT_CANCEL_IN_PAIRS) == []


@pytest.mark.parametrize("e, expected", cases(REPEATS_THAT_CANCEL_IN_PAIRS))
def test_a_head_distributing_over_one_whose_repeats_cancel_in_pairs(e, expected):
    __tracebackhide__ = True
    check_same_normal_form(e, expected)


UNDECIDED = [
    (Add(x, y, Mul(-1, Add(x, y))), n(0)),
    (Pow(x, y) * Pow(x, y), Pow(x, 2 * y)),
    (Pow(x, y) * Pow(x, y), Pow(Pow(x, y), 2)),
    (Add(x, y, 2 * (x + y)), 3 * (x + y)),
    (SoonXor(p, SoonMeet(p, q)), SoonMeet(p, SoonXor(q, true))),
]


def test_undecided_pairs_are_equal_in_value():
    assert unequal(UNDECIDED) == []


MUST_STAY = [
    log(x) + log(y),
    log(x * y),
    Pow(x * y, z),
    Pow(Pow(x, y), z),
    exp(x) + exp(y),
    x / y,
    x - y,
    And(p, Not(q)),
    Or(p, Not(q)),
    SoonMeet(p, SoonXor(q, r)),
    SoonXor(p, SoonMeet(q, r)),
]


@pytest.mark.parametrize("e", [pytest.param(e, id=repr(e)) for e in MUST_STAY])
def test_must_stay_as_it_is(e):
    __tracebackhide__ = True
    check_shape_kept(e)


MUST_NOT_BECOME = [
    (log(x) + log(y), log(x * y)),
    (log(x) + log(x), log(Pow(x, 2))),
    (Pow(Mul(x, y), z), Pow(x, z) * Pow(y, z)),
    (Pow(Pow(x, 2), y), Pow(x, 2 * y)),
    (exp(x) + exp(y), exp(x + y)),
    (Not(And(p, q)), And(Not(p), Not(q))),
    (SoonXor(p, SoonMeet(p, q)), p),
    (SoonMeet(p, SoonXor(q, r)), SoonXor(SoonMeet(p, q), r)),
]


def test_a_form_it_must_not_become_differs_in_value():
    assert unequal(MUST_NOT_BECOME) == MUST_NOT_BECOME


@pytest.mark.parametrize("e, wrong", pairs(MUST_NOT_BECOME))
def test_must_not_become(e, wrong):
    __tracebackhide__ = True
    check_different_normal_form(e, wrong)

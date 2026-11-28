from collections import Counter
from itertools import permutations

import pytest

import nary as nr
from nary import Many, Ne, NumberKind, Pow, declare_function, exp, log, sin, tan
from nary.calculus import NumberFunction
from nary.logic import And, Not, Or, false, true
from nary.normalising import normalise
from nary.properties import declare_properties

x, y, z = (NumberKind(name) for name in "xyz")
p, q = nr.BoolKind("p"), nr.BoolKind("q")

Max = declare_function("Max", Many(NumberKind), returns=NumberKind, domain=true)
declare_properties(Max, is_associative=True, is_commutative=True, is_idempotent=True)

Cat = declare_function("Cat", Many(NumberKind), returns=NumberKind, domain=true)
declare_properties(
    Cat, is_associative=True, identity_element=0, absorbing_element=9, is_idempotent=True,
)

Hcf = declare_function("Hcf", NumberKind, NumberKind, returns=NumberKind, domain=true)
declare_properties(
    Hcf, is_commutative=True, identity_element=0, absorbing_element=1, is_idempotent=True,
)

Sym = declare_function("Sym", Many(NumberKind), returns=NumberKind, domain=true)
declare_properties(Sym, is_commutative=True, identity_element=0, is_idempotent=True)


def same(e, expected, known=None):
    expected = expected if isinstance(expected, nr.Expr) else NumberKind(expected)
    return normalise(e, known) == normalise(expected)


@pytest.mark.parametrize("e, expected", [
    (x + (y + x) + 0, nr.Add(x, x, y)),
    (z * (y * 1) * x, nr.Mul(x, y, z)),
    (nr.Add(3, 2), nr.Add(2, 3)),
    (nr.Add(), 0),
    (nr.Mul(x), x),
    (nr.Mul(1, 1), 1),
    (x * 0 * y, 0),
    (nr.Mul(0, 2), 0),
    (And(q, Or(p, false), q, true), And(p, q)),
    (Or(p, true, q), true),
    (And(p, false), false),
    (Or(p, Or(q, p)), Or(p, q)),
    (Max(x, y, x, Max(y, 3)), Max(3, x, y)),
    (Max(x, x), x),
    (Max(), Max()),
    (Max(Max(y), x, y), Max(x, y)),
    (Cat(x, x, y), Cat(x, y)),
    (Cat(x, Cat(x, y), y), Cat(x, y)),
    (Cat(x, 0, x), x),
    (Cat(y, Cat(0), x, 9), 9),
    (Cat(0, 0), 0),
    (Cat(), 0),
    (Hcf(x, 0), x),
    (Hcf(0, 0), 0),
    (Hcf(x, x), x),
    (Hcf(1, x), 1),
    (Hcf(Hcf(x, 0), y), Hcf(x, y)),
    (Sym(x, 0), x),
    (Sym(Sym(x, x), y), Sym(x, y)),
    (Sym(x, x, 0), Sym(x, x, 0)),
])
def test_the_declared_laws(e, expected):
    assert same(e, expected)


@pytest.mark.parametrize("e", [
    Cat(x, y, x),
    Cat(y, x),
    Cat(log(x), 9),
    Hcf(x, y),
    Hcf(x, Hcf(x, y)),
    Hcf(log(x), 1),
    Sym(0, x, y),
    Sym(x, x, x),
    Sym(Sym(x, y), y),
    Pow(x, 1),
])
def test_what_the_laws_leave_alone(e):
    assert (normalise(e).head, Counter(normalise(e).args)) == (e.head, Counter(e.args))


def test_only_a_commutative_head_is_reordered():
    assert normalise(Cat(x, y, x)) == Cat(x, y, x)
    assert normalise(Cat(y, x)) == Cat(y, x)
    assert normalise(Hcf(y, x)) == normalise(Hcf(x, y))
    assert normalise(Sym(y, 0, x)) == normalise(Sym(x, y, 0))


@pytest.mark.parametrize("order", list(permutations(range(3))))
def test_the_order_of_the_keywords_does_not_change_the_result(order):
    given = [("identity_element", 0), ("absorbing_element", 9), ("is_idempotent", True)]
    C = declare_function(f"Cat{order}", Many(NumberKind), returns=NumberKind, domain=true)
    declare_properties(C, is_associative=True, **dict(given[i] for i in order))
    for e, expected in [
        (C(x, 0, x, y, y), C(x, y)),
        (C(x, C(0, 9), log(y)), C(x, 9, log(y))),
        (C(x, 0, 9), 9),
        (C(y, x, 0, 0, x), C(y, x)),
    ]:
        assert same(e, expected)


@pytest.mark.parametrize("e, expected", [
    (sin(x) * 0, 0),
    (exp(sin(x)) * 0, 0),
    (log(x) * 0, nr.Mul(0, log(x))),
    (tan(x) * y * 0, nr.Mul(0, y, tan(x))),
    (x / x, nr.Mul(x, x ** -1)),
])
def test_nothing_without_a_value_is_erased(e, expected):
    assert same(e, expected)


def test_known_conditions_allow_more():
    assert same(log(x) * 0, 0, known=lambda c: c == Ne(x, 0))
    assert same(log(x) * 0, nr.Mul(0, log(x)), known=lambda c: 1)


@pytest.mark.parametrize("e, expected", [
    (Pow(x, 1), Pow(x, 1)),
    (Pow(x * 1, 0 + nr.Mul(1)), Pow(x, 1)),
    (Pow(1, x + y), Pow(1, nr.Add(x, y))),
    (Not(Not(p)), Not(Not(p))),
    (Not(And(q, p, true)), Not(And(p, q))),
    (exp(log(y + 0)), exp(log(y))),
])
def test_other_heads_only_get_normal_arguments(e, expected):
    assert normalise(e) == expected


def test_a_normal_form_is_its_own_normal_form():
    cases = [
        (x + y) * (y + x) * 1 + x * 0,
        sin(x + 0) * sin(0 + x) + log(x * 1 * y),
        And(Or(p, q), Or(q, p), Not(Not(Or(p, q)))),
        Or(And(p, false), And(q, q), p),
        Pow(x * 0 + 1, Max(x, x)),
        Max(Max(x, 0), Max(y, x), sin(x)),
        Cat(x, Cat(0, x), y, Cat(y, x)),
        Hcf(Hcf(y, 0), Hcf(x, x)),
        Sym(Hcf(y, x), x, Cat(0)),
    ]
    for e in cases:
        assert normalise(normalise(e)) == normalise(e)


def test_a_head_that_is_not_a_declared_function_has_no_properties():
    f = NumberFunction("f")
    assert normalise(f(x + 0)) == f(x)
    assert normalise(f(x) * 1 + f(0 + x)) == normalise(f(x) + f(x))


def test_lambdas_are_left_alone():
    f = nr.Lambda(x, x + 0)
    assert normalise(f) == f


def test_a_lambda_applied_to_arguments_is_a_head_without_properties():
    square, times = nr.Lambda(x, x * x), nr.Lambda((x, y), x * y)
    assert normalise(square(x + 0) + 0) == square(x)
    assert normalise(times(y, 1)) == times(y, 1)


def test_the_bracketing_of_one_associative_head_does_not_change_the_result():
    expected = nr.Mul(0, log(x), y)
    assert normalise(nr.Mul(log(x), nr.Mul(0, y))) == expected
    assert normalise(nr.Mul(nr.Mul(log(x), 0), y)) == expected
    assert normalise(nr.Mul(log(x), 0, y)) == expected


def test_an_argument_that_becomes_the_same_head_once_normal_is_spliced():
    assert normalise(nr.Add(x, nr.Mul(1, nr.Add(y, z)))) == nr.Add(x, y, z)


def test_a_sum_built_term_by_term_in_a_loop():
    terms = [NumberKind(f"t{i}") for i in range(3000)]
    total = terms[0]
    for term in terms[1:]:
        total = total + term
    assert normalise(total) == normalise(nr.Add(*terms))


def test_only_expressions_are_normalised():
    with pytest.raises(TypeError):
        normalise(3)


def test_a_kind_declared_here_with_a_plain_head_and_a_commutative_associative_head():
    Shape = nr.declare_kind("Shape")
    Rotate = declare_function("Rotate", Shape, returns=Shape, domain=true)
    Overlay = declare_function("Overlay", Many(Shape), returns=Shape, domain=true)
    declare_properties(Overlay, is_associative=True, is_commutative=True)
    a, b, c = Shape("a"), Shape("b"), Shape("c")

    assert normalise(Rotate(Rotate(a))) == Rotate(Rotate(a))
    assert Counter(normalise(Overlay(b, Overlay(c, a))).args) == Counter([a, b, c])
    assert normalise(Rotate(Overlay(c, Overlay(b, a)))) == Rotate(normalise(Overlay(a, b, c)))
    assert normalise(Overlay(Overlay(a))) == a and normalise(Overlay(a)).kind is Shape

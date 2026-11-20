"""Sets of numbers, declared in ``nary.sets``."""

import doctest

import pytest

from nary import BoolKind, NumberKind, sets
from nary.sets import (
    Contains,
    FiniteSet,
    Intersection,
    Interval,
    NumberSetKind,
    SetKind,
    Union,
)

x, a, b = (NumberKind(n) for n in "xab")
S, T = NumberSetKind("S"), NumberSetKind("T")


def test_each_function_builds_a_node_of_its_declared_kind():
    i = Interval(a, b)
    assert (i.start, i.end) == (a, b)
    assert FiniteSet().args == ()
    built = [i, FiniteSet(a, x), Union(S, T, i), Intersection(S, T)]
    assert all(e.kind is NumberSetKind for e in built)
    c = Contains(x, Intersection(S, T))
    assert c.kind is BoolKind
    assert (c.element, c.set) == (x, Intersection(S, T))


def test_a_number_where_a_set_is_required_is_a_kind_error():
    with pytest.raises(TypeError, match=r"^Union expects SetKind\(NumberKind\), got NumberKind: x$"):
        Union(S, x)


def test_set_kind_of_numbers_is_the_same_object_every_time():
    assert SetKind(NumberKind) is NumberSetKind
    assert SetKind(NumberKind) is SetKind(NumberKind)
    assert NumberSetKind.family is SetKind
    assert NumberSetKind.params == (NumberKind,)


def test_module_docstring_examples():
    result = doctest.testmod(sets)
    assert result.attempted > 0
    assert result.failed == 0

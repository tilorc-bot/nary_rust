"""Sets of numbers, declared in nary.sets."""

import doctest

import nary as nr
import nary.sets
import pytest
from nary.sets import (
    Contains,
    FiniteSet,
    Intersection,
    NumberSet,
    Reals,
    SetKind,
    Union,
)

x = nr.NumberKind("x")
S = NumberSet("S")


def test_module_docstring_examples():
    result = doctest.testmod(nary.sets)
    assert result.attempted > 0
    assert result.failed == 0


def test_kinds():
    assert NumberSet is SetKind(nr.NumberKind)
    assert Reals.kind is NumberSet and Reals.is_constant
    assert FiniteSet().kind is NumberSet and Intersection().kind is NumberSet
    assert Contains(x, Intersection(S, Reals)).kind is nr.BoolKind
    assert "Contains" not in nr.__all__


def test_kind_errors():
    with pytest.raises(TypeError, match=r"^Contains expects SetKind\(NumberKind\), got NumberKind: x$"):
        Contains(x, x)
    with pytest.raises(TypeError, match=r"^Union expects SetKind\(NumberKind\), got NumberKind: x$"):
        Union(S, x)

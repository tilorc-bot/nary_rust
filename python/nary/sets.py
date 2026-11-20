"""Contains says whether a number is in a set.

    >>> from nary import NumberKind
    >>> from nary.sets import Contains, FiniteSet, Integers, NumberSet, Reals, Union
    >>> x, n = NumberKind("x"), NumberKind("n")
    >>> S = NumberSet("S")
    >>> Contains(x, Reals), Contains(n, Integers)
    (Contains(x, Reals), Contains(n, Integers))

FiniteSet and Union build sets, and Contains is a BoolKind.

    >>> c = Contains(x, Union(FiniteSet(1, 2), S))
    >>> c, c.kind, S.kind
    (Contains(x, Union(FiniteSet(1, 2), S)), BoolKind, SetKind(NumberKind))

The second argument of Contains must be a set.

    >>> Contains(x, n)
    Traceback (most recent call last):
        ...
    TypeError: Contains expects SetKind(NumberKind), got NumberKind: n
"""

from ._core import declare_constant, declare_kind_family
from .domains import declare_function
from .kinds import BoolKind, NumberKind
from .logic import true

__all__ = [
    "SetKind", "NumberSet", "Reals", "Integers",
    "Contains", "FiniteSet", "Union", "Intersection",
]

SetKind = declare_kind_family("SetKind", params=1)

NumberSet = SetKind(NumberKind)

Reals = declare_constant("Reals", NumberSet)
Integers = declare_constant("Integers", NumberSet)

Contains = declare_function(
    "Contains", NumberKind, NumberSet, returns=BoolKind, domain=true
)
FiniteSet = declare_function(
    "FiniteSet", rest=NumberKind, returns=NumberSet, domain=true
)
Union = declare_function("Union", rest=NumberSet, returns=NumberSet, domain=true)
Intersection = declare_function(
    "Intersection", rest=NumberSet, returns=NumberSet, domain=true
)

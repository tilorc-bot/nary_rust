"""Sets of numbers.

This module declares the kind family ``SetKind``, with one parameter, and
functions on sets of numbers, whose kind is ``SetKind(NumberKind)``, named
``NumberSetKind`` here:

- ``Interval(start, end)``: the numbers from ``start`` to ``end``.
- ``FiniteSet(*elements)``: the set of the given numbers. With no
  arguments it is the empty set.
- ``Union(*sets)`` and ``Intersection(*sets)``.
- ``Contains(element, set)``: whether a number is in a set, a ``BoolKind``.

It is imported as ``nary.sets``; these names are not re-exported from
``nary``. Sets have no operators.

    >>> from nary import NumberKind
    >>> from nary.sets import Contains, FiniteSet, Interval, NumberSetKind, Union
    >>> x, a, b = (NumberKind(n) for n in "xab")
    >>> S = NumberSetKind("S")
    >>> c = Contains(x, Union(Interval(a, b), FiniteSet(a, x), S))
    >>> c
    Contains(x, Union(Interval(a, b), FiniteSet(a, x), S))
    >>> c.kind, c.set.kind
    (BoolKind, SetKind(NumberKind))
    >>> Contains(x, a)
    Traceback (most recent call last):
        ...
    TypeError: Contains expects SetKind(NumberKind), got NumberKind: a

Known gaps:

- An interval is always closed at both ends.
- The elements of a set are only numbers; there are no functions on
  ``SetKind`` of any other kind.
"""

from ._core import function, kind_family
from .kinds import BoolKind, NumberKind

__all__ = [
    "Contains", "FiniteSet", "Intersection", "Interval", "NumberSetKind",
    "SetKind", "Union",
]

SetKind = kind_family("SetKind", params=1)
NumberSetKind = SetKind(NumberKind)

Interval = function(
    "Interval", NumberKind, NumberKind, returns=NumberSetKind, names=("start", "end")
)
FiniteSet = function("FiniteSet", rest=NumberKind, returns=NumberSetKind)
Union = function("Union", rest=NumberSetKind, returns=NumberSetKind)
Intersection = function("Intersection", rest=NumberSetKind, returns=NumberSetKind)
Contains = function(
    "Contains", NumberKind, NumberSetKind, returns=BoolKind, names=("element", "set")
)

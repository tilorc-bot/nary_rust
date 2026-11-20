"""Sets of numbers.

This module declares the kind family ``SetKind`` (one parameter, the kind of
the elements), the kind ``NumberSet = SetKind(NumberKind)`` of a set of
numbers, and:

- the constants ``Reals`` and ``Integers``, declared with
  ``declare_constant``;
- ``Contains(element, set)``: whether a number is in a set, a ``BoolKind``;
- ``FiniteSet(a, b, ...)``: the set of the given numbers. ``FiniteSet()`` is
  the empty set.
- ``Union(A, B, ...)`` and ``Intersection(A, B, ...)``: any number of sets,
  returning a set.

So "x is real" is ``Contains(x, Reals)`` and "n is an integer" is
``Contains(n, Integers)``. Nothing is computed or simplified.

The module is imported as ``nary.sets``; ``import nary`` does not import
it, and its names are not re-exported from ``nary``.

    >>> from nary import NumberKind
    >>> from nary.sets import Contains, FiniteSet, Integers, NumberSet, Reals, Union
    >>> x, n = NumberKind("x"), NumberKind("n")
    >>> S = NumberSet("S")
    >>> Contains(x, Reals), Contains(n, Integers)
    (Contains(x, Reals), Contains(n, Integers))
    >>> c = Contains(x, Union(FiniteSet(1, 2), S))
    >>> c, c.kind, S.kind
    (Contains(x, Union(FiniteSet(1, 2), S)), BoolKind, SetKind(NumberKind))
    >>> Contains(x, n)
    Traceback (most recent call last):
        ...
    TypeError: Contains expects SetKind(NumberKind), got NumberKind: n

Not here:

- ``Interval``: whether each end is open or closed, infinite ends, and
  whether the ends must be real are undecided.
- Complements, set differences and sets built from a condition.
- Other named sets, such as ``Rationals``, ``Naturals`` or ``Complexes``.
- Operators: ``|``, ``&`` and ``in`` do not build these functions.
- Sets of anything other than numbers: ``SetKind`` can be given any kind,
  but the functions here are declared only for ``SetKind(NumberKind)``.
"""

from ._core import declare_constant, declare_function, declare_kind_family
from .kinds import BoolKind, NumberKind

__all__ = [
    "SetKind", "NumberSet", "Reals", "Integers",
    "Contains", "FiniteSet", "Union", "Intersection",
]

SetKind = declare_kind_family("SetKind", params=1)

NumberSet = SetKind(NumberKind)

Reals = declare_constant("Reals", NumberSet)
Integers = declare_constant("Integers", NumberSet)

Contains = declare_function("Contains", NumberKind, NumberSet, returns=BoolKind)
FiniteSet = declare_function("FiniteSet", rest=NumberKind, returns=NumberSet)
Union = declare_function("Union", rest=NumberSet, returns=NumberSet)
Intersection = declare_function("Intersection", rest=NumberSet, returns=NumberSet)

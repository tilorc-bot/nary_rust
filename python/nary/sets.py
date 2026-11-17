"""Sets of numbers, of the kind SetKind(NumberKind)."""

from ._core import function
from .kinds import BoolKind, NumberKind, SetKind

_Set = SetKind(NumberKind)

# TODO: an interval is closed at both ends.
Interval = function(
    "Interval", NumberKind, NumberKind, returns=_Set, names=("start", "end")
)
FiniteSet = function("FiniteSet", rest=NumberKind, returns=_Set)
Union = function("Union", rest=_Set, returns=_Set)
Intersection = function("Intersection", rest=_Set, returns=_Set)
Contains = function(
    "Contains", NumberKind, _Set, returns=BoolKind, names=("element", "set")
)

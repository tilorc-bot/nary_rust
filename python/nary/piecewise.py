"""Piecewise."""

from ._core import function
from .kinds import BoolKind, NumberKind

# The pairs are written flat, alternating value and condition:
#
#     Piecewise(x, x > 0, Mul(-1, x), true)
#
# There is no tuple kind, so the (value, condition) pairs are not grouped.
Piecewise = function("Piecewise", rest=(NumberKind, BoolKind), returns=NumberKind)

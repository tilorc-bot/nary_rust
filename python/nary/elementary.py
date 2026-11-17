"""Elementary functions."""

from ._core import function
from .kinds import NumberKind

sin = function("sin", NumberKind, returns=NumberKind)

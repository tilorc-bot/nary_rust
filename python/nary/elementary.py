"""Elementary functions."""

from ._core import function
from .kinds import NumberKind

__all__ = ["sin"]

sin = function("sin", NumberKind, returns=NumberKind)

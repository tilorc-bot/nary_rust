"""Elementary functions."""

from ._core import function
from .kinds import NumberKind

__all__ = ["cos", "exp", "log", "sin", "tan"]

sin = function("sin", NumberKind, returns=NumberKind)
cos = function("cos", NumberKind, returns=NumberKind)
tan = function("tan", NumberKind, returns=NumberKind)
exp = function("exp", NumberKind, returns=NumberKind)
log = function("log", NumberKind, returns=NumberKind)

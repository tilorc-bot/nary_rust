"""Elementary functions."""

from ._core import declare_function
from .kinds import NumberKind

__all__ = ["cos", "exp", "log", "sin", "tan"]

sin = declare_function("sin", NumberKind, returns=NumberKind)
cos = declare_function("cos", NumberKind, returns=NumberKind)
tan = declare_function("tan", NumberKind, returns=NumberKind)
exp = declare_function("exp", NumberKind, returns=NumberKind)
log = declare_function("log", NumberKind, returns=NumberKind)

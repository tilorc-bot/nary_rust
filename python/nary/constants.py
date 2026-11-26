from ._core import declare_constant
from .kinds import NumberKind

__all__ = ["E", "I", "pi"]

pi = declare_constant("pi", NumberKind)
E = declare_constant("E", NumberKind)
I = declare_constant("I", NumberKind)

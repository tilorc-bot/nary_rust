"""Named constants of numbers.

A constant is a named leaf that stands for one specific thing. It is
declared with ``declare_constant(name, kind)``, is equal only to itself, and,
unlike a symbol, cannot be bound by ``Lambda``. The names are SymPy's: ``pi``,
``E`` (the base of the natural logarithm) and ``I`` (the imaginary unit).
Nothing is known about them beyond their kind.
"""

from ._core import declare_constant
from .kinds import NumberKind

__all__ = ["E", "I", "pi"]

pi = declare_constant("pi", NumberKind)
E = declare_constant("E", NumberKind)
I = declare_constant("I", NumberKind)

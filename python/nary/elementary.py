"""Elementary functions and constants."""

from ._core import function
from .kinds import NumberKind

sin = function("sin", NumberKind, returns=NumberKind)
cos = function("cos", NumberKind, returns=NumberKind)
tan = function("tan", NumberKind, returns=NumberKind)
exp = function("exp", NumberKind, returns=NumberKind)
log = function("log", NumberKind, returns=NumberKind)

# A constant is a function of no arguments, applied once. It is not a symbol,
# so it is rejected where a signature asks for Symbol(NumberKind).
pi = function("pi", returns=NumberKind)()

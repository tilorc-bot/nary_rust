"""Boolean connectives and constants."""

from ._core import function
from .kinds import BoolKind

And = function("And", rest=BoolKind, returns=BoolKind)
Or = function("Or", rest=BoolKind, returns=BoolKind)
Not = function("Not", BoolKind, returns=BoolKind)

# Python's True and False are not converted. Use these where a BoolKind is
# expected, such as the last condition of a Piecewise.
true = function("true", returns=BoolKind)()
false = function("false", returns=BoolKind)()

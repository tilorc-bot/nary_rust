"""Derivatives, integrals, sums, products, limits and substitution.

Every function here takes a variable, declared as ``Symbol(NumberKind)`` so
that only a symbol is accepted in that position. The arguments are written
flat, and several variables are written by nesting:

    Integral(Integral(f, x, 0, 1), y, 0, 2)

``binds={1: (0,)}`` records that argument 1 is a variable bound in argument 0.
Nothing reads it yet. It is there so that substitution, when it is written,
can tell that x in the body of an integral is not the x outside it. The
limits of an integral are outside the scope of its variable.
"""

from ._core import Symbol, function
from .kinds import NumberKind

_var = Symbol(NumberKind)

# The variable of a derivative or an antiderivative stays free: the result
# still depends on it.
Derivative = function(
    "Derivative", NumberKind, _var, returns=NumberKind, names=("expr", "var")
)
Antiderivative = function(
    "Antiderivative", NumberKind, _var, returns=NumberKind, names=("body", "var")
)

_range = ("body", "var", "lower", "upper")

Integral = function(
    "Integral", NumberKind, _var, NumberKind, NumberKind,
    returns=NumberKind, names=_range, binds={1: (0,)},
)
Sum = function(
    "Sum", NumberKind, _var, NumberKind, NumberKind,
    returns=NumberKind, names=_range, binds={1: (0,)},
)
Product = function(
    "Product", NumberKind, _var, NumberKind, NumberKind,
    returns=NumberKind, names=_range, binds={1: (0,)},
)

# TODO: a limit has no direction.
Limit = function(
    "Limit", NumberKind, _var, NumberKind,
    returns=NumberKind, names=("expr", "var", "point"), binds={1: (0,)},
)

# An unevaluated substitution of point for var in expr.
Subs = function(
    "Subs", NumberKind, _var, NumberKind,
    returns=NumberKind, names=("expr", "var", "point"), binds={1: (0,)},
)

# TODO: these need a function kind, which does not exist, so they are left
# out:
#   - Lambda;
#   - passing an undefined function itself as an argument (applying one is
#     fine: f = function("f", NumberKind, returns=NumberKind));
#   - derivatives written as operators, such as D(f) or D(f)(x).
# TODO: a derivative of order n, and derivatives, integrals and substitutions
# in several variables at once, need a tuple kind or more signature forms.
# Write them by nesting.

"""Integral takes a function, here a lambda, and two numbers.

    >>> from nary import Lambda, NumberKind, sin
    >>> from nary.calculus import Derivative, Integral, Limit, NumberFunction
    >>> x, a, b = NumberKind("x"), NumberKind("a"), NumberKind("b")
    >>> f = NumberFunction("f")
    >>> Integral(Lambda(x, x * x), a, b)
    Integral(Lambda(x, Mul(x, x)), a, b)

The arguments are named, and the result is a number.

    >>> Integral(sin, a, b).integrand, Integral(f, a, b).kind
    (sin, NumberKind)

Derivative(f) is a function, so it can be applied or differentiated again.

    >>> Derivative(f)(a), Derivative(Derivative(f)).kind
    (Derivative(f)(a), FunctionKind((NumberKind,), NumberKind))

Limit takes a function and a point.

    >>> Limit(Lambda(x, sin(x) * x), a)
    Limit(Lambda(x, Mul(sin(x), x)), a)

A substitution left unevaluated is a call of a lambda.

    >>> Lambda(x, sin(x))(a)                 # a substitution, unevaluated
    Lambda(x, sin(x))(a)

An expression is not accepted where a function is expected.

    >>> Integral(x * x, a, b)
    Traceback (most recent call last):
        ...
    TypeError: Integral expects FunctionKind((NumberKind,), NumberKind), got NumberKind: Mul(x, x)
"""

from ._core import FunctionKind
from .domains import declare_function
from .kinds import NumberKind
from .logic import true

__all__ = [
    "NumberFunction",
    "Integral", "Sum", "Product", "Limit", "Derivative", "Antiderivative",
]

NumberFunction = FunctionKind((NumberKind,), NumberKind)

integrand, summand = NumberFunction("integrand"), NumberFunction("summand")
factor, function = NumberFunction("factor"), NumberFunction("function")
lower, upper, point = NumberKind("lower"), NumberKind("upper"), NumberKind("point")

Integral = declare_function("Integral", integrand, lower, upper, returns=NumberKind, domain=None)
Sum = declare_function("Sum", summand, lower, upper, returns=NumberKind, domain=None)
Product = declare_function("Product", factor, lower, upper, returns=NumberKind, domain=None)
Limit = declare_function("Limit", function, point, returns=NumberKind, domain=None)
Derivative = declare_function("Derivative", function, returns=NumberFunction, domain=true)
Antiderivative = declare_function("Antiderivative", function, returns=NumberFunction, domain=true)

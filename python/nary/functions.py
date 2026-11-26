"""A lambda of one variable has a function kind.

    >>> from nary import NumberKind
    >>> from nary.functions import Lambda, is_lambda
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> square = Lambda(x, x * x)
    >>> square, square.kind
    (Lambda(x, Mul(x, x)), FunctionKind((NumberKind,), NumberKind))

Several variables are given as a tuple.

    >>> Lambda((x, y), x < y)
    Lambda(x, y, Lt(x, y))

The arguments of a lambda are its variables and then its body.

    >>> square.args[:-1], square.args[-1], is_lambda(square)
    ((x,), Mul(x, x), True)
"""

from ._core import Bound, Expr, FunctionKind, KindVariable, ManyMixed
from .domains import declare_function
from .logic import true

__all__ = ["Lambda", "is_lambda"]

K, B = KindVariable("K"), KindVariable("B")
_lambda = declare_function(
    "Lambda",
    ManyMixed(Bound(K("variables"))),
    B("expr"),
    returns=FunctionKind((ManyMixed(K),), B),
    domain=true,
)


def Lambda(variables, body):
    if not isinstance(variables, tuple):
        variables = (variables,)
    if not variables:
        raise TypeError("Lambda takes at least one variable, got ()")
    for variable in variables:
        if not isinstance(variable, Expr):
            raise TypeError(f"Lambda variables must be symbols, got {variable!r}")
    if not isinstance(body, Expr):
        raise TypeError(f"the body of a Lambda must be an expression, got {body!r}")

    names = set()
    for variable in variables:
        if variable.is_symbol:
            if variable.name in names:
                raise ValueError(
                    f"Lambda variables must have different names, got {variable.name} more than once"
                )
            names.add(variable.name)

    return _lambda(*variables, body)


def is_lambda(e):
    if not isinstance(e, Expr) or e.head is None:
        return False
    return e.head is _lambda

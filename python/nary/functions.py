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

from __future__ import annotations

from ._core import Expr, FunctionKind, Kind, Symbol
from .domains import declare_function
from .logic import true

__all__ = ["Lambda", "is_lambda"]

_lambda_functions: dict[tuple[Kind, ...], Expr] = {}


def _lambda_function(variable_kinds: tuple[Kind, ...], body_kind: Kind) -> Expr:
    key = (*variable_kinds, body_kind)
    if key not in _lambda_functions:
        _lambda_functions[key] = declare_function(
            "Lambda",
            *(Symbol(kind) for kind in variable_kinds),
            body_kind,
            returns=FunctionKind(variable_kinds, body_kind),
            domain=true,
        )
    return _lambda_functions[key]


def Lambda(variables: Expr | tuple[Expr, ...], body: Expr) -> Expr:
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

    variable_kinds = tuple(variable.kind for variable in variables)
    return _lambda_function(variable_kinds, body.kind)(*variables, body)


def is_lambda(e: object) -> bool:
    if not isinstance(e, Expr) or e.is_atom:
        return False
    return _lambda_functions.get(e.head.kind.inputs) is e.head

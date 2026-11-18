"""Lambda: a function given by variables and a body.

A lambda is not a special form. It is an ordinary application, made with
the same ``declare_function(...)`` and ``Symbol(kind)`` that any declaration
uses. For each combination of kinds, a function named ``"Lambda"`` is
declared once: it takes the variables, each declared ``Symbol(kind)`` so
that only a symbol is accepted, then the body, and it returns the function
kind from the kinds of the variables to the kind of the body.
``Lambda(variables, body)`` applies that function. So a lambda prints as
``Lambda(x, y, body)``, with the variables and the body as its arguments:

    >>> from nary import NumberKind
    >>> from nary.functions import Lambda, is_lambda
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> square = Lambda(x, x * x)
    >>> square, square.kind
    (Lambda(x, Mul(x, x)), FunctionKind((NumberKind,), NumberKind))
    >>> Lambda((x, y), x < y)
    Lambda(x, y, Lt(x, y))
    >>> square.args[:-1], square.args[-1], is_lambda(square)
    ((x,), Mul(x, x), True)

A lambda is called like any expression of a function kind, and calling it
is inert: ``square(y)`` is an application whose head is ``square``. Nothing
is substituted.
"""

from ._core import Expr, FunctionKind, Symbol, declare_function

__all__ = ["Lambda", "is_lambda"]

# The function named "Lambda" for each combination of kinds, declared the
# first time it is needed. The key is the kinds of the variables followed by
# the kind of the body, which is also the inputs of the function's kind.
_lambda_functions = {}


def _lambda_function(variable_kinds, body_kind):
    """The function named "Lambda" for these kinds, declared once."""
    key = (*variable_kinds, body_kind)
    if key not in _lambda_functions:
        _lambda_functions[key] = declare_function(
            "Lambda",
            *(Symbol(kind) for kind in variable_kinds),
            body_kind,
            returns=FunctionKind(variable_kinds, body_kind),
        )
    return _lambda_functions[key]


def Lambda(variables, body):
    """The function of ``variables`` given by ``body``.

    ``variables`` is one symbol or a tuple of one or more symbols, with
    different names. ``body`` is any expression.
    """
    if not isinstance(variables, tuple):
        variables = (variables,)
    if not variables:
        raise TypeError("Lambda takes at least one variable, got ()")
    for variable in variables:
        if not isinstance(variable, Expr):
            raise TypeError(f"Lambda variables must be symbols, got {variable!r}")
    if not isinstance(body, Expr):
        raise TypeError(f"the body of a Lambda must be an expression, got {body!r}")

    # Two variables with the same name would be ambiguous in the body, even
    # if their kinds differ. That each variable is a symbol is checked by
    # the Symbol(kind) positions when the function is applied below.
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


def is_lambda(e):
    """Whether ``e`` is a lambda: an application of one of the functions
    named "Lambda" declared here."""
    if not isinstance(e, Expr) or e.head is None:
        return False
    return _lambda_functions.get(e.head.kind.inputs) is e.head

"""Each function has a declared domain.

    >>> from nary import Ne, NumberKind, Pow, declare_function, log, sin
    >>> from nary.domains import domain, domain_of
    >>> from nary.logic import true
    >>> domain(log), domain(sin), domain(Pow)
    (Ne(x, 0), true, Or(Ne(base, 0), Gt(re(exp), 0)))

domain_of puts the arguments of an application in place of the parameters.

    >>> y = NumberKind("y")
    >>> domain_of(log(y + 1)), domain_of(Pow(y, -1))
    (Ne(Add(y, 1), 0), Or(Ne(y, 0), Gt(re(-1), 0)))

A domain must be a BoolKind expression whose symbols are all parameters.

    >>> t = NumberKind("t")
    >>> sinc = declare_function("sinc", t, returns=NumberKind, domain=true)
    >>> declare_function("f", t, returns=NumberKind, domain=log(y))
    Traceback (most recent call last):
        ...
    TypeError: the domain of f must be a BoolKind expression, got log(y)
    >>> declare_function("f", t, returns=NumberKind, domain=Ne(y, 0))
    Traceback (most recent call last):
        ...
    ValueError: the domain of f mentions y, which is not one of its parameters
"""

from . import _core
from ._core import Expr
from .kinds import BoolKind

__all__ = ["declare_function", "domain", "domain_of"]

_domains = {}

_AWAITING_A_DECISION = {
    "Integral", "Sum", "Product", "Limit",
    "MatAdd", "MatMul", "Transpose", "Inverse", "Determinant", "Trace",
}


def declare_function(name, *parameters, returns, domain):
    symbols = [p for p in parameters if isinstance(p, Expr) and p.is_symbol]
    if symbols and len(symbols) != len(parameters):
        raise TypeError(
            f"either every parameter of {name} is a symbol or none is, got {parameters!r}"
        )
    names = [symbol.name for symbol in symbols]
    for n in names:
        if names.count(n) > 1:
            raise ValueError(f"{name} has two parameters named {n}")

    if domain is None and name in _AWAITING_A_DECISION:
        pass
    elif not (isinstance(domain, Expr) and domain.kind is BoolKind):
        raise TypeError(f"the domain of {name} must be a BoolKind expression, got {domain!r}")
    else:
        for e in _subexpressions(domain):
            if e.is_symbol and e not in symbols:
                raise ValueError(
                    f"the domain of {name} mentions {e!r}, which is not one of its parameters"
                )

    if symbols:
        parameters = [symbol.kind for symbol in symbols]
    function = _core.declare_function(
        name, *parameters, returns=returns, names=tuple(names)
    )
    if domain is not None:
        _domains[function] = domain
    return function


def _subexpressions(e):
    yield e
    if not e.is_atom:
        yield from _subexpressions(e.head)
        for arg in e.args:
            yield from _subexpressions(arg)


def _is_declared_function(e):
    return isinstance(e, Expr) and e.is_constant and e.kind.inputs is not None


def domain(function):
    if not _is_declared_function(function):
        raise TypeError(f"domain expects a declared function, got {function!r}")
    return _domains.get(function)


def domain_of(e):
    if not (isinstance(e, Expr) and _is_declared_function(e.head)):
        raise TypeError(f"domain_of expects an application of a declared function, got {e!r}")
    condition = domain(e.head)
    if condition is None:
        return None
    parameters = [kind(name) for kind, name in zip(e.head.kind.inputs, e.head.names)]
    return _replace(condition, dict(zip(parameters, e.args)))


def _replace(e, replacements):
    if e.is_symbol:
        return replacements.get(e, e)
    if e.is_atom:
        return e
    return _replace(e.head, replacements)(*(_replace(arg, replacements) for arg in e.args))

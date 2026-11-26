"""Declaring functions, each with its domain.

Functions are partial: ``1/0`` and ``log(0)`` have no value (issue #2). The
domain of a function is the condition under which it has a value, given that
its arguments do. It is stated when the function is declared, as a
``BoolKind`` expression in the function's parameters. This module only
records domains: nothing here simplifies or decides them.

- ``declare_function(name, *parameters, rest=None, returns, domain)``
  declares a function with ``nary._core.declare_function`` and records its
  domain. A parameter is a kind, a ``Symbol(kind)`` marker (a position that
  accepts only a symbol), or a symbol such as ``NumberKind("x")``: a
  position of that symbol's kind, whose argument is then available by the
  symbol's name, as ``Eq(a, b).lhs`` is. Either every parameter is a
  symbol or none is. ``domain`` must be given: a ``BoolKind`` expression
  whose symbols are all parameters. A function with no parameter symbols,
  or with only ``rest=``, can only have a domain that mentions none, such
  as ``true``.
- ``domain(function)`` returns the declared domain.
- ``domain_of(e)`` returns the domain of the application ``e``: the domain
  of its head with each parameter replaced by the argument in its
  position.

    >>> from nary import Ne, NumberKind, Pow, declare_function, log, sin
    >>> from nary.domains import domain, domain_of
    >>> from nary.logic import true
    >>> domain(log), domain(sin), domain(Pow)
    (Ne(x, 0), true, Or(Ne(base, 0), Gt(re(exp), 0)))
    >>> y = NumberKind("y")
    >>> domain_of(log(y + 1)), domain_of(Pow(y, -1))
    (Ne(Add(y, 1), 0), Or(Ne(y, 0), Gt(re(-1), 0)))
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

A parameter symbol is an ordinary symbol, not the ``Symbol(kind)`` marker:
its position accepts any expression of its kind.

Deliberately not declared yet:

- Kleene logic for ``And`` and ``Or`` (``false and <no value>`` is ``false``);
- ``0**0``, and natural-number powers with ``a**0 = 1`` for every ``a``;
- the domains of ``Integral``, ``Sum``, ``Product``, ``Limit`` and of the
  matrix functions (see ``_AWAITING_A_DECISION`` below).

The module is imported as ``nary.domains``; ``declare_function`` is
re-exported from ``nary``, ``domain`` and ``domain_of`` are not.
"""

from . import _core
from ._core import Expr
from .kinds import BoolKind

__all__ = ["declare_function", "domain", "domain_of"]

# The domain of each declared function that has one.
_domains = {}

# AWAITING A DECISION BY THE OWNER. The domains of these functions need
# words that do not exist yet (when an integral, sum, product or limit
# converges; the shape of a matrix), and it is not decided whether to add
# them or to take the functions out. Until then these functions, and no
# others, are declared with domain=None, which records no domain.
_AWAITING_A_DECISION = {
    "Integral", "Sum", "Product", "Limit",
    "MatAdd", "MatMul", "Transpose", "Inverse", "Determinant", "Trace",
}


def declare_function(name, *parameters, rest=None, returns, domain):
    """Declare a function with ``nary._core.declare_function`` and record
    its ``domain``.

    Each of ``parameters`` is a kind, a ``Symbol(kind)`` marker or a
    symbol; a symbol stands for its kind and names the argument in its
    position. Either every parameter is a symbol or none is. A parameter
    symbol is not the ``Symbol(kind)`` marker: its position accepts any
    expression of its kind. ``domain`` is a ``BoolKind`` expression whose
    symbols are all parameters.
    """
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
        name, *parameters, rest=rest, returns=returns, names=tuple(names)
    )
    if domain is not None:
        _domains[function] = domain
    return function


def _subexpressions(e):
    """``e`` and every expression inside it."""
    yield e
    if e.head is not None:
        yield from _subexpressions(e.head)
        for arg in e.args:
            yield from _subexpressions(arg)


def _is_declared_function(e):
    """Whether ``e`` is a declared function: a constant of a function kind."""
    return isinstance(e, Expr) and e.is_constant and e.kind.inputs is not None


def domain(function):
    """The domain declared for the declared ``function``. ``None`` for the
    functions awaiting a decision, and for a function declared with
    ``nary._core.declare_function`` directly."""
    if not _is_declared_function(function):
        raise TypeError(f"domain expects a declared function, got {function!r}")
    return _domains.get(function)


def domain_of(e):
    """The domain of the application ``e`` of a declared function: the
    domain of its head, with each parameter replaced by the argument in its
    position, all at once. ``None`` where ``domain`` of the head is."""
    if not (isinstance(e, Expr) and _is_declared_function(e.head)):
        raise TypeError(f"domain_of expects an application of a declared function, got {e!r}")
    condition = domain(e.head)
    if condition is None:
        return None
    parameters = [kind(name) for kind, name in zip(e.head.kind.inputs, e.head.names)]
    return _replace(condition, dict(zip(parameters, e.args)))


def _replace(e, replacements):
    """``e`` with each symbol in ``replacements`` replaced by its value.
    Nothing here knows about ``Lambda``; no declared domain contains one."""
    if e.is_symbol:
        return replacements.get(e, e)
    if e.head is None:
        return e
    return _replace(e.head, replacements)(*(_replace(arg, replacements) for arg in e.args))

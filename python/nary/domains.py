"""Declaring functions, each with its domain.

Functions are partial: ``1/0`` and ``log(0)`` have no value (issue #2). The
domain of a function is the condition under which it has a value, given that
its arguments do. It is stated when the function is declared, and
``domain`` returns it. This module only records domains: nothing here
combines, simplifies or decides them. The format is provisional.

- ``declare_function(name, *arg_kinds, rest=None, returns, names=None,
  domain)`` declares a function with ``nary._core.declare_function`` and
  records its domain. ``domain`` must be given. It is a Python function,
  called with the argument expressions of an application, that returns a
  ``BoolKind`` expression; or ``None``, meaning that no domain is stated:
  the function may have no value even where its arguments have one.
- ``domain(function)`` returns that Python function, or ``None``.

    >>> from nary import NumberKind, Pow, declare_function, log, sin
    >>> from nary.domains import domain
    >>> from nary.logic import true
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> domain(log)(x), domain(sin)(x)
    (Ne(x, 0), true)
    >>> domain(Pow)(y, -1)
    Or(Ne(y, 0), Gt(re(-1), 0))
    >>> sinc = declare_function("sinc", NumberKind, returns=NumberKind, domain=lambda x: true)
    >>> f = declare_function("f", NumberKind, returns=NumberKind, domain=None)
    >>> domain(sinc)(y), domain(f) is None
    (true, True)

Deliberately not declared yet:

- comparisons ``Lt``, ``Gt``, ``Le``, ``Ge`` having a value only on reals;
- Kleene logic for ``And`` and ``Or`` (``false and <no value>`` is ``false``);
- ``0**0``, and natural-number powers with ``a**0 = 1`` for every ``a``;
- the domain of ``Inverse`` for matrices, and of the other matrix functions;
- the calculus functions.

The module is imported as ``nary.domains``; ``declare_function`` is
re-exported from ``nary``, ``domain`` is not.
"""

from . import _core
from ._core import Expr

__all__ = ["declare_function", "domain"]

# The domain of each declared function that has one.
_domains = {}


def declare_function(name, *arg_kinds, rest=None, returns, names=None, domain):
    """Declare a function with ``nary._core.declare_function`` and record
    its ``domain``: a Python function returning a ``BoolKind`` expression,
    or ``None`` for no stated domain."""
    # An Expr is callable too, but calling one builds an application.
    if domain is not None and (not callable(domain) or isinstance(domain, Expr)):
        raise TypeError(
            f"the domain of {name} must be a Python function or None, got {domain!r}"
        )
    function = _core.declare_function(
        name, *arg_kinds, rest=rest, returns=returns, names=names
    )
    if domain is not None:
        _domains[function] = domain
    return function


def _is_declared_function(e):
    """Whether ``e`` is a declared function: a constant of a function kind."""
    return isinstance(e, Expr) and e.is_constant and e.kind.inputs is not None


def domain(function):
    """The domain declared for the declared ``function``, or ``None``."""
    if not _is_declared_function(function):
        raise TypeError(f"domain expects a declared function, got {function!r}")
    return _domains.get(function)

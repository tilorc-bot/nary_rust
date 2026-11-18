"""The domains of partial functions.

Functions are partial: ``1/0`` and ``log(0)`` have no value (issue #2). The
domain of a function is the condition under which it has a value, given that
its arguments do. A declared function records its domain with
``set_domain``, next to its declaration, and ``domain`` returns it. This
module only records domains: nothing here combines, simplifies or decides
them. The format is provisional.

- ``set_domain(function, condition)`` registers the domain of a declared
  function, once. ``condition`` is a Python function called with the
  argument expressions of an application; it returns a ``BoolKind``
  expression.
- ``domain(function)`` returns the registered Python function, or ``None``
  if ``function`` has no domain registered.

    >>> from nary import NumberKind, Pow, log, sin
    >>> from nary.domains import domain
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> domain(log)(x)
    Ne(x, 0)
    >>> domain(Pow)(y, -1)
    Or(Ne(y, 0), Gt(re(-1), 0))
    >>> domain(sin) is None
    True

Deliberately not declared yet:

- comparisons ``Lt``, ``Gt``, ``Le``, ``Ge`` having a value only on reals;
- Kleene logic for ``And`` and ``Or`` (``false and <no value>`` is ``false``);
- ``0**0``, and natural-number powers with ``a**0 = 1`` for every ``a``;
- the domain of ``Inverse`` for matrices;
- the calculus functions.

The module is imported as ``nary.domains``; its names are not re-exported
from ``nary``.
"""

from ._core import Expr

__all__ = ["domain", "set_domain"]

# The domain of each declared function that has one.
_domains = {}


def _is_declared_function(e):
    """Whether ``e`` is a declared function: a constant of a function kind."""
    return isinstance(e, Expr) and e.is_constant and e.kind.inputs is not None


def set_domain(function, condition):
    """Register the domain of the declared ``function``.

    ``condition`` is called with the arguments of an application of
    ``function`` and returns a ``BoolKind`` expression. It can be set once
    for each function.
    """
    if not _is_declared_function(function):
        raise TypeError(
            f"set_domain expects a declared function, got {function!r}"
        )
    # An Expr is callable too, but calling one builds an application.
    if not callable(condition) or isinstance(condition, Expr):
        raise TypeError(
            f"the domain condition of {function!r} must be a Python function, "
            f"got {condition!r}"
        )
    if function in _domains:
        raise ValueError(f"the domain of {function!r} is already set")
    _domains[function] = condition


def domain(function):
    """The domain registered for the declared ``function``, or ``None``."""
    if not _is_declared_function(function):
        raise TypeError(f"domain expects a declared function, got {function!r}")
    return _domains.get(function)

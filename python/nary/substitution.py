"""Free symbols, substitution and applying a lambda.

``Lambda`` is the only thing that binds a variable, so these are the only
operations that need to know about it. Every other expression is walked as
it is: a symbol, a declared function, or an application, whose head is
walked as well as its arguments.

- ``free_symbols(e)`` is the set of symbols in ``e`` not bound by an
  enclosing ``Lambda``. Heads count: ``f`` is free in ``Derivative(f)(a)``.
- ``substitute(e, replacements)`` replaces free symbols, all at once.
  ``replacements`` maps symbols to expressions of the same kind. A lambda's
  own variables are not replaced inside it, and a variable is renamed when
  a replacement would otherwise be captured by it. The result is rebuilt
  with the same heads, so the core checks every kind again; the original
  object is returned when nothing in it is replaced.
- ``apply_lambda(e)`` takes ``Lambda((x, y), body)(a, b)`` to ``body`` with
  ``a`` for ``x`` and ``b`` for ``y``: one step, at the root only.

Nothing here simplifies or applies anything on its own. Substituting a
lambda for an unknown function gives an application of the lambda, left
as it is until ``apply_lambda`` is called on it.

The module is imported as ``nary.substitution``; ``import nary`` does not
import it, and its names are not re-exported from ``nary``.

    >>> from nary import Lambda, NumberKind, sin
    >>> from nary.calculus import Derivative, Integral, NumberFunction
    >>> from nary.substitution import apply_lambda, free_symbols, substitute
    >>> x, y, a, b = (NumberKind(n) for n in "xyab")
    >>> f = NumberFunction("f")
    >>> sorted(s.name for s in free_symbols(Integral(Lambda(x, x * y), a, b)))
    ['a', 'b', 'y']
    >>> sorted(s.name for s in free_symbols(Derivative(f)(a)))
    ['a', 'f']
    >>> substitute(x * y, {x: y, y: x})          # simultaneous
    Mul(y, x)
    >>> substitute(Integral(Lambda(x, x * y), a, b), {y: x})   # x is renamed
    Integral(Lambda(x_1, Mul(x_1, x)), a, b)
    >>> substitute(f(a), {f: Lambda(x, sin(x))})
    Lambda(x, sin(x))(a)
    >>> apply_lambda(Lambda(x, sin(x))(a))
    sin(a)
    >>> substitute(x, {x: x < y})
    Traceback (most recent call last):
        ...
    TypeError: cannot replace x, of kind NumberKind, with Lt(x, y), of kind BoolKind

A fresh name is the variable's name with ``_1``, ``_2``, ... appended (an
existing ``_<digits>`` suffix is replaced), taking the first one not used by
any symbol, of any kind, in the lambda or in the replacements made in it.

Known gaps:

- Lambdas that differ only in the names of their variables are still not
  equal: ``Lambda(x, x*x) != Lambda(t, t*t)``.
- The walk is recursive, so the depth of an expression is limited by
  Python's recursion limit.
- Nothing here simplifies: no application other than the one given to
  ``apply_lambda`` is reduced, and nothing is evaluated.
"""

import re

from ._core import Expr
from .functions import is_lambda

__all__ = ["apply_lambda", "free_symbols", "substitute"]


def free_symbols(e):
    """The set of symbols that occur in ``e`` and are not bound by an
    enclosing ``Lambda``."""
    if e.is_symbol:
        return {e}
    if e.head is None:
        return set()
    if is_lambda(e):
        return free_symbols(e.args[-1]) - set(e.args[:-1])
    result = free_symbols(e.head)
    for arg in e.args:
        result |= free_symbols(arg)
    return result


def substitute(e, replacements):
    """``e`` with each free occurrence of a key of ``replacements`` replaced
    by its value, all at the same time.

    Each key must be a symbol and each value an expression of the key's
    kind. Bound variables are renamed where a replacement would otherwise
    be captured. ``e`` itself is returned when nothing in it is replaced.
    """
    if not isinstance(e, Expr):
        raise TypeError(f"substitute expects an expression, got {e!r}")
    replacements = dict(replacements)
    for old, new in replacements.items():
        if not isinstance(old, Expr) or not old.is_symbol:
            raise TypeError(f"only a symbol can be replaced, got {old!r}")
        if not isinstance(new, Expr):
            raise TypeError(f"cannot replace {old!r} with {new!r}, which is not an expression")
        if new.kind is not old.kind:
            raise TypeError(
                f"cannot replace {old!r}, of kind {old.kind!r}, with {new!r}, of kind {new.kind!r}"
            )
    return _substitute(e, replacements)


def apply_lambda(e):
    """The body of the lambda ``e.head`` with the arguments of ``e`` for its
    variables: ``Lambda((x, y), body)(a, b)`` gives ``body`` with ``a`` for
    ``x`` and ``b`` for ``y``. Only the root is reduced."""
    if not isinstance(e, Expr) or e.head is None or not is_lambda(e.head):
        raise ValueError(f"apply_lambda expects a lambda applied to arguments, got {e!r}")
    variables, body = e.head.args[:-1], e.head.args[-1]
    # The core has checked the number and kinds of the arguments.
    return substitute(body, dict(zip(variables, e.args)))


def _substitute(e, replacements):
    if not replacements or e.head is None:
        return replacements.get(e, e) if e.is_symbol else e
    if is_lambda(e):
        return _substitute_lambda(e, replacements)
    head = _substitute(e.head, replacements)
    args = tuple(_substitute(arg, replacements) for arg in e.args)
    if head is e.head and all(new is old for new, old in zip(args, e.args)):
        return e
    return head(*args)


def _substitute_lambda(e, replacements):
    variables, body = e.args[:-1], e.args[-1]
    # The replacements that will actually be made in the body: not of the
    # lambda's own variables, and of symbols that occur free in it.
    free = free_symbols(body)
    inner = {
        old: new for old, new in replacements.items()
        if old in free and old not in variables
    }
    if not inner:
        return e

    # A variable that occurs free in a replacement would capture it.
    incoming = set()
    for new in inner.values():
        incoming |= free_symbols(new)
    if any(variable in incoming for variable in variables):
        used = _symbol_names(e)
        for new in inner.values():
            used |= _symbol_names(new)
        new_variables = []
        for variable in variables:
            if variable in incoming:
                fresh = variable.kind(_fresh_name(variable.name, used))
                used.add(fresh.name)
                inner[variable] = fresh
                variable = fresh
            new_variables.append(variable)
        variables = tuple(new_variables)

    return e.head(*variables, _substitute(body, inner))


def _symbol_names(e):
    """The names of all symbols in ``e``, free or bound."""
    if e.is_symbol:
        return {e.name}
    if e.head is None:
        return set()
    names = _symbol_names(e.head)
    for arg in e.args:
        names |= _symbol_names(arg)
    return names


def _fresh_name(name, used):
    """The first of ``name_1``, ``name_2``, ... not in ``used``, where a
    ``_<digits>`` suffix of ``name`` is dropped first."""
    base = re.sub(r"_\d+$", "", name) or name
    i = 1
    while f"{base}_{i}" in used:
        i += 1
    return f"{base}_{i}"

"""normalise applies the laws declared for each head, from the leaves up.

    >>> from nary import BoolKind, NumberKind, log, sin
    >>> from nary.logic import And, Not, Or, false, true
    >>> from nary.normalising import normalise
    >>> x, y, p, q = NumberKind("x"), NumberKind("y"), BoolKind("p"), BoolKind("q")
    >>> normalise(y + (x + 0) + x * 1), normalise(y * (2 * x) * 1)
    (Add(x, x, y), Mul(2, x, y))
    >>> normalise(And(q, Or(p, false), q, true)), normalise(Not(Not(p)))
    (And(p, q), p)
    >>> normalise(sin(x) * 0), normalise(log(x) * 0)
    (0, Mul(0, log(x)))
"""

from . import arithmetic_rules, logic_rules  # noqa: F401
from ._core import Expr
from ._identities import (
    absorbing, associative, commutative, idempotent, identities, identity, involution,
)
from .functions import is_lambda
from .kinds import Many
from .logic import true
from .rewriting import _has_a_value

__all__ = ["normalise"]


def normalise(e, known=None):
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    return _Normaliser(known or (lambda condition: False)).normal(e)


def _element(head, value):
    return value if isinstance(value, Expr) else head.kind.output(value)


def _variadic(head):
    inputs = head.kind.inputs
    return bool(inputs) and inputs[-1].family is Many


def _key(e):
    if e.is_literal:
        return 0, type(e.value).__name__, e.value
    if e.is_constant:
        return 1, e.name
    if e.is_symbol:
        return 2, e.name, e.kind.name
    return 3, _key(e.head), tuple(_key(arg) for arg in e.args)


class _Normaliser:
    def __init__(self, known):
        self.known, self.done, self.tables = known, {}, {}

    def laws(self, head):
        if head not in self.tables:
            self.tables[head] = {item.of: item for item in identities(head)}
        return self.tables[head]

    def normal(self, e):
        if e.head is None or is_lambda(e):
            return e
        if e not in self.done:
            head = self.normal(e.head)
            self.done[e] = self.node(head, [self.normal(arg) for arg in e.args])
        return self.done[e]

    def holds(self, condition):
        condition = self.normal(condition)
        return condition == true or self.known(condition) is True

    def has_a_value(self, e):
        return _has_a_value(e, self.holds)

    def node(self, head, args):
        laws = self.laws(head)
        for needs, step in _STEPS:
            if all(law in laws for law in needs):
                result = step(self, head, laws, args)
                if isinstance(result, Expr):
                    return result
                args = result
        return head(*args)


def _flatten(n, head, laws, args):
    return [part for arg in args for part in (arg.args if arg.head == head else (arg,))]


def _sort(n, head, laws, args):
    return sorted(args, key=_key)


def _drop_duplicates(n, head, laws, args):
    return [arg for i, arg in enumerate(args) if arg not in args[:i]]


def _absorb(n, head, laws, args):
    z = _element(head, laws[absorbing].args[0])
    if z in args and all(n.has_a_value(arg) for arg in args if arg != z):
        return z
    return args


def _drop_units(n, head, laws, args):
    if not _variadic(head):
        return args
    unit = _element(head, laws[identity].args[0])
    kept = [arg for arg in args if arg != unit]
    if len(kept) < 2:
        return kept[0] if kept else unit
    return kept


def _cancel(n, head, laws, args):
    (arg,) = args
    return arg.args[0] if arg.head == head else args


_STEPS = [
    ((associative,), _flatten),
    ((commutative,), _sort),
    ((idempotent,), _drop_duplicates),
    ((absorbing,), _absorb),
    ((identity,), _drop_units),
    ((involution,), _cancel),
]

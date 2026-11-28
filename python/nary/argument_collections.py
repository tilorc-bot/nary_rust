"""
    >>> from nary import Add, Mul, NumberKind, log, sin
    >>> from nary.rewriting import _has_a_value
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> has_a_value = lambda e: _has_a_value(e, lambda condition: False)
    >>> normalise_collection(Mul, [y, Mul(x, 2), NumberKind(1)], has_a_value)
    Mul(2, x, y)
    >>> zero = NumberKind(0)
    >>> normalise_collection(Mul, [sin(x), zero], has_a_value)
    0
    >>> normalise_collection(Mul, [log(x), zero], has_a_value)
    Mul(0, log(x))
    >>> normalise_collection(Add, [], has_a_value), normalise_collection(sin, [x], has_a_value)
    (0, sin(x))
"""

from __future__ import annotations

from itertools import groupby
from typing import Callable

from ._core import Expr
from .properties import declared_properties, is_property

__all__ = ["acting_properties", "collection_step", "count_step", "normalise_collection"]

_steps = {}


def collection_step(name: str, multiset_only: bool = False) -> Callable:
    if not is_property(name):
        raise ValueError(f"{name} is not a property")
    if name in _steps:
        raise ValueError(f"{name} already has a step")

    def register(step: Callable) -> Callable:
        _steps[name] = (len(_steps), step, multiset_only)
        return step

    return register


def count_step(name: str) -> Callable:
    register = collection_step(name)

    def register_counts(recount: Callable) -> Callable:
        def step(head, args, has_a_value, *value):
            kept = []
            for arg, run in groupby(args):
                count = len(list(run))
                new = recount(arg, count, *value)
                kept += [arg] * (new if new or has_a_value(arg) else count)
            return kept

        register(step)
        return recount

    return register_counts


def _acting(head: Expr, unordered: bool) -> dict[str, object]:
    declared = declared_properties(head)
    return {
        name: declared[name]
        for name in sorted(declared.keys() & _steps.keys(), key=lambda name: _steps[name][0])
        if declared[name] is not None and declared[name] is not False
        and (unordered or not _steps[name][2])
    }


def acting_properties(head: Expr) -> list[str]:
    """
    >>> from nary import Mul, Pow
    >>> acting_properties(Mul), acting_properties(Pow)
    (['identity_element', 'absorbing_element'], [])
    """
    return list(_acting(head, head.is_commutative))


def _arrange(unordered: bool, args: list[Expr]) -> list[Expr]:
    return sorted(args, key=repr) if unordered else args


def _settle(head: Expr, unordered: bool, args: list[Expr], has_a_value: Callable) -> list[Expr]:
    acting = _acting(head, unordered).items()
    while True:
        args = _arrange(unordered, args)
        stepped = args
        for name, value in acting:
            given = () if name.startswith("is_") else (value,)
            stepped = _steps[name][1](head, stepped, has_a_value, *given)
        if stepped == args:
            return args
        args = stepped


def _spliced(head: Expr, arg: Expr) -> tuple[Expr, ...]:
    return arg.args if not arg.is_atom and arg.head == head else (arg,)


def normalise_collection(
    head: Expr, args: list[Expr], has_a_value: Callable[[Expr], bool]
) -> Expr:
    associative, unordered = head.is_associative, head.is_commutative
    if associative:
        args = [inner for arg in args for inner in _spliced(head, arg)]
    if associative or len(args) == 2:
        args = _settle(head, unordered, args, has_a_value)
        if len(args) == 1:
            return args[0]
        if not args and head.identity_element is not None:
            return head.identity_element
    return head(*_arrange(unordered, args))


@count_step("identity_element")
def _drop_identity(arg: Expr, count: int, identity: Expr) -> int:
    return 0 if arg == identity else count


@collection_step("absorbing_element")
def _absorb(head, args, has_a_value, absorbing):
    return [absorbing] if absorbing in args and all(map(has_a_value, args)) else args


@count_step("is_idempotent")
def _keep_one(arg: Expr, count: int) -> int:
    return min(count, 1)

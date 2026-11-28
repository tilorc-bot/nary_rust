from __future__ import annotations

from itertools import groupby
from typing import Callable

from ._core import Expr
from .properties import declared_properties, is_property

__all__ = ["acting_properties", "normalise_collection", "per_argument", "step"]

_steps = {}


def step(name: str, multiset_only: bool = False) -> Callable:
    """Register the step of the property name.

    Args:
        name: A name declare_property has declared.
        multiset_only: If True, the step acts only on heads whose is_commutative is True.

    Returns:
        A decorator for fn. fn is called as fn(head, args) for an is_ name and as
        fn(head, args, value) otherwise, with value = getattr(head, name), and returns
        the new list of arguments. If an argument that may have no value is missing
        from that list, the list is not used.

    >>> step("kind")
    Traceback (most recent call last):
        ...
    ValueError: kind is not a property
    """
    if not is_property(name):
        raise ValueError(f"{name} is not a property")
    if name in _steps:
        raise ValueError(f"{name} already has a step")

    def register(fn: Callable) -> Callable:
        _steps[name] = (len(_steps), fn, multiset_only)
        return fn

    return register


def per_argument(fn: Callable) -> Callable:
    """Turn a law about one argument and its copies into a function for step(name).

    Args:
        fn: Called as fn(arg, copies) or fn(arg, copies, value) once for each run of
            equal neighbouring arguments, with copies the length of the run. Returns
            how many copies to keep.

    Returns:
        A function to decorate with step(name).

    >>> from nary import NumberKind
    >>> x = NumberKind("x")
    >>> keep_an_odd_number = per_argument(lambda arg, copies: copies % 2)
    >>> keep_an_odd_number(None, [x, x, x]), keep_an_odd_number(None, [x, x])
    ([x], [])
    """
    def keep(head, copies, *value):
        return copies[:1] * fn(copies[0], len(copies), *value)

    keep.copies_to_keep = fn
    return keep


def _acting(head: Expr, unordered: bool) -> dict[str, object]:
    declared = declared_properties(head)
    return {
        name: declared[name]
        for name in sorted(declared.keys() & _steps.keys(), key=lambda name: _steps[name][0])
        if declared[name] is not None and declared[name] is not False
        and (unordered or not _steps[name][2])
    }


def acting_properties(head: Expr) -> list[str]:
    """The properties of head whose steps act on its arguments.

    Args:
        head: A function, such as e.head.

    Returns:
        Their names, in the order their steps were registered.

    >>> from nary import Mul, Pow
    >>> acting_properties(Mul), acting_properties(Pow)
    (['identity_element', 'absorbing_element'], [])
    """
    return list(_acting(head, head.is_commutative))


def _arrange(unordered: bool, args: list[Expr]) -> list[Expr]:
    return sorted(args, key=repr) if unordered else args


def _guarded(fn: Callable, head: Expr, args: list, has_a_value: Callable, *value) -> list[Expr]:
    groups = [list(run) for _, run in groupby(args)] if hasattr(fn, "copies_to_keep") else [args]
    kept = []
    for before in groups:
        after = fn(head, before, *value)
        kept += after if all(map(has_a_value, set(before) - set(after))) else before
    return kept


def _settle(head: Expr, unordered: bool, args: list[Expr], has_a_value: Callable) -> list[Expr]:
    acting = _acting(head, unordered).items()
    while True:
        args = _arrange(unordered, args)
        stepped = args
        for name, value in acting:
            given = () if name.startswith("is_") else (value,)
            stepped = _guarded(_steps[name][1], head, stepped, has_a_value, *given)
        if stepped == args:
            return args
        args = stepped


def _spliced(head: Expr, arg: Expr) -> tuple[Expr, ...]:
    return arg.args if not arg.is_atom and arg.head == head else (arg,)


def normalise_collection(head: Expr, args: list[Expr], has_a_value: Callable) -> Expr:
    """Build head(*args), applying the steps that act on head.

    Args:
        head: What e.head normalised to.
        args: What each of e.args normalised to.
        has_a_value: Called as has_a_value(arg). An argument is erased only where this
            returns True.

    Returns:
        head(*args) after the steps, or the one argument or the identity element left.

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


@step("identity_element")
@per_argument
def _no_copies_of_the_identity(arg: Expr, copies: int, identity: Expr) -> int:
    return 0 if arg == identity else copies


@step("is_idempotent")
@per_argument
def _one_copy_of_each(arg: Expr, copies: int) -> int:
    return min(copies, 1)


@step("absorbing_element")
def _only_the_absorbing_element(head: Expr, args: list[Expr], absorbing: Expr) -> list[Expr]:
    return [absorbing] if absorbing in args else args

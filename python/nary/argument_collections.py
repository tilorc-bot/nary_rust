from __future__ import annotations

from itertools import groupby
from typing import Callable

from ._core import Expr
from .properties import declared_properties, is_property

__all__ = ["acting_properties", "normalise_collection", "per_argument", "step"]

_steps = {}


def step(name: str, multiset_only: bool = False) -> Callable:
    """Register a function that changes the arguments of a head that has the property name.

    Args:
        name: A property, already declared with declare_property(name).
        multiset_only: If True, the function is used only where head.is_commutative.

    Returns:
        A decorator. The function it registers is called as fn(head, args) if name
        starts with is_, and as fn(head, args, getattr(head, name)) otherwise. It returns
        the new args.

    >>> from nary import Many, NumberKind, declare_function, log
    >>> from nary.logic import true
    >>> from nary.normalising import normalise
    >>> from nary.properties import declare_properties, declare_property
    >>> declare_property("inverse_function")
    >>> @step("inverse_function", multiset_only=True)
    ... def cancel(head, args, inverse):
    ...     for arg in args:
    ...         if inverse(arg) in args:
    ...             return [other for other in args if other not in (arg, inverse(arg))]
    ...     return args
    >>> undo = declare_function("undo", NumberKind, returns=NumberKind, domain=true)
    >>> Tally = declare_function("Tally", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(Tally, is_associative=True, is_commutative=True, inverse_function=undo)
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> normalise(Tally(x, y, undo(x)))
    y

    What fn returns is not used if it leaves out an argument that may have no value.

    >>> normalise(Tally(log(x), y, undo(log(x))))
    Tally(log(x), undo(log(x)), y)
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
    """Make the function for step(name) from one that says how many copies of an argument stay.

    Args:
        fn: Called as fn(arg, copies) if name starts with is_, and as
            fn(arg, copies, getattr(head, name)) otherwise. copies counts the arguments
            equal to arg that are next to each other, which is all of them where
            head.is_commutative. It returns how many of them to keep.

    Returns:
        The function to register with step(name).

    >>> from nary import Many, NumberKind, declare_function
    >>> from nary.logic import true
    >>> from nary.normalising import normalise
    >>> from nary.properties import declare_properties, declare_property
    >>> declare_property("is_cancelled_by_a_copy")
    >>> @step("is_cancelled_by_a_copy")
    ... @per_argument
    ... def keep_one_of_an_odd_number(arg, copies):
    ...     return copies % 2
    >>> Toggle = declare_function("Toggle", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(
    ...     Toggle, is_associative=True, is_commutative=True, is_cancelled_by_a_copy=True,
    ... )
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> normalise(Toggle(x, y, x)), normalise(Toggle(x, y, x, x))
    (y, Toggle(x, y))
    >>> Queue = declare_function("Queue", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(Queue, is_associative=True, is_cancelled_by_a_copy=True)
    >>> normalise(Queue(x, x, y)), normalise(Queue(x, y, x))
    (y, Queue(x, y, x))
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
    """The properties of head that have a function registered with step.

    Args:
        head: A function, such as e.head.

    Returns:
        Their names, in the order normalise uses their functions.

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
    """Build head(*args), with args changed by the functions that step registered.

    Args:
        head: A function.
        args: Its arguments, each already normalised.
        has_a_value: Called as has_a_value(arg). An argument is removed only where this
            returns True.

    Returns:
        head applied to the arguments that are left. If one is left, that argument.
        If none is left and head.identity_element is not None, head.identity_element.

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

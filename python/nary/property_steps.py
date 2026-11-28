from __future__ import annotations

from itertools import groupby
from typing import Callable, NamedTuple

from ._core import Expr
from .literal_evaluation import with_literals_combined
from .properties import is_property

__all__ = ["apply_property_steps", "step"]

_sort_key = repr


class _Step(NamedTuple):
    function: Callable
    commutative_only: bool
    per_argument: bool


_step_of_property: dict[str, _Step] = {}


def step(name: str, commutative_only: bool = False, per_argument: bool = False) -> Callable:
    """Register a function that changes the arguments of a head that has the property name.

    Args:
        name: A property, already declared with declare_property(name).
        commutative_only: If True, the function is used only where head.is_commutative.
        per_argument: If True, the function is called as fn(arg, copies) and returns how
            many copies of arg to keep. copies counts the arguments equal to arg that are
            next to each other, which is all of them where head.is_commutative.

    Returns:
        A decorator. Unless per_argument is True, the function it registers is called as
        fn(head, args) and returns the new args. Either way getattr(head, name) is passed
        as one more argument, unless name starts with is_.

    >>> from nary import Many, NumberKind, declare_function, log
    >>> from nary.logic import true
    >>> from nary.normalising import normalise
    >>> from nary.properties import declare_properties, declare_property
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> declare_property("is_cancelled_by_a_copy")
    >>> @step("is_cancelled_by_a_copy", per_argument=True)
    ... def keep_one_of_an_odd_number(arg, copies):
    ...     return copies % 2
    >>> Toggle = declare_function("Toggle", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(
    ...     Toggle, is_associative=True, is_commutative=True, is_cancelled_by_a_copy=True,
    ... )
    >>> normalise(Toggle(x, y, x)), normalise(Toggle(x, y, x, x))
    (y, Toggle(x, y))
    >>> Queue = declare_function("Queue", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(Queue, is_associative=True, is_cancelled_by_a_copy=True)
    >>> normalise(Queue(x, x, y)), normalise(Queue(x, y, x))
    (y, Queue(x, y, x))

    A function that needs all the arguments at once, and the value of its property:

    >>> declare_property("inverse_function")
    >>> @step("inverse_function", commutative_only=True)
    ... def cancel(head, args, inverse):
    ...     for arg in args:
    ...         if inverse(arg) in args:
    ...             return [other for other in args if other not in (arg, inverse(arg))]
    ...     return args
    >>> undo = declare_function("undo", NumberKind, returns=NumberKind, domain=true)
    >>> Tally = declare_function("Tally", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(Tally, is_associative=True, is_commutative=True, inverse_function=undo)
    >>> normalise(Tally(x, y, undo(x)))
    y

    What a function returns is not used if it leaves out an argument that may have no value.

    >>> normalise(Tally(log(x), y, undo(log(x))))
    Tally(log(x), undo(log(x)), y)
    """
    if not is_property(name):
        raise ValueError(f"{name} is not a property")
    if name in _step_of_property:
        raise ValueError(f"{name} already has a step")

    def register(function: Callable) -> Callable:
        _step_of_property[name] = _Step(function, commutative_only, per_argument)
        return function

    return register


def apply_property_steps(head: Expr, args: list[Expr], has_a_value: Callable) -> Expr:
    """Build head(*args), with args changed by the functions that step registered.

    Args:
        head: A function.
        args: Its arguments, each already normalised. Where head.is_associative, none
            of them has head as its own head.
        has_a_value: Called as has_a_value(arg). An argument is removed only where this
            returns True.

    Returns:
        head applied to the arguments that are left. If one is left, that argument.
        If none is left and head.identity_element is not None, head.identity_element.

    >>> from nary import Add, Mul, NumberKind, log, sin
    >>> from nary.rewriting import _has_a_value
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> has_a_value = lambda e: _has_a_value(e, lambda condition: False)
    >>> apply_property_steps(Mul, [y, x, NumberKind(2), NumberKind(1)], has_a_value)
    Mul(2, x, y)
    >>> zero = NumberKind(0)
    >>> apply_property_steps(Mul, [sin(x), zero], has_a_value)
    0
    >>> apply_property_steps(Mul, [log(x), zero], has_a_value)
    Mul(0, log(x))
    >>> apply_property_steps(Add, [], has_a_value), apply_property_steps(sin, [x], has_a_value)
    (0, sin(x))
    """
    commutative = head.is_commutative
    if head.is_associative or len(args) == 2:
        args = _apply_steps_until_unchanged(head, args, commutative, has_a_value)
        if len(args) == 1:
            return args[0]
        if not args and head.identity_element is not None:
            return head.identity_element
    if commutative:
        args = sorted(args, key=_sort_key)
    return head(*args)


def _apply_steps_until_unchanged(
    head: Expr, args: list[Expr], commutative: bool, has_a_value: Callable,
) -> list[Expr]:
    properties = head.properties
    seen_before = set()
    while True:
        if commutative:
            args = sorted(args, key=_sort_key)
        if tuple(args) in seen_before:
            raise RuntimeError(f"the steps for {head!r} never stop changing {args!r}")
        seen_before.add(tuple(args))
        args_after_steps = args
        for name, value in properties.items():
            registered = _step_of_property.get(name)
            if registered is None or (registered.commutative_only and not commutative):
                continue
            declared_value = () if name.startswith("is_") else (value,)
            args_after_steps = _apply_step_keeping_arguments_without_a_value(
                registered, head, args_after_steps, declared_value, has_a_value,
            )
        if head.is_associative:
            args_after_steps = with_literals_combined(head, args_after_steps)
        if args_after_steps == args:
            return args
        args = args_after_steps


def _apply_step_keeping_arguments_without_a_value(
    registered: _Step, head: Expr, args: list[Expr], declared_value: tuple, has_a_value: Callable,
) -> list[Expr]:
    if not registered.per_argument:
        new_args = registered.function(head, args, *declared_value)
        if head.is_associative:
            _raise_if_an_added_argument_has_the_head(head, args, new_args, registered)
        removed = set(args) - set(new_args)
        return new_args if all(map(has_a_value, removed)) else args
    new_args = []
    for arg, equal_args in groupby(args):
        copies = len(list(equal_args))
        copies_to_keep = registered.function(arg, copies, *declared_value)
        if copies_to_keep == 0 and not has_a_value(arg):
            copies_to_keep = copies
        new_args += [arg] * copies_to_keep
    return new_args


def _raise_if_an_added_argument_has_the_head(
    head: Expr, args: list[Expr], new_args: list[Expr], registered: _Step,
) -> None:
    for added in set(new_args) - set(args):
        if not added.is_atom and added.head == head:
            raise ValueError(
                f"the step {registered.function.__name__} put {added!r} among the arguments "
                f"of {head!r}: {head!r} is associative, so the step has to put the arguments "
                f"of {added!r} there instead"
            )


@step("identity_element", per_argument=True)
def _no_copies_of_the_identity(arg: Expr, copies: int, identity: Expr) -> int:
    return 0 if arg == identity else copies


@step("is_idempotent", per_argument=True)
def _one_copy_of_each(arg: Expr, copies: int) -> int:
    return min(copies, 1)


@step("absorbing_element")
def _only_the_absorbing_element(head: Expr, args: list[Expr], absorbing: Expr) -> list[Expr]:
    return [absorbing] if absorbing in args else args

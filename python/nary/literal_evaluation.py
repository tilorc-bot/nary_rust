"""A function may be declared with evaluate_literals, which computes it on the values of literals.

    >>> from nary import Add, Many, NumberKind, Pow, declare_function, sin
    >>> from nary.logic import true
    >>> from nary.normalising import normalise
    >>> x = NumberKind("x")
    >>> Add.evaluate_literals(2, 3), Pow.evaluate_literals(NumberKind(2), NumberKind(3))
    (5, 8)
    >>> Add.evaluate_literals(x, 3), Pow.evaluate_literals(0, -1), sin.evaluate_literals
    (None, None, None)
    >>> Largest = declare_function(
    ...     "Largest", Many(NumberKind), returns=NumberKind, domain=true, evaluate_literals=max,
    ... )
    >>> normalise(Largest(2, 3))
    3
"""

from __future__ import annotations

from itertools import groupby

from ._core import Expr

__all__ = ["with_literals_combined"]


def with_literals_combined(head: Expr, args: list[Expr]) -> list[Expr]:
    """Replace literals next to each other, or anywhere where head.is_commutative, by one literal.

    Args:
        head: A function with head.is_associative.
        args: Its arguments.

    Returns:
        The arguments with fewer literals, or args itself if no literals were combined.

    >>> from nary import Add, Many, NumberKind, declare_function
    >>> from nary.logic import true
    >>> from nary.properties import declare_properties
    >>> one, two, four, x = NumberKind(1), NumberKind(2), NumberKind(4), NumberKind("x")
    >>> with_literals_combined(Add, [one, two, x, four])
    [7, x]
    >>> Last = declare_function(
    ...     "Last", Many(NumberKind), returns=NumberKind, domain=true,
    ...     evaluate_literals=lambda *values: values[-1],
    ... )
    >>> declare_properties(Last, is_associative=True)
    >>> with_literals_combined(Last, [one, two, x, four])
    [2, x, 4]
    """
    evaluate_literals = head.evaluate_literals
    if evaluate_literals is None:
        return args
    literals_together = (
        sorted(args, key=lambda arg: not arg.is_literal) if head.is_commutative else args
    )
    new_args = []
    for is_literal, neighbours in groupby(literals_together, key=lambda arg: arg.is_literal):
        neighbours = list(neighbours)
        literal = evaluate_literals(*neighbours) if is_literal and len(neighbours) > 1 else None
        new_args += neighbours if literal is None else [literal]
    return new_args if len(new_args) < len(args) else args

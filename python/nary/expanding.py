"""expand multiplies out what normalise leaves as a product of sums.

    >>> from nary import NumberKind
    >>> from nary.expanding import expand
    >>> from nary.normalising import normalise
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> normalise(2 * (x + 1)), expand(2 * (x + 1))
    (Mul(2, Add(1, x)), Add(2, Mul(2, x)))
    >>> expand((x + y) * (x - y))
    Add(Mul(-1, Pow(y, 2)), Pow(x, 2))
"""

from __future__ import annotations

from collections.abc import Callable

from ._core import Expr
from .normalising import normalise
from .properties import heads_declaring
from .traversal import bottom_up

__all__ = ["expand"]


def expand(e: Expr, known: Callable[[Expr], object] | None = None) -> Expr:
    """Distribute each F(..., G(...), ...) with F.distributes_over == G, then normalise.

    Args:
        e: The expression to expand.
        known: Passed to normalise.

    Returns:
        The expanded expression.

    >>> from nary import NumberKind, Pow
    >>> x = NumberKind("x")
    >>> expand(Pow(x + 1, 3))
    Add(1, Mul(3, Pow(x, 2)), Mul(3, x), Pow(x, 3))
    >>> expand(Pow(x + 1, -1))
    Pow(Add(1, x), -1)

    Heads that distribute over each other, such as And and Or, are left as they are.

    >>> from nary import BoolKind
    >>> from nary.logic import And, Or
    >>> p, q, r = BoolKind("p"), BoolKind("q"), BoolKind("r")
    >>> expand(And(p, Or(q, r)))
    And(Or(q, r), p)
    """

    def multiplied_out(head: Expr, args: list[Expr]) -> Expr:
        power_of = _product_that_a_power_repeats(head, args)
        if power_of is not None:
            return multiplied_out(power_of, [args[0]] * args[1].value)
        over = head.distributes_over
        if over is None or over.distributes_over == head:
            return head(*args)
        if not any(_terms(arg, over) != [arg] for arg in args):
            return head(*args)
        if not head.is_associative and len(args) != 2:
            return head(*args)
        product = args[0]
        for arg in args[1:]:
            pairs = [
                multiplied_out(head, [s, t])
                for s in _terms(product, over) for t in _terms(arg, over)
            ]
            product = normalise(over(*pairs), known)
        return product

    return normalise(bottom_up(multiplied_out)(normalise(e, known)), known)


def _terms(e: Expr, total: Expr) -> list[Expr]:
    return list(e.args) if not e.is_atom and e.head == total else [e]


def _product_that_a_power_repeats(head: Expr, args: list[Expr]) -> Expr | None:
    """The F with F.power_function == head that distributes over the base, if the exponent is above 0.

    >>> from nary import Mul, NumberKind, Pow
    >>> x = NumberKind("x")
    >>> _product_that_a_power_repeats(Pow, [x + 1, NumberKind(2)])
    Mul
    >>> _product_that_a_power_repeats(Pow, [x, NumberKind(2)]) is None
    True
    """
    if len(args) != 2 or args[0].is_atom or not args[1].is_literal:
        return None
    exponent = args[1].value
    if not (isinstance(exponent, int) and exponent > 0):
        return None
    for product in heads_declaring("power_function", head):
        if product.distributes_over == args[0].head:
            return product
    return None

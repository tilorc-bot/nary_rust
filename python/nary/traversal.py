from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TypeVar

from ._core import Expr
from .functions import is_lambda

__all__ = ["bottom_up"]

_Result = TypeVar("_Result")


def _never(head: Expr) -> bool:
    return False


def bottom_up(
    at_node: Callable[[Expr | _Result, list[Expr | _Result]], _Result],
    flat: Callable[[Expr], bool] = _never,
) -> Callable[[Expr], Expr | _Result]:
    """Return a function walk(e) that gives the result for an expression, children first.

    at_node(head, args) is called once for each application, with its head and
    the list of its arguments already processed, and returns the result for
    that node. Atoms and lambdas are returned as they are; at_node is not
    called for them. Each distinct subexpression is processed once per walker:
    walk may be called again, also from inside at_node, and shares those results.

    flat(head) is asked with a node's unprocessed head. When it is true, every
    argument that is an application of the same head is expanded in place,
    through every nested layer, so at_node is called once for the whole run with
    the arguments in written order; the inner nodes are neither built nor passed
    to at_node. An argument that only becomes an application of that head once
    it is processed is not expanded.

    The walk uses an explicit stack, so depth is limited by memory, not by the
    recursion limit.

    >>> from nary import Add, NumberKind, sin
    >>> x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
    >>> def show(head, args):
    ...     print(head, args)
    ...     return head(*args)
    >>> bottom_up(show)(sin(x + y) + z)
    Add [x, y]
    sin [Add(x, y)]
    Add [sin(Add(x, y)), z]
    Add(sin(Add(x, y)), z)

    A repeated subexpression is processed once, also across calls of walk.

    >>> walk = bottom_up(show)
    >>> walk(sin(x + y) * sin(x + y))
    Add [x, y]
    sin [Add(x, y)]
    Mul [sin(Add(x, y)), sin(Add(x, y))]
    Mul(sin(Add(x, y)), sin(Add(x, y)))
    >>> walk(sin(x + y))
    sin(Add(x, y))

    With flat, nested applications of a flat head become one call, in written order.

    >>> bottom_up(show, flat=lambda head: head == Add)(x + (y + z) + sin(x + y))
    Add [x, y]
    sin [Add(x, y)]
    Add [x, y, z, sin(Add(x, y))]
    Add(x, y, z, sin(Add(x, y)))
    """
    done: dict[Expr, _Result] = {}

    def walk(root: Expr) -> Expr | _Result:
        results: list[Expr | _Result] = []
        stack: list[tuple[Expr | None, Iterator[Expr], list[Expr | _Result], Expr | None]] = [
            (None, iter([root]), results, None)
        ]
        while stack:
            node, pending, done_args, run_head = stack[-1]
            for e in pending:
                if run_head is not None and not e.is_atom and e.head == run_head:
                    stack.append((None, iter(e.args), done_args, run_head))
                    break
                if e.is_atom or is_lambda(e):
                    done_args.append(e)
                elif e in done:
                    done_args.append(done[e])
                else:
                    new_run_head = e.head if flat(e.head) else None
                    stack.append((e, iter((e.head, *e.args)), [], new_run_head))
                    break
            else:
                stack.pop()
                if node is not None:
                    head, *args = done_args
                    value = done[node] = at_node(head, args)
                    stack[-1][2].append(value)
        return results[0]

    return walk

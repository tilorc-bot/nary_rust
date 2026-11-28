from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TypeVar

from ._core import Expr
from .functions import is_lambda

__all__ = ["bottom_up"]

Result = TypeVar("Result")


def _never(head: Expr) -> bool:
    return False


def bottom_up(
    at_node: Callable[[Expr | Result, list[Expr | Result]], Result],
    flat: Callable[[Expr], bool] = _never,
) -> Callable[[Expr], Expr | Result]:
    """Return a function walk(e).

    walk(e) calls at_node for e and for the expressions inside it, each before
    any expression that contains it, and returns what at_node returned for e.

    If e.is_atom or is_lambda(e) is true, walk(e) returns e itself: at_node is
    not called, and nothing inside a lambda is visited.

    Otherwise walk(e) is at_node(head, args), with head = walk(e.head), so the
    head is included, and args = [walk(a) for a in e.args].

    at_node must depend only on head and args. walk remembers what at_node
    returned for each e, so when the same e occurs again at_node is not called
    a second time. The values are kept as long as walk exists, also across
    calls, and walk may be called from inside at_node.

    flat is optional; by default nothing is merged. It is called as
    flat(e.head), with the head as written in e. When it is true, each a in
    e.args with a.head == e.head is replaced by a.args, and so on inside those,
    so at_node is called once for e, with all the arguments in order, and not
    for the replaced a. A replaced a gets no remembered value: if it also
    occurs where it is not replaced, at_node is called for it there.

    Only what is written in e is replaced. In Add(x, Mul(1, Add(y, z))) the
    inner Add is an argument of Mul, so it is not merged, even if at_node turns
    the Mul into Add(y, z).

    walk keeps its own stack, so e can be nested as deeply as memory allows,
    whatever Python's recursion limit.

    >>> from nary import Add, Mul, NumberKind, sin
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

    An Add that only appears once at_node has handled the Mul around it is not merged.

    >>> def drop_ones(head, args):
    ...     print(head, args)
    ...     args = [a for a in args if a != NumberKind(1)]
    ...     return args[0] if len(args) == 1 else head(*args)
    >>> bottom_up(drop_ones, flat=lambda head: head == Add)(Add(x, Mul(1, Add(y, z))))
    Add [y, z]
    Mul [1, Add(y, z)]
    Add [x, Add(y, z)]
    Add(x, Add(y, z))
    """
    done: dict[Expr, Result] = {}

    def walk(root: Expr) -> Expr | Result:
        results: list[Expr | Result] = []
        stack: list[tuple[Expr | None, Iterator[Expr], list[Expr | Result], Expr | None]] = [
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

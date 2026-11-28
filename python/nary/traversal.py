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

    walk(e) calls at_node(head, args) for e and for everything inside it that has a head,
    innermost first, and returns what at_node returned for e. head and args are what walk
    returned for e.head and each of e.args.

    If flat(e.head) is true, arguments of e with that same head are replaced by their own
    arguments first, and so on.

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
    >>> bottom_up(show)(sin(x) * sin(x))
    sin [x]
    Mul [sin(x), sin(x)]
    Mul(sin(x), sin(x))
    >>> bottom_up(show, flat=lambda head: head == Add)((x + y) + (y + z))
    Add [x, y, y, z]
    Add(x, y, y, z)

    An Add that appears only once at_node has handled the Mul around it is not merged.

    >>> def unwrap(head, args):
    ...     return args[1] if head == Mul and args[0] == NumberKind(1) else head(*args)
    >>> bottom_up(unwrap, flat=lambda head: head == Add)(x + Mul(1, y + z))
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

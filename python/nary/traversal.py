from __future__ import annotations

from collections.abc import Callable, Iterator

from ._core import Expr
from .functions import is_lambda

__all__ = ["bottom_up", "bottom_up_every_node"]


def _never(head: Expr) -> bool:
    return False


def bottom_up(
    at_node: Callable[[Expr, list[Expr]], Expr],
    flat: Callable[[Expr], bool] = _never,
) -> Callable[[Expr], Expr]:
    """Return a function walk(e).

    Args:
        at_node: Called as at_node(head, args) for e and for everything inside it that
            has a head, innermost first, skipping lambdas whole. head and args are what
            walk returned for e.head and each of e.args.
        flat: Called as flat(e.head). If true, arguments of e with that same head are
            replaced by their own arguments first, and so on.

    Returns:
        walk, where walk(e) is what at_node returned for e, or e itself if at_node
        was not called for e.

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
    done: dict[Expr, Expr] = {}

    def walk(root: Expr) -> Expr:
        results: list[Expr] = []
        stack: list[tuple[Expr | None, Iterator[Expr], list[Expr], Expr | None]] = [
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


def bottom_up_every_node(at_node: Callable[[Expr, list[Expr]], Expr]) -> Callable[[Expr], Expr]:
    """Return a function walk(e) that calls at_node wherever a constructor would run.

    Args:
        at_node: Called as at_node(head, args) for e and for everything inside it that
            has a head, innermost first, skipping lambdas whole. head and args are what
            walk returned for e.head and each of e.args.

    Returns:
        walk, where walk(e) is what at_node returned for e, or e itself if at_node
        was not called for e.

    >>> from nary import Add, NumberKind, sin
    >>> x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
    >>> def show(head, args):
    ...     print(head, args)
    ...     return head(*args)
    >>> bottom_up_every_node(show)((x + y) + z)
    Add [x, y]
    Add [Add(x, y), z]
    Add(Add(x, y), z)
    >>> bottom_up(show, flat=lambda head: head == Add)((x + y) + z)
    Add [x, y, z]
    Add(x, y, z)
    >>> bottom_up_every_node(show)(sin(x) * sin(x))
    sin [x]
    sin [x]
    Mul [sin(x), sin(x)]
    Mul(sin(x), sin(x))
    """
    def walk(e: Expr) -> Expr:
        if e.is_atom or is_lambda(e):
            return e
        return at_node(walk(e.head), [walk(arg) for arg in e.args])

    return walk

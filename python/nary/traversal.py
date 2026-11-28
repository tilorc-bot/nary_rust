from __future__ import annotations

from collections.abc import Callable, Iterator

from ._core import Expr
from .functions import is_lambda

__all__ = ["bottom_up"]


def _never(head: Expr) -> bool:
    return False


def _is(a: Expr, b: Expr) -> bool:
    return a is b


def bottom_up(
    at_node: Callable[[Expr, list[Expr]], Expr],
    flat: Callable[[Expr], bool] = _never,
    orderless: Callable[[Expr], bool] = _never,
    again: bool = False,
) -> Callable[[Expr], Expr]:
    """Return a function walk(e).

    Args:
        at_node: Called as at_node(head, args) for e and for everything inside it that
            has a head, innermost first, skipping lambdas whole. head and args are what
            walk returned for e.head and each of e.args.
        flat: Called as flat(e.head). If true, arguments of e with that same head are
            replaced by their own arguments first, and so on.
        orderless: Called as orderless(e.head). If true, at_node gets the args sorted by repr.
        again: If True, whatever at_node returns other than head(*args) is walked in turn,
            raising RuntimeError if it is already being walked.

    Returns:
        walk, where walk(e) is what at_node returned for e, or e itself if at_node
        was not called for e. With again, what at_node last returned.

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
    >>> bottom_up(unwrap, flat=lambda head: head == Add, again=True)(Mul(1, Mul(1, x)))
    x
    """
    done: dict[Expr, Expr] = {}

    def walk(root: Expr) -> Expr:
        results: list[Expr] = []
        stack: list[tuple[Expr | None, Iterator[Expr], list[Expr], Expr | None, Expr | None]] = [
            (None, iter([root]), results, None, None)
        ]
        walking_again: set[Expr] = set()
        while stack:
            node, pending, done_args, run_head, walked_again = stack[-1]
            for e in pending:
                if run_head is not None and not e.is_atom and e.head == run_head:
                    stack.append((None, iter(e.args), done_args, run_head, None))
                    break
                if e.is_atom or is_lambda(e):
                    done_args.append(e)
                elif e in done:
                    done_args.append(done[e])
                else:
                    new_run_head = e.head if flat(e.head) else None
                    stack.append((e, iter((e.head, *e.args)), [], new_run_head, None))
                    break
            else:
                stack.pop()
                if node is None:
                    continue
                if walked_again is not None:
                    walking_again.discard(walked_again)
                    value = done[node] = done_args[0]
                    stack[-1][2].append(value)
                    continue
                head, *args = done_args
                if orderless(node.head):
                    args.sort(key=repr)
                value = at_node(head, args)
                if again:
                    if value.is_atom or value.head != head or list(value.args) != args:
                        if value in walking_again:
                            message = f"the results of at_node never stop changing {value!r}"
                            raise RuntimeError(message)
                        walking_again.add(value)
                        stack.append((node, iter([value]), [], None, value))
                        continue
                    same_args = len(args) == len(node.args) and all(map(_is, args, node.args))
                    if head is node.head and same_args:
                        value = node
                    done[value] = value
                done[node] = value
                stack[-1][2].append(value)
        return results[0]

    return walk

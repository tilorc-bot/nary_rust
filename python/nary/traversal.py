"""at_node gets each node's head and arguments once they are done, children first.

    >>> from nary import Add, NumberKind, sin
    >>> from nary.traversal import bottom_up
    >>> x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
    >>> def show(head, args):
    ...     print(head, args)
    ...     return head(*args)
    >>> bottom_up(show)(sin(x + y) + z)
    Add [x, y]
    sin [Add(x, y)]
    Add [sin(Add(x, y)), z]
    Add(sin(Add(x, y)), z)

With flat, nested applications of a flat head become one call, in written order.

    >>> bottom_up(show, flat=lambda head: head == Add)(x + (y + z) + sin(x + y))
    Add [x, y]
    sin [Add(x, y)]
    Add [x, y, z, sin(Add(x, y))]
    Add(x, y, z, sin(Add(x, y)))
"""

from .functions import is_lambda

__all__ = ["bottom_up"]


def _never(head):
    return False


def bottom_up(at_node, flat=_never):
    done = {}

    def walk(root):
        results = []
        stack = [(None, iter([root]), results, None)]
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

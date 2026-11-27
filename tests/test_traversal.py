from nary import NumberKind, sin
from nary.functions import Lambda
from nary.traversal import bottom_up

x, y = NumberKind("x"), NumberKind("y")


def test_each_subexpression_is_visited_once_leaves_first():
    visited = []

    def swap(head, args):
        visited.append(head(*args))
        return head(*reversed(args))

    walk = bottom_up(swap)
    assert walk((sin(x) + y) * (sin(x) + y)) == (y + sin(x)) * (y + sin(x))
    assert visited == [sin(x), sin(x) + y, (y + sin(x)) * (y + sin(x))]
    assert walk(sin(x) + y) == y + sin(x) and len(visited) == 3


def test_atoms_and_lambdas_are_returned_untouched():
    walk = bottom_up(lambda head, args: 1 / 0)
    square = Lambda(x, x * x)
    assert walk(x) is x and walk(square) is square

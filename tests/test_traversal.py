import ast
import random
import subprocess
import sys
from pathlib import Path

import pytest
from nary import Add, FunctionKind, Lambda, Mul, NumberKind, sin, traversal
from nary._core import Many
from nary.functions import is_lambda
from nary.traversal import bottom_up

x, y, z, u, v = (NumberKind(name) for name in "xyzuv")
a = NumberKind("a")
NumToNum = FunctionKind((NumberKind,), NumberKind)
f, g = NumToNum("f"), NumToNum("g")
h = FunctionKind((NumToNum,), FunctionKind((Many(NumberKind),), NumberKind))("h")
F = FunctionKind((Many(NumToNum),), NumberKind)("F")
C = FunctionKind((Many(NumToNum),), NumToNum)("C")
square = Lambda(a, a * a)
plus_one = Lambda(a, a + 1)


def bottom_up_recursive(at_node):
    done = {}

    def walk(e):
        if e.is_atom or is_lambda(e):
            return e
        if e not in done:
            done[e] = at_node(walk(e.head), [walk(arg) for arg in e.args])
        return done[e]

    return walk


def recorder():
    calls = []

    def at_node(head, args):
        calls.append((head, args))
        return head(*args)

    return calls, at_node


def calls_of(walker, e, **options):
    calls, at_node = recorder()
    assert walker(at_node, **options)(e) is not None
    return calls


def flat_add(head):
    return head == Add


def random_expression(rng, size):
    pool = [x, y, z, NumberKind(1), NumberKind(2)]
    for _ in range(size):
        pick = rng.randrange(6)
        if pick == 0:
            pool.append(Add(*rng.choices(pool, k=rng.randint(0, 4))))
        elif pick == 1:
            pool.append(Mul(*rng.choices(pool, k=2)))
        elif pick == 2:
            pool.append(sin(rng.choice(pool)))
        elif pick == 3:
            pool.append(h(rng.choice([f, g]))(*rng.choices(pool, k=rng.randint(1, 3))))
        elif pick == 4:
            pool.append(plus_one(rng.choice(pool)))
        else:
            pool.append(F(square, plus_one) + rng.choice(pool))
    return Add(*pool[-3:])


def chain(depth, head=Add):
    e = x
    for i in range(depth):
        e = head(e, y) if i % 2 else head(z, e)
    return e


def bracketings(args, head=Add):
    if len(args) == 1:
        yield args[0]
        return
    for i in range(1, len(args)):
        for left in bracketings(args[:i], head):
            for right in bracketings(args[i:], head):
                yield head(left, right)


def test_children_before_parents_in_written_order():
    assert calls_of(bottom_up, sin(x + y) * Add(z, sin(x))) == [
        (Add, [x, y]),
        (sin, [Add(x, y)]),
        (sin, [x]),
        (Add, [z, sin(x)]),
        (Mul, [sin(Add(x, y)), Add(z, sin(x))]),
    ]


def test_at_node_gets_the_processed_head_and_args():
    swap = bottom_up(lambda head, args: head(*reversed(args)))
    assert swap(Add(Mul(x, y), sin(Add(z, u)))) == Add(sin(Add(u, z)), Mul(y, x))


def test_without_flat_the_calls_are_those_of_the_recursive_walk():
    rng = random.Random(20261128)
    expressions = [
        x,
        Add(),
        sin(x + y) * (sin(x + y) + z),
        h(f)(x, h(f)(y, square(z))),
        F(square, plus_one) + Add(Add(x, y), Add(x, y)),
        *(random_expression(rng, 40) for _ in range(30)),
    ]
    for e in expressions:
        assert calls_of(bottom_up, e) == calls_of(bottom_up_recursive, e)


def test_flat_makes_one_call_with_every_argument_in_written_order():
    xs = [NumberKind(f"x{i}") for i in range(6)]
    shapes = [
        *bracketings(xs),
        Add(xs[0], Add(xs[1], xs[2], xs[3]), xs[4], xs[5]),
        Add(Add(Add(xs[0]), xs[1], Add(xs[2], Add(xs[3], xs[4]))), xs[5]),
    ]
    assert len(shapes) == 44
    for e in shapes:
        assert calls_of(bottom_up, e, flat=flat_add) == [(Add, xs)]


def test_left_right_and_mixed_chains_flatten_to_one_call():
    for e in [chain(50), Add(x, Add(y, Add(z, Add(u, v)))), Add(Add(Add(Add(x, y), z), u), v)]:
        calls = calls_of(bottom_up, e, flat=flat_add)
        assert len(calls) == 1
        assert calls[0][1] == list(Add(*calls[0][1]).args)
    assert calls_of(bottom_up, chain(4), flat=flat_add) == [(Add, [z, z, x, y, y])]


def test_only_the_head_that_asked_is_flattened():
    e = Add(Mul(Add(x, y), Mul(z, u)), Add(u, v))
    assert calls_of(bottom_up, e, flat=flat_add) == [
        (Add, [x, y]),
        (Mul, [z, u]),
        (Mul, [Add(x, y), Mul(z, u)]),
        (Add, [Mul(Add(x, y), Mul(z, u)), u, v]),
    ]
    assert calls_of(bottom_up, e, flat=lambda head: head == Mul) == [
        (Add, [x, y]),
        (Mul, [Add(x, y), z, u]),
        (Add, [u, v]),
        (Add, [Mul(Add(x, y), z, u), Add(u, v)]),
    ]


def test_a_different_head_between_two_layers_stops_the_run():
    assert calls_of(bottom_up, Add(x, sin(Add(y, Add(z, u)))), flat=flat_add) == [
        (Add, [y, z, u]),
        (sin, [Add(y, z, u)]),
        (Add, [x, sin(Add(y, z, u))]),
    ]


def test_flat_is_asked_with_the_unprocessed_head_of_each_node_once():
    asked = []

    def flat(head):
        asked.append(head)
        return head == Add

    calls_of(bottom_up, Add(Add(x, sin(y)), Mul(z, Add(u, v))), flat=flat)
    assert asked == [Add, sin, Mul, Add]


def test_same_head_compares_the_unprocessed_heads():
    def at_node(head, args):
        calls.append((head, args))
        return h(g) if head == h else head(*args)

    calls = []
    walk = bottom_up(at_node, flat=lambda head: head == h(f))
    assert walk(h(f)(x, h(f)(y, z), h(g)(u))) == h(g)(x, y, z, h(g)(u))
    assert calls == [
        (h, [f]),
        (h, [g]),
        (h(g), [u]),
        (h(g), [x, y, z, h(g)(u)]),
    ]


def test_an_argument_that_becomes_a_same_head_application_is_not_expanded():
    def at_node(head, args):
        calls.append((head, args))
        return Add(*args, 1) if head == sin else head(*args)

    calls = []
    assert bottom_up(at_node, flat=flat_add)(Add(x, sin(y))) == Add(x, Add(y, 1))
    assert calls[-1] == (Add, [x, Add(y, 1)])


def test_a_flattened_run_memoises_only_its_top_node():
    calls, at_node = recorder()
    walk = bottom_up(at_node, flat=flat_add)
    walk(Add(Add(x, sin(y)), z))
    assert calls == [(sin, [y]), (Add, [x, sin(y), z])]
    walk(Add(Add(x, sin(y)), z))
    walk(Add(x, sin(y)))
    assert calls[2:] == [(Add, [x, sin(y)])]


def test_a_node_shared_by_a_run_and_another_place():
    inner = Add(x, sin(y))
    assert calls_of(bottom_up, Mul(inner, Add(inner, z)), flat=flat_add) == [
        (sin, [y]),
        (Add, [x, sin(y)]),
        (Add, [x, sin(y), z]),
        (Mul, [inner, Add(x, sin(y), z)]),
    ]
    assert calls_of(bottom_up, Mul(Add(inner, z), inner), flat=flat_add) == [
        (sin, [y]),
        (Add, [x, sin(y), z]),
        (Add, [x, sin(y)]),
        (Mul, [Add(x, sin(y), z), inner]),
    ]


def test_shared_subexpressions_are_processed_once():
    shared = sin(x + y)
    e = Mul(shared, Add(shared, Mul(shared, x + y)))
    for flat in [None, flat_add]:
        calls = calls_of(bottom_up, e, **({"flat": flat} if flat else {}))
        assert [call for call in calls if call[0] == sin] == [(sin, [Add(x, y)])]
        assert calls.count((Add, [x, y])) == 1


def test_atoms_and_lambdas_come_back_by_identity():
    one = NumberKind(1)
    walk = bottom_up(lambda head, args: head(*args), flat=lambda head: head == C)
    assert walk(x) is x and walk(one) is one and walk(square) is square
    calls, at_node = recorder()
    bottom_up(at_node, flat=lambda head: head == C)(C(square, C(C(plus_one), f), square))
    assert [type(arg) for arg in calls[0][1]] == [type(square)] * 4
    assert [id(arg) for arg in calls[0][1]] == [id(square), id(plus_one), id(f), id(square)]
    assert calls_of(bottom_up, plus_one(x) + x, flat=flat_add) == [
        (plus_one, [x]),
        (Add, [plus_one(x), x]),
    ]


def test_empty_argument_lists():
    assert calls_of(bottom_up, Add()) == [(Add, [])]
    assert calls_of(bottom_up, Add(Add(), x, Add(Add())), flat=flat_add) == [(Add, [x])]
    assert calls_of(bottom_up, Add(Add()), flat=flat_add) == [(Add, [])]


def test_walk_called_from_inside_at_node():
    def at_node(head, args):
        calls.append((head, args))
        if head == Mul:
            assert walk(sin(x)) == sin(x)
            assert walk(sin(z)) == sin(z)
        return head(*args)

    calls = []
    walk = bottom_up(at_node, flat=flat_add)
    assert walk(Add(Mul(sin(x), y), Add(sin(z), u))) == Add(Mul(sin(x), y), sin(z), u)
    assert calls == [
        (sin, [x]),
        (Mul, [sin(x), y]),
        (sin, [z]),
        (Add, [Mul(sin(x), y), sin(z), u]),
    ]


def test_again_walks_what_at_node_returns_until_it_returns_the_same_node():
    def at_node(head, args):
        calls.append((head, args))
        return args[0] if head == Mul and args[1] == NumberKind(1) else head(*args)

    calls = []
    walk = bottom_up(at_node, again=True)
    assert walk(Mul(Mul(sin(x), 1), 1)) == sin(x)
    one = NumberKind(1)
    assert calls == [(sin, [x]), (Mul, [sin(x), one]), (Mul, [sin(x), one])]


def test_again_walks_new_arguments_of_what_at_node_returns_and_takes_the_rest_from_memory():
    def at_node(head, args):
        calls.append((head, args))
        return Add(args[0], sin(y)) if head == Mul else head(*args)

    calls = []
    assert bottom_up(at_node, again=True)(Mul(sin(x), z)) == Add(sin(x), sin(y))
    assert calls == [(sin, [x]), (Mul, [sin(x), z]), (sin, [y]), (Add, [sin(x), sin(y)])]


def test_again_does_not_call_at_node_twice_where_it_returns_the_same_node():
    e = sin(x + y) * (sin(x + y) + z)
    assert calls_of(bottom_up, e, again=True) == calls_of(bottom_up, e)


def test_orderless_sorts_the_arguments_by_repr():
    assert calls_of(bottom_up, Add(z, Mul(y, x)), orderless=flat_add) == [
        (Mul, [y, x]),
        (Add, [Mul(y, x), z]),
    ]


def test_again_raises_where_at_node_returns_to_what_it_is_walking():
    swap = bottom_up(lambda head, args: head(*reversed(args)), again=True)
    assert swap(sin(x)) == sin(x)
    with pytest.raises(RuntimeError, match="never stop changing"):
        swap(Add(x, y))


def test_deeper_than_the_recursion_limit():
    depth = 3 * sys.getrecursionlimit()
    e = chain(depth)
    with pytest.raises(RecursionError):
        bottom_up_recursive(lambda head, args: head(*args))(e)
    assert bottom_up(lambda head, args: head(*args))(e) == e
    calls = calls_of(bottom_up, e, flat=flat_add)
    assert len(calls) == 1 and len(calls[0][1]) == depth + 1


DEEP = (
    "from nary import Add, NumberKind\n"
    "from nary.traversal import bottom_up\n"
    "def chain():\n"
    "    e = NumberKind('x')\n"
    "    for i in range(100000):\n"
    "        e = Add(e, NumberKind('y')) if i % 2 else Add(NumberKind('z'), e)\n"
    "    return e\n"
    "e = chain()\n"
)


@pytest.mark.parametrize(
    "check",
    [
        "assert len(bottom_up(lambda h, a: h(*a), flat=lambda h: h == Add)(e).args) == 100001",
        "assert bottom_up(lambda h, a: h(*a))(e) == e",
        "assert bottom_up(lambda h, a: h(*a), again=True)(e) == e",
    ],
)
def test_a_chain_100000_deep(check):
    run = subprocess.run([sys.executable, "-c", DEEP + check], check=False, timeout=600)
    assert run.returncode == 0


def test_the_walker_imports_only_is_lambda():
    tree = ast.parse(Path(traversal.__file__).read_text(encoding="utf-8"))
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert [(node.module, [alias.name for alias in node.names]) for node in imports] == [
        ("__future__", ["annotations"]),
        ("collections.abc", ["Callable", "Iterator"]),
        ("_core", ["Expr"]),
        ("functions", ["is_lambda"]),
    ]
    names = {name for name in vars(traversal) if not name.startswith("__")}
    assert names == {
        "bottom_up", "is_lambda", "_never", "_is", "annotations", "Callable", "Iterator", "Expr"
    }
    assert traversal.is_lambda is is_lambda


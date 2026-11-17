"""Time building, comparing and hashing expressions.

    python bench/bench_construct.py                # a table, ns per operation
    python bench/bench_construct.py --json         # {"label": [ns, ...], ...}
    python bench/bench_construct.py --only "x + y" # one operation

The package ``nary`` has to be installed or on PYTHONPATH. ``--module`` names
another module with the same names, so that one copy of this script can time
several versions; ``bench/compare.py`` does that.

Each statement is timed with ``timeit``. The number of loops is chosen so
that one repeat takes about ``--target`` seconds, and the result is the time
of one loop in each of ``--repeats`` repeats.
"""

import argparse
import importlib
import json
import sys
import timeit

# The statements, each with the number of operations in it. A time is
# reported for one operation.
STATEMENTS = [
    ("Add(x, y, z)", "Add(x, y, z)", 1),
    ("x + y", "x + y", 1),
    ("x * y", "x * y", 1),
    ("x < y", "x < y", 1),
    ("sin(x) * y < z", "sin(x) * y < z", 1),
    ("Eq(x + y, z).lhs", "Eq(x + y, z).lhs", 1),
    ("a == b, 90 nodes deep", "a == b", 1),
    ("hash(a), 90 nodes deep", "hash(a)", 1),
    ('NumberKind("x")', 'NumberKind("x")', 1),
    ("sum of 1000 terms with +, per term", "e = x\nfor _ in thousand: e = e + y", 1000),
]


def namespace(nr):
    x, y, z = (nr.NumberKind(name) for name in "xyz")

    def deep():
        e = x
        for _ in range(30):
            e = nr.sin(e) * y + z
        return e

    return {
        "Add": nr.Add, "Eq": nr.Eq, "sin": nr.sin, "NumberKind": nr.NumberKind,
        "x": x, "y": y, "z": z,
        # Two equal trees that share no node, so == walks all of both.
        "a": deep(), "b": deep(),
        "thousand": range(1000),
    }


def measure(nr, repeats, target, only=None):
    names = namespace(nr)
    results = {}
    for label, statement, operations in STATEMENTS:
        if only and label not in only:
            continue
        timer = timeit.Timer(statement, globals=dict(names))
        loops, seconds = timer.autorange()
        loops = max(1, round(loops * target / seconds))
        timer.timeit(loops)  # warm up
        times = timer.repeat(repeats, loops)
        results[label] = [t / loops / operations * 1e9 for t in times]
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--module", default="nary")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--target", type=float, default=0.1, help="seconds per repeat")
    parser.add_argument(
        "--only", action="append", metavar="LABEL",
        help="time only the operation with this label; can be given more than once",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = measure(
        importlib.import_module(args.module), args.repeats, args.target, args.only
    )
    if args.json:
        json.dump(results, sys.stdout)
        return
    width = max(len(label) for label in results)
    print(f"{'ns per operation':<{width}}  {'min':>8}  {'max':>8}")
    for label, times in results.items():
        print(f"{label:<{width}}  {min(times):>8.1f}  {max(times):>8.1f}")


if __name__ == "__main__":
    main()

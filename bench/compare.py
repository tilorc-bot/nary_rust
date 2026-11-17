"""Compare versions of the package with bench_construct.py.

    python bench/compare.py --rounds 10 \\
        base=/work/main base-again=/work/main candidate=/work/python-kinds

Each argument is ``label=path`` or ``label=path:module``. The path is put on
PYTHONPATH, so it has to hold the compiled module and the module that
declares the kinds and functions (``nary_rs`` unless a module is named). One
way to make such a directory from a checkout:

    uvx maturin build -r -i python3.13 -o /tmp/wheels
    uv pip install --target /work/python-kinds /tmp/wheels/nary_rust-*.whl
    cp nary_rs.py /work/python-kinds/

The first argument is the base and the others are compared with it. Naming
the base twice gives the noise: the ratio that two runs of the same code
show. A difference no larger than that is not a difference.

Every measurement is made in a new process that times one operation, so that
one operation cannot leave the allocator in a state that changes the time of
the next. In each round each operation is timed once for every version, one
version straight after another, and the order of the versions rotates from
round to round. The time of an operation in a round is the smallest of the
repeats in its process. A ratio is taken within a round, and the table gives
the median of the rounds and their range.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "bench_construct.py"
sys.path.insert(0, str(SCRIPT.parent))

from bench_construct import STATEMENTS  # noqa: E402


def run(path, module, repeats, target, operation):
    """The time of one operation in a new process, in ns."""
    env = dict(os.environ, PYTHONPATH=path)
    command = [
        sys.executable, str(SCRIPT), "--json", "--module", module,
        "--repeats", str(repeats), "--target", str(target), "--only", operation,
    ]
    output = subprocess.run(command, env=env, check=True, capture_output=True, text=True)
    return min(json.loads(output.stdout)[operation])


def spread(values):
    return f"{statistics.median(values):.3f} ({min(values):.3f}-{max(values):.3f})"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("versions", nargs="+", metavar="label=path[:module]")
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--target", type=float, default=0.1, help="seconds per repeat")
    parser.add_argument(
        "--only", action="append", metavar="LABEL",
        help="time only the operation with this label; can be given more than once",
    )
    parser.add_argument("--output", help="write every measurement to this JSON file")
    args = parser.parse_args()

    versions = []
    for text in args.versions:
        label, _, rest = text.partition("=")
        path, _, module = rest.partition(":")
        versions.append((label, path, module or "nary_rs"))
    labels = [label for label, _, _ in versions]

    operations = [label for label, _, _ in STATEMENTS if not args.only or label in args.only]

    # times[label][operation] is a list with one time for each round.
    times = {label: {operation: [] for operation in operations} for label in labels}
    for round_number in range(args.rounds):
        shift = round_number % len(versions)
        for operation in operations:
            for label, path, module in versions[shift:] + versions[:shift]:
                ns = run(path, module, args.repeats, args.target, operation)
                times[label][operation].append(ns)
        print(f"round {round_number + 1} of {args.rounds} done", file=sys.stderr)

    if args.output:
        Path(args.output).write_text(json.dumps(times, indent=1))

    base, others = labels[0], labels[1:]
    header = ["operation", f"{base}, ns"]
    for label in others:
        header += [f"{label}, ns", f"{label} / {base}"]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for operation, base_times in times[base].items():
        row = [operation, f"{statistics.median(base_times):.1f}"]
        for label in others:
            other_times = times[label][operation]
            ratios = [other / base for other, base in zip(other_times, base_times)]
            row += [f"{statistics.median(other_times):.1f}", spread(ratios)]
        print("| " + " | ".join(row) + " |")


if __name__ == "__main__":
    main()

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
    parser = argparse.ArgumentParser(description="Compare versions of the package with bench_construct.py.")
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
        versions.append((label, path, module or "nary"))
    labels = [label for label, _, _ in versions]

    operations = [label for label, _, _ in STATEMENTS if not args.only or label in args.only]

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

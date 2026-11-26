from pathlib import Path

from nary import Add, Mul, Pow, cos, exp, log, sin, tan
from nary.arithmetic_rules import rules
from nary.lean import to_lean_facts, to_lean_rule
from nary.logic import And, Not, Or

PATH = Path(__file__).resolve().parent / "Nary" / "ArithmeticRules" / "Statements.lean"

PENDING = {"pow_whole_split", "pow_positive_split", "pow_composes"}

HEADER = """\
import Nary.Calculus
import Nary.Facts
import Nary.Logic
"""


def render():
    declarations = [to_lean_rule(r) for r in rules]
    heads = (Add, Mul, Pow, exp, log, sin, cos, tan, And, Or, Not)
    declarations += [d for f in heads for d in to_lean_facts(f)]
    names = [d.split("abbrev ", 1)[1].split()[0] for d in declarations]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"two statements have the same name: {', '.join(duplicates)}")
    pending = [f"{name}_law" for name in sorted(PENDING)]
    proved = "".join(f"\n  {name} : Statement.{name}" for name in names if name not in pending)
    unproved = "".join(f"\n  {name} : Statement.{name}" for name in pending)
    return (
        f"{HEADER}\nnamespace Nary.ArithmeticRules.Statement\n\n"
        + "\n\n".join(declarations)
        + "\n\nend Nary.ArithmeticRules.Statement\n\nnamespace Nary.ArithmeticRules\n\n"
        f"structure Proved : Prop where{proved}\n\n"
        f"structure Pending : Prop where{unproved}\n\nend Nary.ArithmeticRules\n"
    )


if __name__ == "__main__":
    PATH.parent.mkdir(exist_ok=True)
    PATH.write_text(render(), encoding="utf-8")
    print(f"wrote {PATH}")

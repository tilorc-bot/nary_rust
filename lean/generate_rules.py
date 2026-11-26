from pathlib import Path

from nary import Add, Mul
from nary.arithmetic_rules import rules
from nary.autosimp import RULES
from nary.lean import to_lean_facts, to_lean_rule

NARY = Path(__file__).resolve().parent / "Nary"
TARGETS = {
    "ArithmeticRules": (rules, (Add, Mul)),
    "Autosimp": ([r for group in RULES.values() for r in group if r not in rules], ()),
}

HEADER = """\
import Nary.Calculus
import Nary.Facts
import Nary.Logic
"""


def render(target):
    chosen, facts = TARGETS[target]
    declarations = [to_lean_rule(r) for r in chosen]
    declarations += [d for f in facts for d in to_lean_facts(f)]
    names = [d.split("abbrev ", 1)[1].split()[0] for d in declarations]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"two statements have the same name: {', '.join(duplicates)}")
    fields = "".join(f"\n  {name} : Statement.{name}" for name in names)
    return (
        f"{HEADER}\nnamespace Nary.{target}.Statement\n\n"
        + "\n\n".join(declarations)
        + f"\n\nend Nary.{target}.Statement\n\nnamespace Nary.{target}\n\n"
        f"structure Proved : Prop where{fields}\n\nend Nary.{target}\n"
    )


if __name__ == "__main__":
    for target in TARGETS:
        path = NARY / target / "Statements.lean"
        path.parent.mkdir(exist_ok=True)
        path.write_text(render(target), encoding="utf-8")
        print(f"wrote {path}")

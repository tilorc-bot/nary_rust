from importlib import import_module
from pathlib import Path

from nary import Add, Mul
from nary.lean import to_lean_facts, to_lean_rule
from nary.logic import And, Or

NARY = Path(__file__).resolve().parent / "Nary"

SOURCES = {
    "ArithmeticRules": ("nary.arithmetic_rules", "rules", (Add, Mul)),
    "ElementaryRules": ("nary.elementary_rules", "rules", ()),
    "LogicRules": ("nary.logic_rules", "rules", (And, Or)),
    "Normal": ("nary.normal", "laws", ()),
}

HEADER = """\
import Nary.Calculus
import Nary.Facts
import Nary.Logic
"""


def render_one(name, module, attribute, functions):
    rules = getattr(import_module(module), attribute)
    declarations = [to_lean_rule(r) for r in rules]
    declarations += [d for f in functions for d in to_lean_facts(f)]
    names = [d.split("abbrev ", 1)[1].split()[0] for d in declarations]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"two statements in {module} have the same name: {', '.join(duplicates)}")
    return (
        f"{HEADER}\nnamespace Nary.{name}.Statement\n\n"
        + "\n\n".join(declarations)
        + f"\n\nend Nary.{name}.Statement\n"
    )


def render():
    return {
        NARY / name / "Statements.lean": render_one(name, *source)
        for name, source in SOURCES.items()
    }


if __name__ == "__main__":
    for path, text in render().items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")

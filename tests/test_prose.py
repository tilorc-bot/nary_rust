import ast
import doctest
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUDGET = ROOT / "tests" / "prose_budget.txt"
EXEMPT = {"AGENTS.md"}


def entry_names(body):
    """
    >>> entry_names(["    a: One.", "    *rest: Others,", "        at length."])
    ['a', 'rest']
    >>> entry_names(["    Not an entry."]) is None
    True
    """
    indent = len(body[0]) - len(body[0].lstrip())
    names = []
    for line in body:
        if len(line) - len(line.lstrip()) == indent:
            entry = re.match(r"\*{0,2}(\w+): \S", line.strip())
            if entry is None:
                return None
            names.append(entry.group(1))
    return names


def without_sections(doc, parameters):
    lines = doc.splitlines()
    kept = []
    i = 0
    while i < len(lines):
        end = i + 1
        while end < len(lines) and lines[end].startswith(" "):
            end += 1
        body = lines[i + 1:end]
        returns = lines[i] == "Returns:" and body
        args = lines[i] == "Args:" and body and entry_names(body) == parameters
        if returns or args:
            i = end
        else:
            kept.append(lines[i])
            i += 1
    return "\n".join(kept)


def docstring_prose(doc, parameters=None):
    """
    >>> docstring_prose("One caption.\\n\\n    >>> 1 + 1\\n    2\\n")
    0
    >>> docstring_prose("First line.\\nSecond line.\\n\\n    >>> 1 + 1\\n    2\\n")
    2
    >>> docstring_prose("One sentence and no example.")
    0
    >>> docstring_prose("First line.\\nSecond line.")
    2
    >>> docstring_prose("    >>> 1 + 1\\n    2\\n\\nAfter the last example.")
    1

    Args and Returns are free where parameters lists the names that Args has to explain.

    >>> sections = "Args:\\n    a: One.\\n    b: Other,\\n        at length.\\n\\nReturns:\\n    Both.\\n"
    >>> example = "\\n>>> 1 + 1\\n2\\n"
    >>> docstring_prose("Add." + "\\n\\n" + sections + example, ["a", "b"])
    0
    >>> docstring_prose("Add." + "\\n\\n" + sections + example)
    7
    >>> docstring_prose("Add." + "\\n\\n" + sections + example, ["b", "a"])
    5
    >>> docstring_prose("Add." + "\\n\\n" + sections + example, ["a", "b", "c"])
    5
    >>> docstring_prose("Add." + "\\n\\n" + sections + "\\nMore to say." + example, ["a", "b"])
    2
    >>> docstring_prose("Add.\\n\\nRaises:\\n    Error: Sometimes.\\n" + example, [])
    3
    """
    if parameters is not None:
        doc = without_sections(doc, parameters)
    pieces = doctest.DocTestParser().parse(doc)
    count = 0
    for i, piece in enumerate(pieces):
        if isinstance(piece, doctest.Example):
            continue
        lines = sum(1 for line in piece.splitlines() if line.strip())
        caption = lines == 1 and (i == 0 or i + 1 < len(pieces))
        if not caption:
            count += lines
    return count


def parameters_to_explain(node):
    """
    >>> parameters_to_explain(ast.parse("def f(self, a, /, b, *rest, c=1, **more): pass").body[0])
    ['a', 'b', 'rest', 'c', 'more']
    >>> parameters_to_explain(ast.parse("def _f(a): pass").body[0]) is None
    True
    >>> parameters_to_explain(ast.parse("class C: pass").body[0]) is None
    True
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name.startswith("_"):
        return None
    spec = node.args
    found = [*spec.posonlyargs, *spec.args, spec.vararg, *spec.kwonlyargs, spec.kwarg]
    names = [arg.arg for arg in found if arg is not None]
    return names[1:] if names[:1] in (["self"], ["cls"]) else names


def python_prose(source):
    """
    >>> python_prose("x = 1  # why\\n# why\\nfrom m import *  # noqa: F403\\n")
    2
    >>> python_prose('def f():\\n    "What f does,\\\\nat length."\\n')
    2
    >>> python_prose('def f(a):\\n    "Add.\\\\n\\\\nArgs:\\\\n    a: One.\\\\n\\\\nReturns:\\\\n    Two."\\n')
    0
    >>> python_prose('def _f(a):\\n    "Add.\\\\n\\\\nArgs:\\\\n    a: One.\\\\n\\\\nReturns:\\\\n    Two."\\n')
    5
    """
    count = 0
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and not token.string.startswith(("# noqa", "#!")):
            count += 1
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc:
                count += docstring_prose(doc, parameters_to_explain(node))
    return count


def line_comment_prose(source, marker):
    """
    >>> line_comment_prose("// a\\nlet x = 1; // b\\n    /// c\\n", "//")
    2
    """
    return sum(1 for line in source.splitlines() if line.strip().startswith(marker))


def lean_prose(source):
    """
    >>> lean_prose("-- a\\n/-- b\\nc -/\\ndef x := 1\\n/- d -/\\n")
    4
    """
    count = 0
    inside = False
    for line in source.splitlines():
        text = line.strip()
        if not inside and text.startswith("/-"):
            inside = True
        if inside:
            count += 1
            if text.endswith("-/"):
                inside = False
        elif text.startswith("--"):
            count += 1
    return count


def markdown_prose(source):
    """
    >>> markdown_prose("# Title\\n\\nText.\\n")
    2
    """
    return sum(1 for line in source.splitlines() if line.strip())


COUNTERS = {
    ".py": python_prose,
    ".rs": lambda source: line_comment_prose(source, "//"),
    ".lean": lean_prose,
    ".md": markdown_prose,
    ".toml": lambda source: line_comment_prose(source, "#"),
    ".yml": lambda source: line_comment_prose(source, "#"),
    ".yaml": lambda source: line_comment_prose(source, "#"),
}


def measure():
    listed = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    counts = {}
    for name in sorted(listed):
        path = ROOT / name
        counter = COUNTERS.get(path.suffix)
        if counter is None or name in EXEMPT or not path.is_file():
            continue
        count = counter(path.read_text(encoding="utf-8"))
        if count:
            counts[name] = count
    return counts


def read_budget():
    budget = {}
    for line in BUDGET.read_text(encoding="utf-8").splitlines():
        count, name = line.split(maxsplit=1)
        budget[name] = int(count)
    return budget


def write_budget(counts):
    BUDGET.write_text(
        "".join(f"{count} {name}\n" for name, count in counts.items()), encoding="utf-8"
    )


def test_the_counters():
    assert doctest.testmod(sys.modules[__name__]).failed == 0


def test_no_file_has_more_prose_than_its_budget():
    budget = read_budget()
    over = {
        name: (count, budget.get(name, 0))
        for name, count in measure().items()
        if count > budget.get(name, 0)
    }
    assert not over, "prose lines (found, budget), see AGENTS.md: " + repr(over)


def test_the_budget_is_lowered_when_prose_is_removed():
    counts = measure()
    under = {
        name: (counts.get(name, 0), allowed)
        for name, allowed in read_budget().items()
        if counts.get(name, 0) < allowed
    }
    assert not under, "run python tests/test_prose.py, (found, budget): " + repr(under)


if __name__ == "__main__":
    write_budget(measure())

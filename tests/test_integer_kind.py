"""The kind of an integer is declared in Python, not known to Rust."""

import importlib.machinery
import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

import nary as nr
import pytest
from nary import BoolKind, Integer, NumberKind, set_integer_kind


def test_the_package_declares_integers_to_be_numbers():
    assert Integer(1).kind is NumberKind
    assert (NumberKind("x") + 1).args[1].kind is NumberKind


def test_the_kind_of_integers_is_declared_once():
    with pytest.raises(ValueError, match="^integers are already declared to be NumberKind$"):
        set_integer_kind(BoolKind)
    with pytest.raises(ValueError, match="^integers are already declared to be NumberKind$"):
        set_integer_kind(NumberKind)
    assert Integer(1).kind is NumberKind


def test_an_int_is_converted_only_for_the_kind_of_integers():
    f = nr.function("f", BoolKind, returns=BoolKind)
    with pytest.raises(TypeError, match=r"^f expects BoolKind, got int: 1$"):
        f(1)


def compiled_module():
    """The path of nary._core, found without importing nary."""
    spec = importlib.util.find_spec("nary")
    for directory in spec.submodule_search_locations:
        for suffix in importlib.machinery.EXTENSION_SUFFIXES:
            for path in Path(directory).glob("_core*" + suffix):
                return path
    return None


# Run in a new process, with the compiled module loaded on its own. The
# package is never imported there, so nothing has declared a kind.
ALONE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("_core", sys.argv[1])
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def error(call, *args):
    try:
        call(*args)
    except Exception as e:
        return f"{type(e).__name__}: {e}"

Whole = core.kind("Whole")
Other = core.kind("Other")
double = core.function("double", Whole, returns=Whole)
other = core.function("other", Other, returns=Other)
print(error(core.Integer, 1))
print(error(double, 1))
print(error(double, "a"))
core.set_integer_kind(Whole)
print(core.Integer(1).kind is Whole, repr(double(2)), double(2).args[0].kind is Whole)
print(error(other, 1))
print(error(core.set_integer_kind, Other))
"""

EXPECTED = """
TypeError: no kind has been declared for integers: call set_integer_kind(kind)
TypeError: double was given the int 1, but no kind has been declared for integers: call set_integer_kind(kind)
TypeError: double expects Whole, got str: 'a'
True double(2) True
TypeError: other expects Other, got int: 1
ValueError: integers are already declared to be Whole
"""


def test_integers_before_and_after_their_kind_is_declared():
    path = compiled_module()
    if path is None:
        pytest.skip("the compiled module was not found as a file")
    result = subprocess.run(
        [sys.executable, "-c", ALONE, str(path)], capture_output=True, text=True
    )
    assert result.stderr == ""
    assert result.stdout.strip() == textwrap.dedent(EXPECTED).strip()

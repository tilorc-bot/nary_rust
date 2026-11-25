"""The catalogue of desired simplifications (catalogue/): SymPy makes each
one, the numerical check finds no counterexample, and today's engine
reaches the entries in PASSING; the others are expected failures."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from catalogue import numeric  # noqa: E402
from catalogue.engine import reaches, result_of  # noqa: E402
from catalogue.entries import ENTRIES  # noqa: E402

sympy = pytest.importorskip("sympy")
from catalogue.sympy_check import SYMPY_VERSION, run, to_sympy  # noqa: E402

# The entries today's engine and rules reach. One that stops reaching its
# expected output fails; one not listed that starts reaching it passes as
# an XPASS and should be added here.
PASSING = {
    "add_zero", "mul_one", "mul_zero", "sin_mul_zero", "sub_self", "add_self",
    "sub_self_inside", "div_self", "log_mul_zero", "pow_one", "pow_zero", "exp_log",
}

IDS = [e.name for e in ENTRIES]


def test_names_are_unique():
    assert len(set(IDS)) == len(IDS)


def test_sympy_version():
    assert sympy.__version__ == SYMPY_VERSION


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_shape(entry):
    assert entry.input != entry.expected
    try:
        entry.as_rule()
    except ValueError as error:
        if "Lambda" not in str(error):
            raise
        pytest.xfail("nary.rules refuses a rule containing a Lambda for now")


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_sympy_makes_it(entry):
    """SymPy, with the recorded call and assumptions, gives expected; the
    call is needed (automatic evaluation alone does not do it), and expected
    is left alone by it."""
    given = to_sympy(entry.input, entry.assume)
    expected = to_sympy(entry.expected, entry.assume)
    assert run(entry.sympy, given) == expected
    if entry.sympy != "auto":
        assert given != expected, "automatic evaluation already does it: record 'auto'"
    assert run(entry.sympy, expected) == expected


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_numerically_correct(entry):
    result = numeric.check(entry.input, entry.expected, entry.when)
    assert not result.counterexamples, result.counterexamples[:3]
    has_numbers = any(k.name == "NumberKind" for _, k in numeric.symbols_of(entry.input))
    assert result.held >= (10 if has_numbers else result.tried)


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_engine(entry):
    if entry.name in PASSING:
        assert reaches(entry), result_of(entry)
    elif not reaches(entry):
        pytest.xfail(f"needs {', '.join(entry.tags)}: got {result_of(entry)!r}")

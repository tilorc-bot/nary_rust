"""The catalogue (catalogue/), one list of entries with a status.

Accepted entries: SymPy makes each one, the numerical check finds no
counterexample, and today's engine reaches the entries in PASSING (the
others are expected failures). Rejected entries: SymPy makes each one and
the numerical check finds wrong values; the test fails if one stops being
wrong. Undecided entries: SymPy does what the entry says, and the numerical
check finds what the entry says it finds. Only accepted entries go through
the engine and into Lean. Entries generated from SymPy's test files
(catalogue/from_tests, also tested in tests/test_from_tests.py) record the
SymPy call for every status, so SymPy is checked the same way for all of
them."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from catalogue import numeric  # noqa: E402
from catalogue.engine import reaches, result_of  # noqa: E402
from catalogue.entries import ENTRIES, with_status  # noqa: E402
from catalogue.entry import KINDS, STATUSES  # noqa: E402

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
ACCEPTED = with_status("accepted")
ACCEPTED_IDS = [e.name for e in ACCEPTED]
OTHERS = with_status("rejected", "undecided")
OTHER_IDS = [e.name for e in OTHERS]
# Entries whose SymPy call is recorded: the accepted ones and the generated
# rejected and undecided ones (the hand-written ones record sympy_source).
SYMPY_CALL = ACCEPTED + [e for e in OTHERS if e.generated]
HAND_OTHERS = [e for e in OTHERS if not e.generated]
NARY_FORM = [e for e in ENTRIES if e.has_nary_form]


def test_names_are_unique():
    assert len(set(IDS)) == len(IDS)


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_status_fields(entry):
    """Each status has the fields it needs and only those."""
    assert entry.status in STATUSES
    if entry.generated:
        # Generated from a SymPy test file (catalogue.from_tests): the SymPy
        # call is recorded for every status, the sources say where it came
        # from, and an undecided entry names its class.
        from catalogue.from_tests.rules import UNDECIDED_CLASSES
        assert entry.has_nary_form and entry.sympy is not None and entry.sources
        assert entry.sympy_source is entry.no_value is None and not entry.needs
        assert not (entry.options or entry.question or entry.semantics)
        if entry.status == "accepted":
            assert entry.kind is entry.numeric is entry.cause is None
        else:
            assert entry.kind in KINDS
            assert (entry.kind == "wrong-value") == (entry.status == "rejected")
            assert (entry.cause is not None) == (entry.status == "undecided")
            if entry.cause is not None:
                assert UNDECIDED_CLASSES[entry.cause]["kind"] == entry.kind
        return
    if entry.status == "accepted":
        assert entry.has_nary_form and entry.sympy is not None
        assert entry.kind is entry.sympy_source is entry.numeric is entry.no_value is None
        assert not (entry.options or entry.question or entry.semantics)
    else:
        assert entry.sympy is None and not entry.assume and not entry.needs
        assert entry.kind in KINDS and entry.sympy_source and entry.sympy_gives
        assert entry.semantics and entry.options and entry.question
        assert (entry.kind == "wrong-value") == (entry.status == "rejected")
        if entry.status == "rejected":
            assert entry.has_nary_form and entry.numeric == "value"


def test_sympy_version():
    assert sympy.__version__ == SYMPY_VERSION


@pytest.mark.parametrize("entry", NARY_FORM, ids=[e.name for e in NARY_FORM])
def test_shape(entry):
    assert entry.input != entry.expected
    try:
        entry.as_rule()
    except ValueError as error:
        if "Lambda" not in str(error):
            raise
        pytest.xfail("nary.rules refuses a rule containing a Lambda for now")


@pytest.mark.parametrize("entry", SYMPY_CALL, ids=[e.name for e in SYMPY_CALL])
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


@pytest.mark.parametrize("entry", ACCEPTED, ids=ACCEPTED_IDS)
def test_numerically_correct(entry):
    result = numeric.check(entry.input, entry.expected, entry.when)
    assert not result.counterexamples, result.counterexamples[:3]
    assert not result.unsure, result.unsure[:3]
    has_numbers = any(k.name == "NumberKind" for _, k in numeric.symbols_of(entry.input))
    assert result.held >= (10 if has_numbers else result.tried)


@pytest.mark.parametrize("entry", ACCEPTED, ids=ACCEPTED_IDS)
def test_engine(entry):
    if entry.name in PASSING:
        assert reaches(entry), result_of(entry)
    elif not reaches(entry):
        pytest.xfail(f"needs {', '.join(entry.tags)}: got {result_of(entry)!r}")


# ---- rejected and undecided entries ----------------------------------------


def _sympy_namespace():
    namespace = vars(sympy).copy()
    namespace.update(
        {name: sympy.Symbol(name) for name in ("x", "y", "a", "b", "p", "q")},
        n=sympy.Symbol("n", integer=True), r=sympy.Symbol("r", real=True))
    return namespace


@pytest.mark.parametrize("entry", HAND_OTHERS, ids=[e.name for e in HAND_OTHERS])
def test_sympy_gives(entry):
    """What SymPy does is what the entry says it does; where there is an
    nary form, SymPy's result is ``expected``."""
    try:
        result = eval(entry.sympy_source, _sympy_namespace())
    except Exception as error:  # noqa: BLE001 - the exception is the result
        result, gives = None, type(error).__name__
    else:
        gives = repr(result)
    assert gives == entry.sympy_gives
    if entry.has_nary_form:
        assert result == to_sympy(entry.expected)


@pytest.mark.parametrize("entry", OTHERS, ids=OTHER_IDS)
def test_numeric_finds(entry):
    """The numerical check finds what the entry says it finds: wrong values
    exactly for the rejected ones, so a rejected entry that stops being
    wrong fails here."""
    if entry.no_value is not None:
        assert numeric.evaluate(entry.no_value, {}) is None
    if not entry.has_nary_form:
        assert entry.numeric is None
        return
    found = numeric.check(entry.input, entry.expected, entry.when)
    outcome = ("value" if found.value_counterexamples
               else "definedness" if found.counterexamples else "none")
    assert outcome == entry.numeric, found.counterexamples[:3]
    assert (outcome == "value") == (entry.status == "rejected")
    # Points no precision decides: exactly for the entries of kind precision.
    assert bool(found.unsure) == (entry.kind == "precision"), found.unsure[:3]


# ---- Lean ------------------------------------------------------------------


def test_lean_statements_are_current():
    from catalogue import lean
    assert lean.PATH.read_text(encoding="utf-8") == lean.render(), (
        "lean/Nary/Catalogue/Statements.lean is out of date: run "
        ".venv/bin/python -m catalogue.lean")


def test_lean_proofs_name_entries():
    from catalogue.lean import proved
    names = proved()
    assert len(set(names)) == len(names)
    assert set(names) <= set(ACCEPTED_IDS)

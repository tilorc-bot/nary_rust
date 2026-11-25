"""The hand-written tables of the scoreboard. Everything that is a judgement
rather than mechanics is here, so reviewing this file reviews the scoreboard.
"""

# The SymPy release the tests are taken from, and the commit of its tag
# (sympy-1.14.0), for links.
SYMPY_VERSION = "1.14.0"
SYMPY_COMMIT = "16fa855354eb7bcabd3fe10993841e03b1382692"

# The test files: name of the report -> (path in the SymPy repository, git
# blob sha of the file at SYMPY_COMMIT).
FILES = {
    "power": ("sympy/core/tests/test_power.py", "80ae48c525c20da6153deffbc9feadef81acf527"),
}

# ---- the piles -------------------------------------------------------------

PASS = "pass"
GAP = "gap"
DIFFERS = "differs"
MISSING = "not expressible yet"
NOT_APPLICABLE = "not applicable"
NOT_RUN = "not run"

PILES = {
    PASS: "nary's engine agrees with SymPy",
    GAP: "nary can write both sides, and its engine does not agree with SymPy yet",
    DIFFERS: "nary does not agree with SymPy, for a stated reason; not counted against nary",
    MISSING: "a test of a value that needs something nary cannot write",
    NOT_APPLICABLE: "not a test of the value of an expression (a query, printing, an error)",
    NOT_RUN: "the scoreboard could not run it; a limit of the scoreboard, not of nary",
}

# ---- differences -----------------------------------------------------------

# Why a case that fails does not count against nary.
DIFFERENCE_KINDS = {
    "sympy-bug": "SymPy's result is wrong",
    "definition": "nary defines the expressions differently",
    "design": "nary chooses not to do this",
}

# Decided by hand: case id (as in the report) -> (kind, note). A case where
# one side has no value at a point where the other has one is filed as
# "definition" without an entry here (report.score).
DIFFERENCES = {
}

# ---- what nary cannot write ------------------------------------------------

# SymPy names and methods are "not expressible yet" under their own name
# unless listed here, where several names are one missing thing.
LABELS = {
    "oo": "infinities", "zoo": "infinities", "Infinity": "infinities",
    "NegativeInfinity": "infinities", "ComplexInfinity": "infinities",
    "nan": "nan", "NaN": "nan",
    "Float": "floats", "N": "floats", "n": "floats", "evalf": "floats",
    "O": "series", "series": "series", "nseries": "series", "_eval_nseries": "series",
    "removeO": "series", "taylor_term": "series",
}

# ---- what is not a test of a value -----------------------------------------

# Names of the test file (SymPy's or Python's) whose result is not the value
# of an expression.
NOT_VALUES = {
    "len": "a structure query (len)",
    "isinstance": "a type query (isinstance)",
    "int": "a conversion to a Python number",
    "float": "a conversion to a Python number",
    "NS": "printing (NS)",
    "raises": "a check that an error is raised",
    "warns": "a check that a warning is given",
    "all_close": "a numerical comparison (all_close)",
    "integer_nthroot": "an integer function (integer_nthroot)",
}

# Attributes of an expression that ask about its structure. Every is_*
# attribute is a query too (name()).
QUERIES = ("args", "func", "base", "exp", "atoms", "free_symbols", "as_numer_denom",
           "as_base_exp", "as_coeff_Mul", "as_coeff_Add", "as_content_primitive",
           "as_real_imag", "as_powers_dict", "as_coefficients_dict")


def name(n):
    """``(pile, label)`` for the SymPy name or attribute ``n`` that nary
    does not have."""
    if n in NOT_VALUES:
        return NOT_APPLICABLE, NOT_VALUES[n]
    if n.startswith("is_"):
        kind = "a type query" if n[3:4].isupper() else "an assumption query"
        return NOT_APPLICABLE, f"{kind} ({n})"
    if n in QUERIES:
        return NOT_APPLICABLE, f"a structure query ({n})"
    return MISSING, LABELS.get(n, n)

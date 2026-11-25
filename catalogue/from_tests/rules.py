"""The reviewed tables of the generator in ``catalogue.from_tests.generate``.

Every decision the generator makes that is not plain mechanics lives here,
so that reviewing this file reviews the generator's judgement. The
generated files (``power.py``, ``power.md``) hold none: they are what the
generator writes from the pinned SymPy test file and these tables.

The order in which an assertion is classified (the first rule that
applies decides its category):

1. ``CONTEXTS``: an assert inside a loop, an ``if``, a ``with`` or a
   helper function is ``not-translatable``: the generator does not run
   loops or follow branches.
2. ``QUERY_ATTRIBUTES``, ``QUERY_CALLS`` and ``is_*`` attributes: an assert
   that asks about structure, assumptions, printing or numerical closeness
   anywhere in its expression is ``not-a-simplification``.
3. ``!=``, ``is not`` or ``not (... == ...)``: ``non-rewrite``, a check that
   SymPy does *not* rewrite one side into the other.
4. Anything else that is not a comparison with ``==`` or ``is`` is
   ``not-translatable`` (``and``/``or`` of checks, a helper call, ...).
5. Each operand is translated into nary (``NAMES``, ``FUNCTIONS``,
   ``S_ATTRIBUTES``, ``OUT_OF_VOCABULARY``, ``METHODS``, ``CALL_METHODS``);
   a missing piece makes the assert ``out-of-vocabulary``, naming it, and a
   construct the generator cannot follow makes it ``not-translatable``.
6. Every operand that SymPy changes gives an entry from its written form
   to SymPy's value; if SymPy changes none, the assert is
   ``not-a-simplification`` ("SymPy leaves it as written").
7. The entry's status comes from the checks: the numerical check finds
   wrong values -> ``rejected``; it finds only points where one side has a
   value and the other has none -> ``undecided``, in the class
   ``UNDECIDED_CLASSES`` keyed on the cause; otherwise ``accepted``.
"""

# ---- the pinned input ------------------------------------------------------

# The test files, by the stem used in entry names: (path in the SymPy
# repository, git blob sha of the file at sympy_check.SYMPY_COMMIT). The blob
# sha was read from GitHub at that commit; tests check that the installed
# SymPy's copy has the same sha.
FILES = {
    "power": ("sympy/core/tests/test_power.py", "80ae48c525c20da6153deffbc9feadef81acf527"),
}

# The area (catalogue.entry.AREAS) of the entries generated from each file.
AREAS = {"power": "powers"}

CATEGORIES = {
    "entry": "became one or more catalogue entries",
    "out-of-vocabulary": "needs something nary cannot write; the reason names it",
    "not-a-simplification": "checks something other than the value of an expression "
                            "(an assumption or structure query, printing, a numerical "
                            "comparison), or SymPy leaves the input as written",
    "non-rewrite": "checks that SymPy does NOT rewrite one side into the other "
                   "(!=, is not); a possible future negative entry",
    "not-translatable": "needs running code the generator does not follow (a loop, a "
                        "branch, a helper, a substitution); the reason says what",
}

# ---- 1. contexts ---------------------------------------------------------

CONTEXTS = {
    "For": "inside a for loop",
    "While": "inside a while loop",
    "If": "inside an if (depends on a run-time setting)",
    "With": "inside a with block",
    "Try": "inside a try block",
    "FunctionDef": "inside a helper function defined in the test",
    "ClassDef": "inside a class defined in the test",
}

# ---- 2. queries: the assert is not about a simplification ---------------

# Attributes (besides every is_*) that ask about structure.
QUERY_ATTRIBUTES = {
    "as_numer_denom": "a structure query (as_numer_denom)",
    "as_base_exp": "a structure query (as_base_exp)",
    "args": "a structure query (.args)",
    "func": "a structure query (.func)",
    "exp": "a structure query (.exp)",
    "base": "a structure query (.base)",
    "atoms": "a structure query (.atoms)",
}

QUERY_CALLS = {
    "str": "printing (str)",
    "NS": "printing (NS)",
    "len": "a structure query (len)",
    "int": "a conversion to a Python int",
    "all_close": "a numerical comparison (all_close)",
    "integer_nthroot": "an integer function (integer_nthroot), not an expression",
    "warns": "a warning check",
    "raises": "a raises check",
}


def is_query_attribute(name):
    """The reason an attribute marks a query, or None."""
    if name.startswith("is_"):
        kind = "a type query" if name[3:4].isupper() else "an assumption query"
        return f"{kind} ({name})"
    return QUERY_ATTRIBUTES.get(name)


# ---- 5. translation into nary --------------------------------------------

# Out of vocabulary: what nary cannot write, by the name the test uses.
OUT_OF_VOCABULARY = {
    "oo": "infinities", "zoo": "infinities", "nan": "nan",
    "Float": "floats", "N": "floats",
    "sec": "sec", "csc": "csc", "atan": "atan", "sinh": "sinh", "cosh": "cosh",
    "tanh": "tanh", "erf": "erf", "abs": "Abs", "Abs": "Abs",
    "O": "series (O)", "Poly": "Poly", "FiniteSet": "sets", "Basic": "bare Basic/Expr",
    "Expr": "bare Basic/Expr",
}

# SymPy's S.<name>.
S_ATTRIBUTES = {
    "Half": ("rational", 1, 2), "One": ("int", 1), "Zero": ("int", 0),
    "NegativeOne": ("int", -1), "ImaginaryUnit": ("I",), "Exp1": ("E",), "Pi": ("pi",),
    "Infinity": ("missing", "infinities"), "NegativeInfinity": ("missing", "infinities"),
    "ComplexInfinity": ("missing", "infinities"), "NaN": ("missing", "nan"),
}

# Functions nary has, by the name the test uses. "sqrt" and the like are
# powers: SymPy defines sqrt(x) as Pow(x, 1/2), root(x, n) and cbrt as
# Pow(x, 1/n), the principal root, which is also what nary's Pow means.
# Rationals are written as the catalogue writes them today (the undecided
# entry "rationals"): Rational(1, q) is Pow(q, -1), Rational(p, q) is
# Mul(p, Pow(q, -1)).
FUNCTIONS = ("Rational", "Integer", "Number", "S", "sqrt", "cbrt", "root", "exp", "log",
             "sin", "cos", "tan", "Pow", "power", "Mul", "Add", "Symbol", "symbols")

# Method calls (receiver.name(...)) in an operand that are not a SymPy call
# of the catalogue: out of vocabulary (a label) or not translatable (None,
# with the reason).
METHODS = {
    "series": ("out-of-vocabulary", "series"),
    "_eval_nseries": ("out-of-vocabulary", "series"),
    "removeO": ("out-of-vocabulary", "series"),
    "taylor_term": ("out-of-vocabulary", "series"),
    "n": ("out-of-vocabulary", "floats"),
    "evalf": ("out-of-vocabulary", "floats"),
    "subs": ("not-translatable", "a substitution (subs)"),
    "xreplace": ("not-translatable", "a substitution (xreplace)"),
}

# Method calls and functions that are SymPy calls of the catalogue
# (catalogue.sympy_check.CALLS), allowed as the outermost call of an
# operand: the operand's receiver is the entry's input and the call is how
# SymPy makes it. (method name, argument names) -> call.
CALL_METHODS = {
    ("expand", ()): "expand",
    ("rewrite", ("exp",)): "rewrite_exp",
}
CALL_FUNCTIONS = {
    "expand_multinomial": "expand_multinomial",
}

# The SymPy assumptions a symbol may have are those of the tables ASSUMPTIONS
# and NO_CONDITION in catalogue/entry.py; any other is out of vocabulary.

# ---- 7. undecided classes --------------------------------------------------

# The cause of an undecided entry is found by a fixed rule
# (generate.cause): at each point where one side has a value and the other
# has none, the side without a value and its innermost subexpression that has
# no value although its arguments do. The class is the sorted set of those
# causes. One decision per class covers all its entries.
UNDECIDED_CLASSES = {
    "input: Pow(0, 0)": dict(
        kind="off-domain",
        description="SymPy gives a value where nary's input has none: the input contains "
                    "0**0 at some point (as x**0 at x = 0), which has no value in nary",
        question="Should a generated entry that only fails at 0**0 be accepted with a "
                 "condition, kept undecided, or left out? (as the hand-written undecided "
                 "entries pow_zero_unconditional and zero_pow_zero)"),
    "input: Pow(0, negative)": dict(
        kind="condition",
        description="SymPy gives a value where nary's input has none: the input divides by "
                    "zero at some point (Pow(0, w) with w a negative real)",
        question="Same, for a division by zero in the input that SymPy cancels"),
    "expected: Pow(0, negative)": dict(
        kind="condition",
        description="SymPy's result has no value where the input has one: the result "
                    "divides by zero at a point where the input does not",
        question="Should an entry whose result is defined on less than its input be "
                 "accepted as a generic simplification?"),
}

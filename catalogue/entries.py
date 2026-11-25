"""The catalogue: one list, ``ENTRIES``, of simplifications SymPy makes,
each with a status (``catalogue.entry`` says what the fields mean).

Every entry is checked by ``tests/test_catalogue.py``. An **accepted** entry
(a desired simplification):

1. SymPy (the version in ``catalogue.sympy_check.SYMPY_VERSION``), with the
   recorded call and assumptions, turns ``input`` into ``expected``.
2. ``catalogue.numeric`` finds no point where ``when`` holds and the two
   sides differ under nary's semantics (issue #2).
3. It is run through ``nary.rewriting.rewrite`` with today's rules; the
   entries in ``PASSING`` must reach ``expected``, the others are expected
   failures.
4. It is stated in Lean (``catalogue.lean``).

A **rejected** entry (SymPy's result is wrong) and an **undecided** one
(SymPy and nary do not line up; for Tilo to decide):

1. ``sympy_source``, evaluated with SymPy, gives ``sympy_gives``; where
   there is an nary form, that is SymPy's version of ``expected``.
2. ``catalogue.numeric.check(input, expected)`` finds what ``numeric``
   says: wrong values (``"value"``) for exactly the rejected entries.
3. ``no_value``, when given, has no value.

They are not run through the engine and not stated in Lean.

Expected outputs are written in SymPy's argument order. Rationals are
written as nary has to write them today: 1/2 is ``Pow(2, -1)`` and 3/2 is
``Mul(3, Pow(2, -1))``.
"""

import nary as nr
from nary import E, I, Lambda, Pow, cos, exp, log, pi, re, sin, tan
from nary.calculus import Derivative
from nary.logic import And, Not, Or, false, true

from .entry import STATUSES, entry, rejected, undecided

x, y, z = nr.NumberKind("x"), nr.NumberKind("y"), nr.NumberKind("z")
a, b = nr.NumberKind("a"), nr.NumberKind("b")
t = nr.NumberKind("t")
p, q = nr.BoolKind("p"), nr.BoolKind("q")
n = nr.NumberKind


def half(k=1):
    """``k/2`` as nary writes it."""
    return Pow(n(2), -1) if k == 1 else n(k) * Pow(n(2), -1)


POSITIVE = {"positive": True}
NONZERO = {"zero": False}
REAL = {"real": True}

# Options that recur for the "condition" kind.
_CONDITION_OPTIONS = (
    "A: catalogue only the conditioned form, as an accepted entry whose SymPy call has the "
    "assumption that makes it right (what the catalogue does where SymPy has such an "
    "assumption)",
    "B: also catalogue SymPy's unconditioned result as a 'generic' simplification, true "
    "where both sides have a value; nary would need a second, weaker notion of rewrite",
    "C: leave it out",
)

ENTRIES = [
    # ---- arithmetic: identities, literals, like terms -------------------
    entry("add_zero", x + 0, x, sympy="auto", tags=["rule"], area="arithmetic"),
    entry("mul_one", x * 1, x, sympy="auto", tags=["rule"], area="arithmetic"),
    entry("mul_zero", x * 0, 0, sympy="auto", tags=["rule"], area="arithmetic"),
    entry("sin_mul_zero", sin(x) * 0, 0, sympy="auto", tags=["rule", "definedness"],
          area="arithmetic",
          note="the erased sin(x) has a value because sin is total"),
    entry("sub_self", x - x, 0, sympy="auto", tags=["rule"], area="arithmetic"),
    entry("add_self", x + x, 2 * x, sympy="auto", tags=["rule"], area="arithmetic"),
    entry("sub_self_inside", x + y - x, y, sympy="auto", tags=["rule"], area="arithmetic"),
    entry("add_literals", n(2) + 3, 5, sympy="auto", tags=["literal-arithmetic"],
          area="arithmetic", needs=["#27"]),
    entry("mul_literals", n(2) * x * 3, 6 * x, sympy="auto", tags=["literal-arithmetic"],
          area="arithmetic", needs=["#27"]),
    entry("collect_literal_coefficients", 2 * x + 3 * x, 5 * x, sympy="auto",
          tags=["literal-arithmetic", "normal-form"], area="arithmetic", needs=["#27"]),
    entry("double_negation", -(-x), x, sympy="auto", tags=["literal-arithmetic"],
          area="arithmetic", needs=["#27"]),
    entry("commuted_product_cancels", x * y - y * x, 0, sympy="auto",
          tags=["matching", "normal-form"], area="arithmetic",
          note="Mul(-1, Mul(y, x)) flattens to Mul(-1, y, x); sub_self would need "
               "Mul(-1, a) to match it with a = Mul(y, x)"),
    entry("collect_products", 2 * x * y + x * y, 3 * x * y, sympy="auto",
          tags=["literal-arithmetic", "matching", "normal-form"], area="arithmetic",
          needs=["#27"], note="#27's collect does not do this: a variable matches one "
                              "argument, not the rest of a product"),
    entry("distribute_literal", 2 * (x + y), 2 * x + 2 * y, sympy="auto",
          tags=["expansion"], area="arithmetic",
          note="SymPy distributes a number over a sum automatically"),
    entry("add_rationals", half() + Pow(n(3), -1), n(5) * Pow(n(6), -1), sympy="auto",
          tags=["literal-arithmetic", "rational-literals"], area="arithmetic"),
    entry("literal_over_itself", n(2) / 2, 1, sympy="auto",
          tags=["literal-arithmetic", "rational-literals", "decide-literals"],
          area="arithmetic", note="div_self applies once Ne(2, 0) is decided"),
    entry("div_self", x / x, 1, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "assumptions"], area="arithmetic"),
    entry("div_self_positive", x / x, 1, sympy="auto", assume={"x": POSITIVE},
          tags=["rule", "assumptions"], area="arithmetic",
          note="needs Ne(x, 0) derived from Gt(x, 0)"),
    undecided("div_self_unconditional", "condition", x / x, n(1),
        area="arithmetic", sympy_source="x/x", sympy_gives="1",
        semantics="x/x has no value at x = 0, 1 has; Mul(x, Pow(x, -1)) -> 1 is a rewrite only "
                  "where Ne(x, 0). SymPy does it automatically and cannot be stopped, so SymPy "
                  "cannot even represent x/x. The entry div_self has zero=False.",
        options=_CONDITION_OPTIONS,
        question="Is SymPy's automatic x/x -> 1 wanted in any form beyond div_self (with "
                 "Ne(x, 0))?",
        numeric="definedness"),
    entry("log_mul_zero", log(x) * 0, 0, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "definedness"], area="arithmetic"),
    undecided("log_mul_zero_unconditional", "condition", log(x) * 0, n(0),
        area="arithmetic", sympy_source="0*log(x)", sympy_gives="0",
        semantics="At x = 0 the left side has no value. The entry log_mul_zero has zero=False. "
                  "Behind it: SymPy erases a factor whenever it multiplies by 0 (x*0 -> 0 also "
                  "for a Symbol that might be infinite), nary only an erased part that has a "
                  "value (the 'definedness' tag).",
        options=_CONDITION_OPTIONS,
        question="Same, for 0*f(x) -> 0 where f(x) may have no value.",
        numeric="definedness"),
    entry("expand_square", (x + 1) ** 2, x ** 2 + 2 * x + 1, sympy="expand",
          tags=["expansion", "normal-form", "literal-arithmetic", "decide-literals"],
          area="arithmetic", needs=["#27"]),
    entry("expand_difference_of_squares", (x + y) * (x - y), x ** 2 - y ** 2,
          sympy="expand", tags=["expansion", "normal-form", "literal-arithmetic"],
          area="arithmetic", needs=["#27"]),
    entry("expand_product", x * (y + z), x * y + x * z, sympy="expand",
          tags=["expansion"], area="arithmetic"),
    entry("factor_square", x ** 2 + 2 * x + 1, (x + 1) ** 2, sympy="factor",
          tags=["strategy"], area="arithmetic"),
    entry("together", 1 / x + 1 / y, (x + y) / (x * y), sympy="together",
          tags=["strategy"], area="arithmetic",
          note="both sides have no value exactly when x = 0 or y = 0"),
    undecided("cancel_removable_singularity", "condition", (x ** 2 - 1) / (x - 1), x + 1,
        area="arithmetic", sympy_source="cancel((x**2 - 1)/(x - 1))", sympy_gives="x + 1",
        semantics="At x = 1 the left side has no value. The condition is Ne(x, 1), which no "
                  "SymPy assumption on x expresses, so there is no entry for it.",
        options=(
            "A: allow conditions that are not SymPy assumptions, written by hand in nary and "
            "checked numerically (the catalogue now derives every condition from a SymPy "
            "assumption, so that SymPy and the check see the same claim)",
        ) + _CONDITION_OPTIONS[1:],
        question="Should the catalogue have hand-written conditions such as Ne(x, 1), "
                 "for cancel and the like?",
        numeric="definedness"),
    undecided("one_over_zero", "off-domain",
        area="arithmetic", sympy_source="S(1)/0", sympy_gives="zoo",
        semantics="Pow(0, -1) has no value; nary has no complex infinity. Same for log(0) "
                  "(log_zero) and tan(pi/2) (tan_pole).",
        options=("A: no value, as now; SymPy's zoo never appears in an entry",
                 "B: add zoo (and nan) to nary's vocabulary"),
        question="None expected (issue #2 decided it); listed so that accepted "
                 "entries never expect zoo.",
        no_value=Pow(n(0), -1)),

    # ---- powers --------------------------------------------------------
    entry("pow_one", x ** 1, x, sympy="auto", tags=["rule"], area="powers"),
    entry("pow_zero", x ** 0, 1, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "assumptions"], area="powers"),
    undecided("pow_zero_unconditional", "condition", x ** 0, n(1),
        area="powers", sympy_source="x**0", sympy_gives="1",
        semantics="Pow(0, 0) has no value (issue #2), so x**0 -> 1 needs Ne(x, 0). The entry "
                  "pow_zero has zero=False. SymPy also gives 0**0 = 1 (see zero_pow_zero).",
        options=_CONDITION_OPTIONS,
        question="Same as div_self_unconditional, for x**0 -> 1.",
        numeric="definedness"),
    undecided("zero_pow_zero", "off-domain", Pow(n(0), 0), n(1),
        area="powers", sympy_source="S(0)**0", sympy_gives="1",
        semantics="Pow(0, 0) has no value (issue #2).",
        options=("A: keep nary's choice; never catalogue 0**0 -> 1",
                 "B: give Pow(0, 0) the value 1, as SymPy and Lean's Mathlib do"),
        question="Keep 0**0 without a value?",
        numeric="definedness", no_value=Pow(n(0), 0)),
    entry("mul_self", x * x, x ** 2, sympy="auto", tags=["rule"], area="powers"),
    entry("mul_powers_literal", x ** 2 * x ** 3, x ** 5, sympy="auto",
          tags=["literal-arithmetic", "decide-literals"], area="powers", needs=["#27"],
          note="x**m * x**n -> x**(m+n) is wrong at x = 0 for m = 2, n = -1, so the rule "
               "needs a condition on the literals"),
    entry("pow_pow_literal", (x ** 2) ** 3, x ** 6, sympy="auto",
          tags=["literal-arithmetic", "decide-literals"], area="powers", needs=["#27"],
          note="(x**a)**n -> x**(a*n) holds for an integer n"),
    entry("mul_powers_positive", x ** a * x ** b, x ** (a + b), sympy="powsimp",
          assume={"x": POSITIVE}, tags=["rule", "assumptions"], area="powers"),
    undecided("powsimp_unconditional", "condition", x ** a * x ** b, x ** (a + b),
        area="powers", sympy_source="powsimp(x**a*x**b)", sympy_gives="x**(a + b)",
        semantics="At x = 0, a = 2, b = -1 the left side has no value (0**-1) and the right is "
                  "0. The entry mul_powers_positive has x positive; mul_powers_literal needs the "
                  "exponents decided.",
        options=_CONDITION_OPTIONS,
        question="Same, for x**a * x**b -> x**(a+b).",
        numeric="definedness"),
    entry("pow_pow_positive", (x ** a) ** b, x ** (a * b), sympy="auto",
          assume={"x": POSITIVE, "a": REAL}, tags=["rule", "assumptions"], area="powers"),
    rejected("powdenest_force", (x ** a) ** b, x ** (a * b),
        area="powers", sympy_source="powdenest((x**a)**b, force=True)",
        sympy_gives="x**(a*b)",
        semantics="At x = -1, a = 2, b = 1/2: ((-1)**2)**(1/2) = 1 and (-1)**1 = -1. "
                  "pow_pow_positive is the entry with x positive and a real.",
        options=("A: reject (as now)",),
        question="As expand_log_force."),
    entry("pow_of_product_positive", (x * y) ** a, x ** a * y ** a,
          sympy="expand_power_base", assume={"x": POSITIVE, "y": POSITIVE},
          tags=["rule", "assumptions", "expansion"], area="powers"),
    entry("pow_of_product_literal", (x * y) ** 2, x ** 2 * y ** 2, sympy="auto",
          tags=["expansion", "decide-literals"], area="powers"),
    entry("sqrt_of_square_positive", (x ** 2) ** half(), x, sympy="auto",
          assume={"x": POSITIVE}, tags=["rule", "assumptions", "rational-literals"],
          area="powers"),
    undecided("sqrt_square_real", "vocabulary",
        area="powers", sympy_source="sqrt(r**2)", sympy_gives="Abs(r)",
        semantics="The input is (r**2)**(1/2) with Eq(re(r), r); nary on main has no Abs, so "
                  "there is no output to expect.",
        options=("A: add Abs (and its Lean meaning)", "B: leave out until then"),
        question="Add Abs to the vocabulary?"),
    entry("square_of_sqrt", (x ** half()) ** 2, x, sympy="auto",
          tags=["rule", "rational-literals"], area="powers",
          note="true for every complex x, including 0"),
    entry("sqrt_times_sqrt", x ** half() * x ** half(), x, sympy="auto",
          tags=["rule", "rational-literals", "literal-arithmetic"], area="powers",
          note="true for every complex x, including 0"),
    rejected("powsimp_sqrt_force", x ** half() * y ** half(), (x * y) ** half(),
        area="powers", sympy_source="powsimp(sqrt(x)*sqrt(y), force=True)",
        sympy_gives="sqrt(x*y)",
        semantics="At x = y = -1: I*I = -1 and sqrt(1) = 1.",
        options=("A: reject (as now)",),
        question="As expand_log_force."),
    entry("i_squared", I ** 2, -1, sympy="auto", tags=["special-values"], area="complex"),
    undecided("even_power_of_minus_one", "vocabulary",
        area="powers", sympy_source="(-1)**(2*n)", sympy_gives="1",
        semantics="Needs n integer. Main has no way to say that; open PR #28 (number sets) "
                  "would give one. Same for sin(pi*n) -> 0 (sin_integer_pi).",
        options=("A: add these entries once #28 is merged", "B: leave out"),
        question="Add integer-assumption entries after #28?"),

    # ---- exp and log ---------------------------------------------------
    entry("exp_log", exp(log(x)), x, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "assumptions"], area="exp-log"),
    undecided("exp_log_unconditional", "condition", exp(log(x)), x,
        area="exp-log", sympy_source="exp(log(x))", sympy_gives="x",
        semantics="log(0) has no value, so exp(log(x)) -> x needs Ne(x, 0); the entry exp_log "
                  "has zero=False. Same for exp(2*log(x)) -> x**2 and exp(log(x)/2) -> "
                  "sqrt(x), also automatic in SymPy.",
        options=_CONDITION_OPTIONS,
        question="Same, for exp(log(x)) -> x and its relatives.",
        numeric="definedness"),
    entry("exp_two_log", exp(2 * log(x)), x ** 2, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "assumptions"], area="exp-log"),
    entry("exp_half_log", exp(log(x) / 2), x ** half(), sympy="auto",
          assume={"x": NONZERO}, tags=["rule", "assumptions", "rational-literals"],
          area="exp-log"),
    entry("log_exp_real", log(exp(x)), x, sympy="auto", assume={"x": REAL},
          tags=["rule", "assumptions"], area="exp-log"),
    entry("exp_add", exp(x) * exp(y), exp(x + y), sympy="powsimp",
          tags=["rule"], area="exp-log"),
    entry("exp_squared", exp(x) ** 2, exp(2 * x), sympy="auto",
          tags=["rule", "decide-literals"], area="exp-log",
          note="exp(a)**n -> exp(n*a) holds for an integer n"),
    entry("e_pow", E ** x, exp(x), sympy="auto", tags=["rule"], area="exp-log"),
    entry("exp_one", exp(1), E, sympy="auto", tags=["rule"], area="exp-log"),
    entry("exp_zero", exp(0), 1, sympy="auto", tags=["special-values"], area="exp-log"),
    entry("log_one", log(1), 0, sympy="auto", tags=["special-values"], area="exp-log"),
    entry("log_e", log(E), 1, sympy="auto", tags=["special-values"], area="exp-log"),
    undecided("log_zero", "off-domain",
        area="exp-log", sympy_source="log(0)", sympy_gives="zoo",
        semantics="log(0) has no value.",
        options=("as one_over_zero",),
        question="As one_over_zero.",
        no_value=log(n(0))),
    entry("exp_i_pi", exp(I * pi), -1, sympy="auto", tags=["special-values"],
          area="exp-log"),
    entry("log_mul_positive", log(x * y), log(x) + log(y), sympy="expand_log",
          assume={"x": POSITIVE, "y": POSITIVE}, tags=["rule", "assumptions"],
          area="exp-log"),
    rejected("expand_log_force", log(x * y), log(x) + log(y),
        area="exp-log", sympy_source="expand_log(log(x*y), force=True)",
        sympy_gives="log(x) + log(y)",
        semantics="At x = y = -1: log(1) = 0, log(-1) + log(-1) = 2*pi*I. force=True tells SymPy "
                  "to ignore the assumptions; documented as unsafe. log_mul_positive is the "
                  "entry with x, y positive.",
        options=("A: reject (as now)",),
        question="None expected: wrong values, not a question of semantics."),
    entry("log_add_positive", log(x) + log(y), log(x * y), sympy="logcombine",
          assume={"x": POSITIVE, "y": POSITIVE}, tags=["rule", "assumptions"],
          area="exp-log", note="the reverse of log_mul_positive: which way is 'simpler' "
                               "is a strategy question"),
    rejected("logcombine_force", log(x) + log(y), log(x * y),
        area="exp-log", sympy_source="logcombine(log(x) + log(y), force=True)",
        sympy_gives="log(x*y)",
        semantics="The reverse of expand_log_force, wrong at the same point.",
        options=("A: reject (as now)",),
        question="As expand_log_force."),
    entry("log_pow_positive", log(x ** 2), 2 * log(x), sympy="expand_log",
          assume={"x": POSITIVE}, tags=["rule", "assumptions"], area="exp-log"),
    entry("log_inverse_positive", log(1 / x), -log(x), sympy="expand_log",
          assume={"x": POSITIVE}, tags=["rule", "assumptions"], area="exp-log"),

    # ---- trigonometry --------------------------------------------------
    entry("sin_neg", sin(-x), -sin(x), sympy="auto", tags=["rule"], area="trig"),
    entry("cos_neg", cos(-x), cos(x), sympy="auto", tags=["rule"], area="trig"),
    entry("tan_neg", tan(-x), -tan(x), sympy="auto", tags=["rule"], area="trig"),
    entry("sin_period", sin(x + 2 * pi), sin(x), sympy="auto", tags=["rule"], area="trig"),
    entry("tan_period", tan(x + pi), tan(x), sympy="auto", tags=["rule"], area="trig"),
    entry("cos_pi_minus", cos(pi - x), -cos(x), sympy="auto", tags=["rule"], area="trig"),
    entry("sin_half_pi_minus", sin(pi / 2 - x), cos(x), sympy="auto",
          tags=["rule", "rational-literals"], area="trig",
          note="pi/2 is Mul(pi, Pow(2, -1)) on both sides of the rule"),
    entry("sin_pi", sin(pi), 0, sympy="auto", tags=["special-values"], area="trig"),
    undecided("sin_integer_pi", "vocabulary",
        area="trig", sympy_source="sin(pi*n)", sympy_gives="0",
        semantics="As even_power_of_minus_one.",
        options=("as even_power_of_minus_one",),
        question="As even_power_of_minus_one."),
    entry("cos_pi", cos(pi), -1, sympy="auto", tags=["special-values"], area="trig"),
    entry("sin_pi_sixth", sin(pi / 6), half(), sympy="auto",
          tags=["special-values", "rational-literals"], area="trig"),
    entry("tan_pi_quarter", tan(pi / 4), 1, sympy="auto",
          tags=["special-values", "rational-literals"], area="trig"),
    entry("pythagoras", sin(x) ** 2 + cos(x) ** 2, 1, sympy="trigsimp",
          tags=["rule"], area="trig"),
    entry("pythagoras_inside_sum", sin(x) ** 2 + cos(x) ** 2 + y, y + 1, sympy="simplify",
          tags=["rule"], area="trig",
          note="main's engine matches part of a sum at the top, so one rule does it"),
    entry("one_minus_sin_squared", 1 - sin(x) ** 2, cos(x) ** 2, sympy="trigsimp",
          tags=["strategy", "matching"], area="trig"),
    entry("sin_over_cos", sin(x) / cos(x), tan(x), sympy="simplify", tags=["rule"],
          area="trig", note="both sides have no value exactly where cos(x) = 0"),
    undecided("tan_cos", "condition", tan(x) * cos(x), sin(x),
        area="trig", sympy_source="simplify(tan(x)*cos(x))", sympy_gives="sin(x)",
        semantics="Where cos(x) = 0 the left side has no value. The condition Ne(cos(x), 0) is "
                  "not a SymPy assumption on x.",
        options=_CONDITION_OPTIONS[:1] + (
            "A': as A, with the hand-written condition Ne(cos(x), 0)",) + _CONDITION_OPTIONS[1:],
        question="Same as cancel_removable_singularity, for tan(x)*cos(x) -> sin(x).",
        numeric="definedness"),
    undecided("tan_pole", "off-domain",
        area="trig", sympy_source="tan(pi/2)", sympy_gives="zoo",
        semantics="tan has no value where cos is 0.",
        options=("as one_over_zero",),
        question="As one_over_zero.",
        no_value=tan(pi * half())),
    entry("expand_sin_double", sin(2 * x), 2 * sin(x) * cos(x), sympy="expand_trig",
          tags=["expansion"], area="trig"),
    entry("sin_double", 2 * sin(x) * cos(x), sin(2 * x), sympy="trigsimp",
          tags=["strategy"], area="trig"),
    entry("cos_double", cos(x) ** 2 - sin(x) ** 2, cos(2 * x), sympy="trigsimp",
          tags=["strategy"], area="trig"),
    entry("tan_squared_plus_one", tan(x) ** 2 + 1, cos(x) ** -2, sympy="trigsimp",
          tags=["strategy"], area="trig",
          note="both sides have no value exactly where cos(x) = 0"),
    entry("sin4_minus_cos4", sin(x) ** 4 - cos(x) ** 4, -cos(2 * x), sympy="simplify",
          tags=["strategy", "normal-form"], area="trig"),

    # ---- complex numbers -----------------------------------------------
    entry("re_i", re(I), 0, sympy="auto", tags=["special-values"], area="complex"),
    entry("re_literal", re(n(3)), 3, sympy="auto",
          tags=["special-values", "decide-literals"], area="complex"),
    entry("re_real", re(x), x, sympy="auto", assume={"x": REAL},
          tags=["rule", "assumptions"], area="complex",
          note="the condition is literally Eq(re(x), x)"),

    # ---- relations -----------------------------------------------------
    entry("eq_self", nr.Eq(x, x), true, sympy="auto", tags=["rule", "definedness"],
          area="relational"),
    entry("ne_self", nr.Ne(x, x), false, sympy="auto", tags=["rule", "definedness"],
          area="relational"),
    entry("lt_self_real", x < x, false, sympy="auto", assume={"x": REAL},
          tags=["rule", "assumptions"], area="relational",
          note="for x not real, x < x has no value in nary, and SymPy leaves it alone"),
    undecided("compare_non_real", "off-domain",
        area="relational", sympy_source="Lt(I, 0)", sympy_gives="TypeError",
        semantics="Lt(I, 0) has no value (a comparison of non-real numbers). SymPy raises "
                  "instead of returning an expression, so it cannot be an entry. For a symbol "
                  "not known to be real, SymPy keeps Lt(x, x) unevaluated; the entry lt_self_real "
                  "has real=True.",
        options=("A: nothing to decide; listed so that entries never compare non-reals",),
        question="None expected.",
        no_value=nr.Lt(I, 0)),
    entry("lt_literals", n(1) < 2, true, sympy="auto", tags=["decide-literals"],
          area="relational"),
    entry("not_lt", Not(x < y), x >= y, sympy="auto", tags=["rule"], area="relational",
          note="for x or y not real, both sides have no value"),

    # ---- logic ---------------------------------------------------------
    entry("not_not", Not(Not(p)), p, sympy="auto", tags=["rule"], area="logic"),
    entry("and_true", And(p, true), p, sympy="auto", tags=["rule"], area="logic"),
    entry("and_false", And(p, false), false, sympy="auto", tags=["rule"], area="logic"),
    entry("or_true", Or(p, true), true, sympy="auto", tags=["rule"], area="logic"),
    entry("and_self", And(p, p), p, sympy="auto", tags=["rule"], area="logic"),
    entry("excluded_middle", Or(p, Not(p)), true, sympy="simplify_logic",
          tags=["rule", "definedness"], area="logic"),
    entry("contradiction", And(p, Not(p)), false, sympy="simplify_logic",
          tags=["rule", "definedness"], area="logic"),
    entry("absorption", And(p, Or(p, q)), p, sympy="simplify_logic",
          tags=["rule", "definedness"], area="logic"),
    entry("de_morgan", Not(And(p, q)), Or(Not(p), Not(q)), sympy="to_nnf",
          tags=["rule"], area="logic"),

    # ---- calculus ------------------------------------------------------
    entry("derivative_sin", Derivative(sin)(x), cos(x), sympy="doit",
          tags=["calculus", "rule"], area="calculus"),
    entry("derivative_square", Derivative(Lambda(t, t ** 2))(x), 2 * x, sympy="doit",
          tags=["calculus", "lambda", "literal-arithmetic"], area="calculus"),
    entry("derivative_product", Derivative(Lambda(t, sin(t) * exp(t)))(x),
          exp(x) * sin(x) + exp(x) * cos(x), sympy="doit",
          tags=["calculus", "lambda"], area="calculus"),
    entry("derivative_chain", Derivative(Lambda(t, sin(t ** 2)))(x), 2 * x * cos(x ** 2),
          sympy="doit", tags=["calculus", "lambda", "literal-arithmetic"],
          area="calculus"),
    entry("derivative_log_positive", Derivative(log)(x), 1 / x, sympy="doit",
          assume={"x": POSITIVE}, tags=["calculus", "rule", "assumptions"],
          area="calculus",
          note="on the negative reals the complex derivative of log does not exist; "
               "see the undecided entry derivative_log"),
    undecided("derivative_log", "off-domain", Derivative(log)(x), 1 / x,
        area="calculus", sympy_source="diff(log(x), x)", sympy_gives="1/x",
        semantics="Derivative(log)(x) has no value where log is not complex-differentiable: "
                  "at 0 and on the negative reals (log's branch cut), by the definition of "
                  "Derivative in lean/Nary/Calculus.lean. 1/x has a value on the negative reals. The numerical "
                  "check cannot see this (log has a value near every point of the cut, and "
                  "mpmath's numerical derivative there is 1/x), so it finds no counterexample; "
                  "the entry derivative_log_positive has x positive.",
        options=("A: keep the complex derivative; catalogue only x positive (as now)",
                 "B: make Derivative the derivative along the real line where the argument "
                 "is real (the open question in lean/Nary/Calculus.lean), which changes "
                 "what Derivative(re) and Derivative(log) mean on the cut"),
        question="Which derivative should Derivative be on the negative reals for log?",
        numeric="none"),

    # ---- lambdas -------------------------------------------------------
    entry("call_lambda", Lambda(t, sin(t))(x), sin(x), sympy="auto", tags=["lambda"],
          area="lambda"),
    entry("call_lambda_literal", Lambda(t, t ** 2)(n(3)), 9, sympy="auto",
          tags=["lambda", "literal-arithmetic", "decide-literals"], area="lambda"),

    # ---- conventions: how the catalogue writes and compares things ----
    undecided("argument_order", "comparison",
        area="conventions", sympy_source="Add(y, x).args", sympy_gives="(x, y)",
        semantics="SymPy sorts the arguments of Add, Mul, And, Or into a canonical order; nary "
                  "keeps Add(y, x) and Add(x, y) apart and has no canonical order. "
                  "catalogue/engine.py compares the engine's result with expected after "
                  "flattening and sorting the functions recorded as flat and unordered (Add and "
                  "Mul; proved in Lean). And and Or are not recorded as unordered, so they are "
                  "compared as written.",
        options=("A: compare modulo flat/unordered (as now)",
                 "B: require one exact form, which needs a canonical order in nary",
                 "C: record And and Or as unordered too (true under Kleene logic) so that "
                 "they are compared modulo order as well"),
        question="What should 'the engine reaches expected' mean: modulo AC, or an exact "
                 "canonical form?"),
    undecided("and_or_order", "comparison",
        area="conventions", sympy_source="And(q, p).args", sympy_gives="(p, q)",
        semantics="As argument_order, for And.",
        options=("as argument_order",),
        question="As argument_order."),
    undecided("rationals", "representation",
        area="conventions", sympy_source="Pow(2, -1)", sympy_gives="1/2",
        semantics="Main has integer literals only, so the catalogue writes 1/2 as Pow(2, -1) and "
                  "3/2 as Mul(3, Pow(2, -1)); SymPy's Pow(2, -1) is Rational(1, 2). An engine "
                  "with rational literals would turn Pow(2, -1) into a literal and no longer "
                  "match these expected outputs as written.",
        options=("A: keep Pow(2, -1) as the written form of 1/2",
                 "B: add rational literals and rewrite the expected outputs with them"),
        question="Will nary get rational literals, and should the expected outputs then "
                 "use them?"),
    undecided("nonzero_means_real", "assumptions",
        area="conventions", sympy_source="Symbol('t', nonzero=True).is_real", sympy_gives="True",
        semantics="SymPy's nonzero=True also means real; the complex 'not zero' is zero=False. "
                  "The catalogue uses zero=False, translated as Ne(x, 0). positive and negative "
                  "imply real in both systems (Gt(x, 0) has no value for x not real). Also, a "
                  "SymPy Symbol with no assumptions may be infinite, while an nary symbol in an "
                  "entry stands for a complex number.",
        options=("A: keep the translation table in catalogue/entry.py as it is",),
        question="Is the table ASSUMPTIONS in catalogue/entry.py the translation you want?"),
]


def with_status(*statuses):
    """The entries with one of ``statuses``, in the order of ``ENTRIES``."""
    unknown = set(statuses) - set(STATUSES)
    if unknown:
        raise ValueError(f"unknown statuses {sorted(unknown)}")
    return [e for e in ENTRIES if e.status in statuses]

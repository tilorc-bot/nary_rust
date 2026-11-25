"""The catalogue: desired simplifications, each one SymPy makes.

Every entry here is checked by ``tests/test_catalogue.py``:

1. SymPy (the version in ``catalogue.sympy_check.SYMPY_VERSION``), with the
   recorded call and assumptions, turns ``input`` into ``expected``.
2. ``catalogue.numeric`` finds no point where ``when`` holds and the two
   sides differ under nary's semantics (issue #2).
3. It is run through ``nary.rewriting.rewrite`` with today's rules; the
   entries in ``PASSING`` must reach ``expected``, the others are expected
   failures.

Expected outputs are written in SymPy's argument order. Rationals are
written as nary has to write them today: 1/2 is ``Pow(2, -1)`` and 3/2 is
``Mul(3, Pow(2, -1))``.

Cases where SymPy and nary do not line up are not here; they are in
``catalogue.mismatches``.
"""

import nary as nr
from nary import E, I, Lambda, Pow, cos, exp, log, pi, re, sin, tan
from nary.calculus import Derivative
from nary.logic import And, Not, Or, false, true

from .entry import entry

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
    entry("log_mul_zero", log(x) * 0, 0, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "definedness"], area="arithmetic"),
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

    # ---- powers --------------------------------------------------------
    entry("pow_one", x ** 1, x, sympy="auto", tags=["rule"], area="powers"),
    entry("pow_zero", x ** 0, 1, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "assumptions"], area="powers"),
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
    entry("pow_pow_positive", (x ** a) ** b, x ** (a * b), sympy="auto",
          assume={"x": POSITIVE, "a": REAL}, tags=["rule", "assumptions"], area="powers"),
    entry("pow_of_product_positive", (x * y) ** a, x ** a * y ** a,
          sympy="expand_power_base", assume={"x": POSITIVE, "y": POSITIVE},
          tags=["rule", "assumptions", "expansion"], area="powers"),
    entry("pow_of_product_literal", (x * y) ** 2, x ** 2 * y ** 2, sympy="auto",
          tags=["expansion", "decide-literals"], area="powers"),
    entry("sqrt_of_square_positive", (x ** 2) ** half(), x, sympy="auto",
          assume={"x": POSITIVE}, tags=["rule", "assumptions", "rational-literals"],
          area="powers"),
    entry("square_of_sqrt", (x ** half()) ** 2, x, sympy="auto",
          tags=["rule", "rational-literals"], area="powers",
          note="true for every complex x, including 0"),
    entry("sqrt_times_sqrt", x ** half() * x ** half(), x, sympy="auto",
          tags=["rule", "rational-literals", "literal-arithmetic"], area="powers",
          note="true for every complex x, including 0"),
    entry("i_squared", I ** 2, -1, sympy="auto", tags=["special-values"], area="complex"),

    # ---- exp and log ---------------------------------------------------
    entry("exp_log", exp(log(x)), x, sympy="auto", assume={"x": NONZERO},
          tags=["rule", "assumptions"], area="exp-log"),
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
    entry("exp_i_pi", exp(I * pi), -1, sympy="auto", tags=["special-values"],
          area="exp-log"),
    entry("log_mul_positive", log(x * y), log(x) + log(y), sympy="expand_log",
          assume={"x": POSITIVE, "y": POSITIVE}, tags=["rule", "assumptions"],
          area="exp-log"),
    entry("log_add_positive", log(x) + log(y), log(x * y), sympy="logcombine",
          assume={"x": POSITIVE, "y": POSITIVE}, tags=["rule", "assumptions"],
          area="exp-log", note="the reverse of log_mul_positive: which way is 'simpler' "
                               "is a strategy question"),
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
               "see the mismatch derivative_log"),

    # ---- lambdas -------------------------------------------------------
    entry("call_lambda", Lambda(t, sin(t))(x), sin(x), sympy="auto", tags=["lambda"],
          area="lambda"),
    entry("call_lambda_literal", Lambda(t, t ** 2)(n(3)), 9, sympy="auto",
          tags=["lambda", "literal-arithmetic", "decide-literals"], area="lambda"),
]

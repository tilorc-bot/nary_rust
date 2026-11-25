"""Cases where SymPy and nary do not line up. Not decided here: each one
says what SymPy does, what nary's semantics (issue #2) say, and the options.
Tilo decides.

These are not catalogue entries and are not run through the engine. What
``tests/test_catalogue.py`` checks for each one:

- ``sympy`` is a SymPy expression in Python syntax, evaluated with
  everything from ``sympy`` and the symbols ``x, y, a, b`` (no
  assumptions), ``n`` (``integer=True``), ``r`` (``real=True``), ``p, q``;
  its ``repr`` must be ``sympy_gives``, or, if it raises, the name of the
  exception. So what SymPy does is a tested fact for the pinned version.
- ``claim``, when given, is the claim SymPy's result makes, written in nary:
  ``(input, output, condition)``. ``catalogue.numeric.check`` is run on it,
  and what it finds must be ``numeric``:

  - ``"value"``: a point where both sides have a value and the values
    differ. SymPy's result is wrong, whatever one thinks of definedness;
    the kind is then ``"rejected"``.
  - ``"definedness"``: points where one side has a value and the other has
    none, and no point where both have different values. SymPy's result is
    right where both sides have a value; nary's semantics reject it as a
    rewrite.
  - ``"none"``: no counterexample among the points tried. Used where the
    difference is one the numerical check cannot see; the text says why.

- ``no_value``, when given, is an nary expression that must have no value
  under ``catalogue.numeric``: what SymPy gives a value to (or refuses).

Kinds: ``condition`` (SymPy's result holds only under a condition SymPy
does not ask for), ``off-domain`` (SymPy gives a value, or an error, where
nary has no value), ``vocabulary`` (nary has no way to write the input,
output or assumption), ``comparison`` (what "reaches expected" should
mean), ``representation``, ``assumptions`` (translating SymPy's
assumptions), ``rejected`` (SymPy's result is wrong).
"""

from dataclasses import dataclass

import nary as nr
from nary import I, Pow, cos, exp, log, pi, sin, tan
from nary.calculus import Derivative

__all__ = ["KINDS", "MISMATCHES", "Mismatch"]

KINDS = ("condition", "off-domain", "vocabulary", "comparison", "representation",
         "assumptions", "rejected")

x, y = nr.NumberKind("x"), nr.NumberKind("y")
a, b = nr.NumberKind("a"), nr.NumberKind("b")
half = Pow(nr.NumberKind(2), -1)
zero, one = nr.NumberKind(0), nr.NumberKind(1)


@dataclass(frozen=True)
class Mismatch:
    name: str
    kind: str
    sympy: str
    sympy_gives: str
    nary: str
    options: tuple
    question: str
    claim: tuple = None
    numeric: str = None
    no_value: object = None


# Options that recur for the "condition" kind.
_CONDITION_OPTIONS = (
    "A: catalogue only the conditioned form, as an entry whose SymPy call has the "
    "assumption that makes it right (what the catalogue does where SymPy has such an "
    "assumption)",
    "B: also catalogue SymPy's unconditioned result as a 'generic' simplification, true "
    "where both sides have a value; nary would need a second, weaker notion of rewrite",
    "C: leave it out",
)

MISMATCHES = [
    # ---- SymPy's result needs a condition it does not ask for ----------
    Mismatch(
        "div_self_unconditional", "condition", "x/x", "1",
        nary="x/x has no value at x = 0, 1 has; Mul(x, Pow(x, -1)) -> 1 is a rewrite only "
             "where Ne(x, 0). SymPy does it automatically and cannot be stopped, so SymPy "
             "cannot even represent x/x. The entry div_self has zero=False.",
        options=_CONDITION_OPTIONS,
        question="Is SymPy's automatic x/x -> 1 wanted in any form beyond div_self (with "
                 "Ne(x, 0))?",
        claim=(x / x, one, None), numeric="definedness"),
    Mismatch(
        "pow_zero_unconditional", "condition", "x**0", "1",
        nary="Pow(0, 0) has no value (issue #2), so x**0 -> 1 needs Ne(x, 0). The entry "
             "pow_zero has zero=False. SymPy also gives 0**0 = 1 (see zero_pow_zero).",
        options=_CONDITION_OPTIONS,
        question="Same as div_self_unconditional, for x**0 -> 1.",
        claim=(x ** 0, one, None), numeric="definedness"),
    Mismatch(
        "exp_log_unconditional", "condition", "exp(log(x))", "x",
        nary="log(0) has no value, so exp(log(x)) -> x needs Ne(x, 0); the entry exp_log "
             "has zero=False. Same for exp(2*log(x)) -> x**2 and exp(log(x)/2) -> "
             "sqrt(x), also automatic in SymPy.",
        options=_CONDITION_OPTIONS,
        question="Same, for exp(log(x)) -> x and its relatives.",
        claim=(exp(log(x)), x, None), numeric="definedness"),
    Mismatch(
        "log_mul_zero_unconditional", "condition", "0*log(x)", "0",
        nary="At x = 0 the left side has no value. The entry log_mul_zero has zero=False. "
             "Behind it: SymPy erases a factor whenever it multiplies by 0 (x*0 -> 0 also "
             "for a Symbol that might be infinite), nary only an erased part that has a "
             "value (the 'definedness' tag).",
        options=_CONDITION_OPTIONS,
        question="Same, for 0*f(x) -> 0 where f(x) may have no value.",
        claim=(log(x) * 0, zero, None), numeric="definedness"),
    Mismatch(
        "powsimp_unconditional", "condition", "powsimp(x**a*x**b)", "x**(a + b)",
        nary="At x = 0, a = 2, b = -1 the left side has no value (0**-1) and the right is "
             "0. The entry mul_powers_positive has x positive; mul_powers_literal needs the "
             "exponents decided.",
        options=_CONDITION_OPTIONS,
        question="Same, for x**a * x**b -> x**(a+b).",
        claim=(x ** a * x ** b, x ** (a + b), None), numeric="definedness"),
    Mismatch(
        "cancel_removable_singularity", "condition", "cancel((x**2 - 1)/(x - 1))", "x + 1",
        nary="At x = 1 the left side has no value. The condition is Ne(x, 1), which no "
             "SymPy assumption on x expresses, so there is no entry for it.",
        options=(
            "A: allow conditions that are not SymPy assumptions, written by hand in nary and "
            "checked numerically (the catalogue now derives every condition from a SymPy "
            "assumption, so that SymPy and the check see the same claim)",
        ) + _CONDITION_OPTIONS[1:],
        question="Should the catalogue have hand-written conditions such as Ne(x, 1), "
                 "for cancel and the like?",
        claim=((x ** 2 - 1) / (x - 1), x + 1, None), numeric="definedness"),
    Mismatch(
        "tan_cos", "condition", "simplify(tan(x)*cos(x))", "sin(x)",
        nary="Where cos(x) = 0 the left side has no value. The condition Ne(cos(x), 0) is "
             "not a SymPy assumption on x.",
        options=_CONDITION_OPTIONS[:1] + (
            "A': as A, with the hand-written condition Ne(cos(x), 0)",) + _CONDITION_OPTIONS[1:],
        question="Same as cancel_removable_singularity, for tan(x)*cos(x) -> sin(x).",
        claim=(tan(x) * cos(x), sin(x), None), numeric="definedness"),

    # ---- values off the domain ----------------------------------------
    Mismatch(
        "zero_pow_zero", "off-domain", "S(0)**0", "1",
        nary="Pow(0, 0) has no value (issue #2).",
        options=("A: keep nary's choice; never catalogue 0**0 -> 1",
                 "B: give Pow(0, 0) the value 1, as SymPy and Lean's Mathlib do"),
        question="Keep 0**0 without a value?",
        claim=(Pow(zero, 0), one, None), numeric="definedness", no_value=Pow(zero, 0)),
    Mismatch(
        "one_over_zero", "off-domain", "S(1)/0", "zoo",
        nary="Pow(0, -1) has no value; nary has no complex infinity. Same for log(0) "
             "(log_zero) and tan(pi/2) (tan_pole).",
        options=("A: no value, as now; SymPy's zoo never appears in an entry",
                 "B: add zoo (and nan) to nary's vocabulary"),
        question="None expected (issue #2 decided it); listed so that entries never "
                 "expect zoo.",
        no_value=Pow(zero, -1)),
    Mismatch(
        "log_zero", "off-domain", "log(0)", "zoo",
        nary="log(0) has no value.", options=("as one_over_zero",),
        question="As one_over_zero.", no_value=log(zero)),
    Mismatch(
        "tan_pole", "off-domain", "tan(pi/2)", "zoo",
        nary="tan has no value where cos is 0.", options=("as one_over_zero",),
        question="As one_over_zero.", no_value=tan(pi * half)),
    Mismatch(
        "compare_non_real", "off-domain", "Lt(I, 0)", "TypeError",
        nary="Lt(I, 0) has no value (a comparison of non-real numbers). SymPy raises "
             "instead of returning an expression, so it cannot be an entry. For a symbol "
             "not known to be real, SymPy keeps Lt(x, x) unevaluated; the entry lt_self_real "
             "has real=True.",
        options=("A: nothing to decide; listed so that entries never compare non-reals",),
        question="None expected.", no_value=nr.Lt(I, 0)),
    Mismatch(
        "derivative_log", "off-domain", "diff(log(x), x)", "1/x",
        nary="Derivative(log)(x) has no value where log is not complex-differentiable: at 0 "
             "and on the negative reals (log's branch cut), by the definition of Derivative in "
             "lean/Nary/Calculus.lean. 1/x has a value on the negative reals. The numerical "
             "check cannot see this (log has a value near every point of the cut, and "
             "mpmath's numerical derivative there is 1/x), so it finds no counterexample; "
             "the entry derivative_log_positive has x positive.",
        options=("A: keep the complex derivative; catalogue only x positive (as now)",
                 "B: make Derivative the derivative along the real line where the argument "
                 "is real (the open question in lean/Nary/Calculus.lean), which changes "
                 "what Derivative(re) and Derivative(log) mean on the cut"),
        question="Which derivative should Derivative be on the negative reals for log?",
        claim=(Derivative(log)(x), 1 / x, None), numeric="none"),

    # ---- vocabulary nary lacks ----------------------------------------
    Mismatch(
        "sqrt_square_real", "vocabulary", "sqrt(r**2)", "Abs(r)",
        nary="The input is (r**2)**(1/2) with Eq(re(r), r); nary on main has no Abs, so "
             "there is no output to expect.",
        options=("A: add Abs (and its Lean meaning)", "B: leave out until then"),
        question="Add Abs to the vocabulary?"),
    Mismatch(
        "even_power_of_minus_one", "vocabulary", "(-1)**(2*n)", "1",
        nary="Needs n integer. Main has no way to say that; open PR #28 (number sets) "
             "would give one. Same for sin(pi*n) -> 0 (sin_integer_pi).",
        options=("A: add these entries once #28 is merged", "B: leave out"),
        question="Add integer-assumption entries after #28?"),
    Mismatch(
        "sin_integer_pi", "vocabulary", "sin(pi*n)", "0",
        nary="As even_power_of_minus_one.", options=("as even_power_of_minus_one",),
        question="As even_power_of_minus_one."),

    # ---- what "equal to expected" means --------------------------------
    Mismatch(
        "argument_order", "comparison", "Add(y, x).args", "(x, y)",
        nary="SymPy sorts the arguments of Add, Mul, And, Or into a canonical order; nary "
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
    Mismatch(
        "and_or_order", "comparison", "And(q, p).args", "(p, q)",
        nary="As argument_order, for And.", options=("as argument_order",),
        question="As argument_order."),

    # ---- representation ------------------------------------------------
    Mismatch(
        "rationals", "representation", "Pow(2, -1)", "1/2",
        nary="Main has integer literals only, so the catalogue writes 1/2 as Pow(2, -1) and "
             "3/2 as Mul(3, Pow(2, -1)); SymPy's Pow(2, -1) is Rational(1, 2). An engine "
             "with rational literals would turn Pow(2, -1) into a literal and no longer "
             "match these expected outputs as written.",
        options=("A: keep Pow(2, -1) as the written form of 1/2",
                 "B: add rational literals and rewrite the expected outputs with them"),
        question="Will nary get rational literals, and should the expected outputs then "
                 "use them?"),

    # ---- assumptions ---------------------------------------------------
    Mismatch(
        "nonzero_means_real", "assumptions", "Symbol('t', nonzero=True).is_real", "True",
        nary="SymPy's nonzero=True also means real; the complex 'not zero' is zero=False. "
             "The catalogue uses zero=False, translated as Ne(x, 0). positive and negative "
             "imply real in both systems (Gt(x, 0) has no value for x not real). Also, a "
             "SymPy Symbol with no assumptions may be infinite, while an nary symbol in an "
             "entry stands for a complex number.",
        options=("A: keep the translation table in catalogue/entry.py as it is",),
        question="Is the table ASSUMPTIONS in catalogue/entry.py the translation you want?"),

    # ---- SymPy results the numerical check shows to be wrong ------------
    Mismatch(
        "expand_log_force", "rejected", "expand_log(log(x*y), force=True)",
        "log(x) + log(y)",
        nary="At x = y = -1: log(1) = 0, log(-1) + log(-1) = 2*pi*I. force=True tells SymPy "
             "to ignore the assumptions; documented as unsafe. log_mul_positive is the "
             "entry with x, y positive.",
        options=("A: reject (as now)",),
        question="None expected: wrong values, not a question of semantics.",
        claim=(log(x * y), log(x) + log(y), None), numeric="value"),
    Mismatch(
        "logcombine_force", "rejected", "logcombine(log(x) + log(y), force=True)",
        "log(x*y)",
        nary="The reverse of expand_log_force, wrong at the same point.",
        options=("A: reject (as now)",), question="As expand_log_force.",
        claim=(log(x) + log(y), log(x * y), None), numeric="value"),
    Mismatch(
        "powdenest_force", "rejected", "powdenest((x**a)**b, force=True)", "x**(a*b)",
        nary="At x = -1, a = 2, b = 1/2: ((-1)**2)**(1/2) = 1 and (-1)**1 = -1. "
             "pow_pow_positive is the entry with x positive and a real.",
        options=("A: reject (as now)",), question="As expand_log_force.",
        claim=((x ** a) ** b, x ** (a * b), None), numeric="value"),
    Mismatch(
        "powsimp_sqrt_force", "rejected", "powsimp(sqrt(x)*sqrt(y), force=True)",
        "sqrt(x*y)",
        nary="At x = y = -1: I*I = -1 and sqrt(1) = 1.",
        options=("A: reject (as now)",), question="As expand_log_force.",
        claim=(x ** half * y ** half, (x * y) ** half, None), numeric="value"),
]

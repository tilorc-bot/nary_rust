"""Printing an expression as a Lean term.

``lean/`` is a Lean 4 project that says what each declared function means
(see ``lean/README.md``). ``to_lean(e)`` writes the expression ``e`` as the
Lean term built from those definitions, and ``to_lean_example(e)`` writes a
whole line that Lean can check on its own: an ``example`` with the free
symbols of ``e`` as variables, the type of the result, and the term. The
line starts with ``noncomputable``, because the definitions in ``lean/``
are noncomputable (they use Mathlib's complex functions and classical
logic) and Lean would otherwise try to compile the example.

    >>> from nary import Lambda, NumberKind, sin
    >>> from nary.calculus import Derivative, Integral, NumberFunction
    >>> from nary.lean import to_lean, to_lean_example
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> to_lean(x - y)
    'Nary.Add [some x, Nary.Mul [Nary.lit (-1), some y]]'
    >>> to_lean(x ** 2)
    'Nary.Pow (some x) (Nary.lit 2)'
    >>> to_lean(Derivative(sin)(x))
    'Nary.apply (Nary.Derivative (fun z => Nary.sin (some z))) (some x)'
    >>> to_lean(Lambda(x, sin(x))(y))
    'Nary.apply (fun x => Nary.sin (some x)) (some y)'
    >>> f = NumberFunction("f")
    >>> to_lean(f(x) < y)
    'Nary.Lt (Nary.apply f (some x)) (some y)'
    >>> print(to_lean_example(x - y))
    noncomputable example (x y : ℂ) : Nary.Number := Nary.Add [some x, Nary.Mul [Nary.lit (-1), some y]]
    >>> to_lean(Integral(sin, 0, x))
    Traceback (most recent call last):
        ...
    ValueError: Integral has no Lean definition: it is not in nary.lean.LEAN_NAMES

How each part is printed:

- A symbol of ``NumberKind`` named ``x`` is a Lean variable ``x : ℂ`` and
  prints as ``some x``; a ``BoolKind`` symbol ``p`` is ``p : Prop`` and
  prints as ``some p``; a symbol ``f`` of ``FunctionKind((NumberKind,),
  NumberKind)`` is ``f : ℂ → Nary.Number`` and prints as ``f``.
- An integer literal prints as ``Nary.lit 3`` or ``Nary.lit (-1)``.
- The declared functions and constants print with their full Lean names,
  ``Nary.Add``, ``Nary.I``, ``Nary.true``, because several of them (``Eq``,
  ``And``, ``Not``, ``Pow``, ``true``, ...) are also names in Lean itself.
  Which declaration is which Lean definition is the table ``LEAN_NAMES``
  below, keyed by the declared object, not by its name.
- A function declared with ``rest=`` takes its arguments as a Lean list,
  ``Nary.Add [a, b]``; any other takes them one after the other.
- ``Lambda(x, body)``, with one ``NumberKind`` variable and a
  ``NumberKind`` body, prints as ``fun x => body``.
- A call whose head is not a declared function (a lambda, a function
  symbol, ``Derivative(f)``) prints with ``Nary.apply``.
- A declared function of one number used as a value, such as ``sin`` in
  ``Derivative(sin)``, prints as ``fun z => Nary.sin (some z)``.

A symbol name that is not a plain ASCII Lean identifier, or that is a Lean
keyword (any word that Lean reads as a keyword once Mathlib is imported),
is written between ``«`` and ``»``: ``NumberKind("fun")`` prints as
``some «fun»`` and ``NumberKind("θ")`` as ``some «θ»``.

Refused, with a ``ValueError`` that names the part with no Lean
definition: ``Integral``, ``Sum``, ``Product``, ``Limit``,
``Antiderivative``, everything in ``nary.matrices``, any other function or
constant that ``LEAN_NAMES`` does not list, a declared function used as a
value unless it is a function of one number, a lambda of more than one
variable or of other kinds, symbols of any other kind, literals of any
other kind, and symbol names that cannot be written in Lean: the empty
name, a name containing ``»`` or a control character, and the names
``some`` and ``Nary``, which would hide the Lean names that the output
uses. Also refused: two free symbols with the same name and different
kinds, and a symbol inside a lambda whose variable has the same name and a
different kind (Lean would read it as the variable).

The module is imported as ``nary.lean``; its names are not re-exported
from ``nary``.
"""

import re as _re

from . import arithmetic, calculus, constants, elementary, logic, relational
from ._core import Expr
from .calculus import NumberFunction
from .functions import is_lambda
from .kinds import BoolKind, NumberKind

__all__ = ["LEAN_NAMES", "to_lean", "to_lean_example"]

# The Lean definition of each declared function and constant, keyed by the
# declared object itself. A function is printed as its Lean definition only
# if it is in this table; whether it takes a list comes from its declaration
# (``rest=``), not from here.
LEAN_NAMES = {
    arithmetic.Add: "Nary.Add",
    arithmetic.Mul: "Nary.Mul",
    arithmetic.Pow: "Nary.Pow",
    elementary.sin: "Nary.sin",
    elementary.cos: "Nary.cos",
    elementary.tan: "Nary.tan",
    elementary.exp: "Nary.exp",
    elementary.log: "Nary.log",
    elementary.re: "Nary.re",
    constants.pi: "Nary.pi",
    constants.E: "Nary.E",
    constants.I: "Nary.I",
    relational.Eq: "Nary.Eq",
    relational.Ne: "Nary.Ne",
    relational.Lt: "Nary.Lt",
    relational.Le: "Nary.Le",
    relational.Gt: "Nary.Gt",
    relational.Ge: "Nary.Ge",
    logic.And: "Nary.And",
    logic.Or: "Nary.Or",
    logic.Not: "Nary.Not",
    logic.true: "Nary.true",
    logic.false: "Nary.false",
    calculus.Derivative: "Nary.Derivative",
}

# The Lean type of a variable of each kind of symbol, and of a result.
_VARIABLE_TYPES = {NumberKind: "ℂ", BoolKind: "Prop", NumberFunction: "ℂ → Nary.Number"}
_RESULT_TYPES = {
    NumberKind: "Nary.Number",
    BoolKind: "Nary.Boolean",
    NumberFunction: "ℂ → Nary.Number",
}

_IDENTIFIER = _re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")

# Words that Lean reads as keywords once Mathlib is imported, so they cannot
# be a plain variable name: every identifier-like token in the token table
# after `import Mathlib` (Lean v4.34.1), plus _ and a few tactic words.
# Writing an ordinary name between « and » does no harm, so a word too many
# here only makes the output less pretty.
_KEYWORDS = frozenset("""
    _ abbrev add_aesop_rules add_decl_doc alias assert_no_sorry
    assert_not_exists assert_not_imported assumeInstancesCommuteDummy at
    attribute axiom bif binder_predicate break builtin_cbv_simproc
    builtin_cbv_simproc_decl builtin_dsimproc builtin_dsimproc_decl
    builtin_grind_propagator builtin_initialize builtin_simproc
    builtin_simproc_decl by by_elab calc catch cbv_eval cbv_simproc
    cbv_simproc_decl class coinductive coinductive_fixpoint continue
    dbg_trace declare_aesop_rule_sets declare_bitwise_int_theorems
    declare_bitwise_uint_theorems declare_command_config_elab
    declare_command_config_elab_legacy declare_config_elab
    declare_config_elab_legacy declare_core_config_elab
    declare_int_theorems declare_simp_like_tactic declare_sint_simprocs
    declare_syntax_cat declare_term_config_elab declare_uint_simprocs
    declare_uint_theorems decreasing_by def def_eval_config_item def_wanted
    deprecate deprecated_module deprecated_syntax deriving distTriang do
    docs_to_verso dsimproc dsimproc_decl elab elab_rules elab_stx_quot else
    end erase_aesop_rules eval_prec eval_prio example exists export
    extend_docs extends finally for forall from from_lrat fun generalizing
    GL grind_annotated grind_pattern grind_propagator guard_min_heartbeats
    have haveI haveI' hiding idbg if import in include include_str
    inductive inductive_fixpoint inferInstanceAs infix infixl infixr
    init_grind_norm init_quot initialize initialize_simps_projections
    insert_to_additive_translation insert_to_dual_translation instance
    instance_wanted irreducible_def kerodon leading_parser lemma let
    let_delayed let_expr let_fun let_impl_detail let_tmp letI letI'
    library_note local logNamedError logNamedErrorAt logNamedWarning
    logNamedWarningAt lrat_proof macro macro_rules match match_expr matches
    max_prec meta mk_iff_of_inductive_prop mod_cast mut mutual
    name_poly_vars name_power_vars namespace nat_lit no_index nofun nomatch
    noncomputable nonrec norm_cast_add_elim nosimp notation notation3
    obtain omit only opaque open over partial partial_fixpoint PiType
    postfix prefix private proof_wanted Prop protected public recall
    recommended_spelling register_builtin_option register_error_explanation
    register_grind_attr register_hint register_label_attr
    register_linter_set register_option register_parser_alias
    register_simp_attr register_sym_dsimp register_sym_simp
    register_tactic_tag renaming repeat return run_cmd run_elab run_meta
    says scoped seal section set_library_suggestions set_option show
    show_panel_widgets show_term show_term_elab simproc simproc_decl sorry
    Sort stacks StateRefT structure sudo suffices suppress_compilation
    syntax tactic_alt tactic_extension tactic_name tactic_tag
    termination_by then theorem theorem_wanted this throwError throwErrorAt
    throwNamedError throwNamedErrorAt to to_additive_name_hint
    to_dual_insert_cast to_dual_insert_cast_fun to_dual_name_hint
    trailing_parser try Type unif_hint universe unless unlock_limits unsafe
    unseal unset_option unsuppress_compilation until using variable
    variables whatsnew where while with with_annotate_term
    with_weak_namespace without_expected_type
""".split())

# Names that the printed term uses unqualified (``some``) or as the start of
# every full name (``Nary``). A variable with one of these names would hide
# them, whether or not it is written with « and ».
_RESERVED = frozenset({"some", "Nary"})


def _identifier(name):
    """``name`` written as a Lean identifier."""
    if not name:
        raise ValueError("a symbol with an empty name cannot be written in Lean")
    if name in _RESERVED:
        raise ValueError(
            f"a symbol named {name} cannot be written in Lean: it would hide "
            f"the Lean name {name} that the printed term uses"
        )
    if _IDENTIFIER.match(name) and name not in _KEYWORDS:
        return name
    if "»" in name or any(not c.isprintable() for c in name):
        raise ValueError(f"the symbol name {name!r} cannot be written in Lean")
    return f"«{name}»"


def _no_definition(e, why=""):
    return ValueError(f"{e!r} has no Lean definition{why}")


def _not_in_table(e):
    return _no_definition(e, ": it is not in nary.lean.LEAN_NAMES")


def _is_declared_function(e):
    return e.is_constant and e.kind.inputs is not None


class _Printer:
    def __init__(self):
        # The free symbols, by name, in the order they are first met.
        self.free = {}
        # The variables of the lambdas around the current subexpression,
        # innermost last.
        self.bound = []

    def symbol(self, e):
        """Record the symbol ``e`` as bound or free and return its name in
        Lean."""
        for variable in reversed(self.bound):
            if variable.name == e.name:
                if variable.kind is not e.kind:
                    raise ValueError(
                        f"the symbol {e.name} of kind {e.kind!r} is inside a "
                        f"Lambda whose variable {e.name} is of kind "
                        f"{variable.kind!r}; Lean would read it as the variable"
                    )
                return _identifier(e.name)
        if e.kind not in _VARIABLE_TYPES:
            raise ValueError(
                f"the symbol {e.name} of kind {e.kind!r} has no Lean definition: "
                f"only symbols of NumberKind, BoolKind and {NumberFunction!r} "
                f"are printed"
            )
        known = self.free.setdefault(e.name, e)
        if known.kind is not e.kind:
            raise ValueError(
                f"two free symbols are named {e.name}, of kinds "
                f"{known.kind!r} and {e.kind!r}"
            )
        return _identifier(e.name)

    def argument(self, e):
        """``e`` as an argument of a Lean application, in parentheses
        unless it is a single name."""
        text, atomic = self.print(e)
        return text if atomic else f"({text})"

    def print(self, e):
        """``e`` in Lean, and whether that is a single name (which then
        needs no parentheses as an argument)."""
        if not isinstance(e, Expr):
            raise TypeError(f"to_lean expects an expression, got {e!r}")

        if e.is_symbol:
            name = self.symbol(e)
            if e.kind is NumberFunction:
                return name, True
            return f"some {name}", False

        if e.is_literal:
            if e.kind is not NumberKind or type(e.value) is not int:
                raise _no_definition(e, ": only integer literals are printed")
            value = e.value
            return (f"Nary.lit {value}" if value >= 0 else f"Nary.lit ({value})"), False

        if e.is_constant:
            if e not in LEAN_NAMES:
                raise _not_in_table(e)
            name = LEAN_NAMES[e]
            if e.kind.inputs is None:
                return name, True
            # A declared function used as a value.
            if e.kind is not NumberFunction:
                raise _no_definition(
                    e, f" as a value: only a declared function of kind "
                    f"{NumberFunction!r} is printed as a value"
                )
            return f"fun z => {name} (some z)", False

        if is_lambda(e):
            *variables, body = e.args
            if len(variables) != 1 or e.kind is not NumberFunction:
                raise _no_definition(
                    e, ": only a Lambda of one NumberKind variable with a "
                    "NumberKind body is printed"
                )
            (variable,) = variables
            self.bound.append(variable)
            try:
                text = f"fun {_identifier(variable.name)} => {self.print(body)[0]}"
            finally:
                self.bound.pop()
            return text, False

        # An application.
        head = e.head
        if _is_declared_function(head):
            if head not in LEAN_NAMES:
                raise _not_in_table(head)
            name = LEAN_NAMES[head]
            fixed = len(head.kind.inputs)
            parts = [name] + [self.argument(a) for a in e.args[:fixed]]
            if head.kind.rest is not None:
                rest = ", ".join(self.print(a)[0] for a in e.args[fixed:])
                parts.append(f"[{rest}]")
            if len(parts) == 1:
                return name, True
            return " ".join(parts), False
        if head.kind is not NumberFunction:
            raise _no_definition(
                head, f" as a function: only a call of an expression of kind "
                f"{NumberFunction!r} is printed"
            )
        (argument,) = e.args
        return f"Nary.apply {self.argument(head)} {self.argument(argument)}", False


def to_lean(e):
    """The Lean term for the expression ``e``, as a string.

    Raises ``ValueError`` if a part of ``e`` has no Lean definition.
    """
    return _Printer().print(e)[0]


def to_lean_example(e):
    """A line that Lean can check on its own: ``noncomputable example``,
    the free symbols of ``e`` as variables with their types, the type of
    ``e`` and its term.

    The variables are grouped by type (numbers, then propositions, then
    functions), each group in the order the symbols first appear in ``e``.
    """
    printer = _Printer()
    term = printer.print(e)[0]
    if e.kind not in _RESULT_TYPES:
        raise _no_definition(e, f": the kind {e.kind!r} has no Lean type")
    binders = []
    for kind, lean_type in _VARIABLE_TYPES.items():
        names = [_identifier(s.name) for s in printer.free.values() if s.kind is kind]
        if names:
            binders.append(f"({' '.join(names)} : {lean_type})")
    # The definitions in lean/ are noncomputable, and without the keyword
    # Lean tries to compile the example and fails.
    return " ".join(
        ["noncomputable example", *binders, ":", _RESULT_TYPES[e.kind], ":=", term]
    )

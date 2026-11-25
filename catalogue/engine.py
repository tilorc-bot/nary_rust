"""Running a catalogue entry through today's engine.

``reaches(entry)`` rewrites ``entry.input`` with ``nary.rewriting.rewrite``
and ``nary.arithmetic_rules.rules`` and says whether the result is
``entry.expected``.

Assumptions: ``known(c)`` is true exactly when ``c`` is one of the entry's
conditions (one per SymPy assumption, see ``catalogue.entry``) or ``true``.
Nothing is derived from them: knowing ``Gt(x, 0)`` does not make
``Ne(x, 0)`` known. Deriving facts is the machinery tagged
``assumptions``.

"Is ``expected``": main has no canonical argument order, so the result
and ``expected`` are compared after flattening every function recorded as
``flat`` and sorting the arguments of every function recorded as
``unordered`` (today ``Add`` and ``Mul``). Both facts are proved in Lean, so
this comparison never calls two expressions with different values the same.
Whether a catalogue should ask for more (an exact form) is one of the
questions in ``catalogue.mismatches``.
"""

from nary.arithmetic_rules import rules as RULES
from nary.rewriting import rewrite
from nary.rules import is_flat, is_unordered
from nary.logic import true

__all__ = ["RULES", "normal", "reaches", "result_of", "same_modulo_order"]


def result_of(entry, rules=RULES):
    """``entry.input`` rewritten with ``rules``, knowing only the entry's
    conditions."""
    conditions = entry.conditions
    return rewrite(entry.input, rules, known=lambda c: c == true or c in conditions)


def _declared(head):
    return head is not None and head.is_constant and head.kind.inputs is not None


def normal(e):
    """``e`` with flat functions flattened and the arguments of unordered
    functions sorted, all the way down. Lambdas are left alone."""
    if e.head is None:
        return e
    head = normal(e.head)
    args = [normal(a) for a in e.args]
    if _declared(head) and is_flat(head):
        merged = []
        for a in args:
            merged.extend(a.args if a.head == head else (a,))
        args = merged
    if _declared(head) and is_unordered(head):
        args.sort(key=repr)
    return head(*args)


def same_modulo_order(a, b):
    """Whether ``a`` and ``b`` are the same up to flattening and argument
    order of the functions recorded as ``flat`` and ``unordered``."""
    return normal(a) == normal(b)


def reaches(entry, rules=RULES):
    """Whether today's engine turns ``entry.input`` into ``entry.expected``."""
    return same_modulo_order(result_of(entry, rules), entry.expected)

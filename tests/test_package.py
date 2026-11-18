"""The package: what ``import nary`` gives, and how its modules plug in."""

import importlib

import nary
from nary import functions, relational


def test_import_nary_exposes_the_core_and_the_declarations():
    assert set(nary.__all__) >= {
        "Expr", "FunctionKind", "Kind", "KindFamily", "Symbol",
        "declare_constant", "declare_function", "declare_kind", "declare_kind_family",
        "set_operator", "Lambda", "is_lambda",
        "NumberKind", "BoolKind", "Add", "Mul", "Pow", "sin", "Lt", "Eq", "pi", "E", "I",
    }
    for name in nary.__all__:
        assert hasattr(nary, name), name
    assert not any(hasattr(nary, name) for name in ("function", "kind", "kind_family"))
    assert nary.Expr is nary._core.Expr
    assert nary.Lt is relational.Lt
    assert nary.Lambda is functions.Lambda and not hasattr(nary._core, "Lambda")
    assert not hasattr(nary, "Bool")


def test_a_name_in_a_module_all_is_reexported():
    # Re-running nary/__init__.py does not re-run the modules it imports, so
    # nothing is declared twice.
    relational.Extra = Extra = object()
    relational.__all__.append("Extra")
    try:
        importlib.reload(nary)
        assert nary.Extra is Extra
        assert "Extra" in nary.__all__
    finally:
        relational.__all__.remove("Extra")
        del relational.Extra
        importlib.reload(nary)
        # A reload keeps the names it does not set again.
        vars(nary).pop("Extra", None)
    assert "Extra" not in nary.__all__

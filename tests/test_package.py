"""The package layout: what is importable and from where."""

import importlib

import nary


def test_all_names_exist():
    for name in nary.__all__:
        assert hasattr(nary, name), name


def test_compiled_module_is_private_submodule():
    core = importlib.import_module("nary._core")
    assert nary.Expr is core.Expr
    assert nary.kind is core.kind
    assert nary.function is core.function


def test_declaration_modules():
    for module in (
        "arithmetic", "calculus", "elementary", "kinds", "logic", "matrices",
        "piecewise", "relational", "sets",
    ):
        importlib.import_module(f"nary.{module}")


def test_classes_report_the_package_as_their_module():
    assert nary.Expr.__module__ == "nary"
    assert nary.Kind.__module__ == "nary"
    assert nary.Function.__module__ == "nary"
    assert nary.KindFamily.__module__ == "nary"


def test_rust_declares_no_particular_kind_or_function():
    core = importlib.import_module("nary._core")
    public = {name for name in dir(core) if not name.startswith("_")}
    assert public == {
        "Expr", "Function", "Integer", "Kind", "KindFamily", "Symbol",
        "function", "kind", "kind_family", "set_integer_kind", "set_operator",
    }


def test_the_kinds_are_declared_in_python():
    kinds = importlib.import_module("nary.kinds")
    for name, declared_with in (
        ("NumberKind", nary.Kind),
        ("BoolKind", nary.Kind),
        ("SetKind", nary.KindFamily),
        ("MatrixKind", nary.KindFamily),
    ):
        declared = getattr(kinds, name)
        assert type(declared) is declared_with
        assert getattr(nary, name) is declared

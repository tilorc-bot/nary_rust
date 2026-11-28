import ast
import inspect
import types
from pathlib import Path

from nary import _core

STUB = ast.parse(Path(_core.__file__).with_name("_core.pyi").read_text(encoding="utf-8"))
NOT_COMPARED = {"__doc__", "__module__", "__new__"}
STUB_NAMES = {"__getattribute__": "__getattr__"}


def defined(body):
    names = {}
    for node in body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.setdefault(node.name, []).append(node)
        elif isinstance(node, ast.AnnAssign):
            names[node.target.id] = [node]
    return names


def stub_parameters(function, skip=0):
    a = function.args
    positional = a.posonlyargs + a.args
    required = len(positional) - len(a.defaults)
    parameters = [(arg.arg, "positional", i >= required) for i, arg in enumerate(positional)]
    if a.vararg:
        parameters.append((a.vararg.arg, "many", False))
    parameters += [
        (arg.arg, "keyword", default is not None)
        for arg, default in zip(a.kwonlyargs, a.kw_defaults)
    ]
    return parameters[skip:]


def runtime_parameters(function):
    kinds = {
        inspect.Parameter.POSITIONAL_OR_KEYWORD: "positional",
        inspect.Parameter.VAR_POSITIONAL: "many",
        inspect.Parameter.KEYWORD_ONLY: "keyword",
    }
    return [
        (p.name, kinds[p.kind], p.default is not p.empty)
        for p in inspect.signature(function).parameters.values()
    ]


def test_the_stub_defines_the_public_names_of_the_module():
    public = {name for name in vars(_core) if not name.startswith("_")}
    assert set(defined(STUB.body)) == public == set(_core.__all__)


def test_each_stubbed_class_has_the_attributes_of_the_class():
    classes = {n: d[0] for n, d in defined(STUB.body).items() if isinstance(d[0], ast.ClassDef)}
    assert set(classes) == {n for n in _core.__all__ if isinstance(getattr(_core, n), type)}
    for name, stub in classes.items():
        runtime = {
            STUB_NAMES.get(attribute, attribute): value
            for attribute, value in vars(getattr(_core, name)).items()
            if attribute not in NOT_COMPARED
        }
        stubbed = {a: d for a, d in defined(stub.body).items() if a not in NOT_COMPARED}
        assert set(stubbed) == set(runtime), name
        for attribute, (node,) in stubbed.items():
            is_property = any(ast.unparse(d) == "property" for d in node.decorator_list)
            getter = isinstance(runtime[attribute], types.GetSetDescriptorType)
            assert is_property == getter, (name, attribute)


def test_each_stubbed_function_has_the_parameters_of_the_function():
    for name, definitions in defined(STUB.body).items():
        for node in definitions:
            if isinstance(node, ast.FunctionDef):
                assert stub_parameters(node) == runtime_parameters(getattr(_core, name)), name
    (new,) = defined(defined(STUB.body)["Symbol"][0].body)["__new__"]
    assert stub_parameters(new, skip=1) == runtime_parameters(_core.Symbol)

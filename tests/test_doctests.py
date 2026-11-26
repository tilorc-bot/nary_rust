import doctest
import importlib
import pkgutil

import nary


def test_docstring_examples_of_every_module():
    modules = [
        importlib.import_module(f"nary.{info.name}") for info in pkgutil.iter_modules(nary.__path__)
    ]
    attempted = 0
    for module in modules:
        result = doctest.testmod(module, optionflags=doctest.ELLIPSIS)
        assert result.failed == 0, module.__name__
        attempted += result.attempted
    assert attempted > 0

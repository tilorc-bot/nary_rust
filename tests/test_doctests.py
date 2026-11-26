import doctest
import importlib
import pkgutil

import nary


def test_docstring_examples_of_every_module():
    modules = [
        importlib.import_module(info.name) for info in pkgutil.walk_packages(nary.__path__, "nary.")
    ]
    attempted = 0
    for module in modules:
        result = doctest.testmod(module, optionflags=doctest.ELLIPSIS)
        assert result.failed == 0, module.__name__
        attempted += result.attempted
    assert attempted > 0

"""A pytest plugin that records the outermost refine and trigsimp calls of satsimp's tests.

    >>> import sympy
    >>> x = sympy.Symbol("x")
    >>> line = _line("trigsimp", (sympy.sin(x) / sympy.cos(x),), {}, sympy.tan(x))
    >>> load([line])
    [('trigsimp', sin(x)/cos(x), True, tan(x))]
"""

import json
import os
import subprocess
import sys

import sympy
from sympy import Q

__all__ = ["load", "record"]

_depth = [0]


def _line(method, args, kwargs, result):
    assumptions = args[1] if len(args) > 1 else kwargs.get("assumptions", True)
    return json.dumps([method, sympy.srepr(args[0]), sympy.srepr(sympy.sympify(assumptions)),
                       sympy.srepr(result)])


def _recording(method, function, path):
    def wrapper(*args, **kwargs):
        _depth[0] += 1
        try:
            result = function(*args, **kwargs)
        finally:
            _depth[0] -= 1
        if _depth[0] == 0 and not kwargs.get("strict"):
            try:
                with open(path, "a") as file:
                    file.write(_line(method, args, kwargs, result) + "\n")
            except (TypeError, ValueError, sympy.SympifyError):
                pass
        return result

    return wrapper


def pytest_configure(config):
    path = os.environ.get("NARY_SATSIMP_RECORD")
    if not path:
        return
    import satsimp
    from satsimp.methods import refine, trigsimp

    refine.refine = satsimp.refine = _recording("refine", refine.refine, path)
    trigsimp.trigsimp = satsimp.trigsimp = _recording("trigsimp", trigsimp.trigsimp, path)


def record(checkout, trees, path):
    for tree in trees:
        env = {**os.environ, "NARY_SATSIMP_RECORD": str(path), "PYTHONHASHSEED": "0"}
        subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", __name__,
                        "-p", "no:cacheprovider", *tree.split()], cwd=checkout, env=env,
                       stdout=subprocess.DEVNULL, check=False)


def load(lines):
    namespace = {**vars(sympy), "Q": Q}
    cases = {}
    for line in lines:
        method, *parts = json.loads(line)
        try:
            case = (method, *(eval(part, namespace) for part in parts))
        except Exception:
            continue
        if all(isinstance(part, sympy.Basic) for part in case[1:]):
            cases.setdefault(case[:3], case)
    return list(cases.values())

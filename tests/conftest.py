import random

import pytest


def pytest_addoption(parser):
    parser.addoption("--fuzz-seed", type=int, default=None)
    parser.addoption("--fuzz-examples", type=int, default=100)


def pytest_configure(config):
    if config.option.fuzz_seed is None:
        config.option.fuzz_seed = random.SystemRandom().randrange(2**32)


def pytest_report_header(config):
    return f"fuzz seed: {config.option.fuzz_seed}, examples: {config.option.fuzz_examples}"


def subexpressions(e):
    yield e
    if not e.is_atom:
        for arg in e.args:
            yield from subexpressions(arg)


def smaller(e):
    if e.is_atom:
        return
    seen = set()
    for arg in e.args:
        if arg.kind == e.kind and arg not in seen:
            seen.add(arg)
            yield arg
    for i, arg in enumerate(e.args):
        for new in [None, *smaller(arg)] if len(e.args) > 2 else smaller(arg):
            args = e.args[:i] + e.args[i + 1:] if new is None else e.args[:i] + (new,) + e.args[i + 1:]
            try:
                yield e.head(*args)
            except (TypeError, ValueError):
                pass


class Fuzz:
    def __init__(self, seed, examples, nodeid):
        self.seed, self.examples, self.nodeid = seed, examples, nodeid
        self.random = random.Random(f"{seed} {nodeid}")

    def command(self):
        return (
            f"PYTHONPATH=python python -m pytest -m fuzz --fuzz-seed={self.seed} "
            f"--fuzz-examples={self.examples} '{self.nodeid}'"
        )

    def fails(self, e, holds):
        try:
            outcome = holds(e, random.Random(f"{self.seed} {e!r}"))
        except Exception as error:
            return f"raises {error!r}"
        return None if outcome is True else str(outcome)

    def shrunk(self, e, holds):
        for _ in range(1000):
            for candidate in smaller(e):
                if self.fails(candidate, holds):
                    e = candidate
                    break
            else:
                return e
        return e

    def check(self, generate, holds):
        for _ in range(self.examples):
            e = generate(self.random)
            if self.fails(e, holds):
                small = self.shrunk(e, holds)
                pytest.fail(
                    f"fails for {small!r}, shrunk from {e!r}: {self.fails(small, holds)}\n"
                    f"seed {self.seed}, rerun with: {self.command()}",
                    pytrace=False,
                )


@pytest.fixture
def fuzz(request):
    config = request.config
    return Fuzz(config.option.fuzz_seed, config.option.fuzz_examples, request.node.nodeid)

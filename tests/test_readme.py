"""The examples in the README are run as doctests."""

import doctest
from pathlib import Path

import pytest

README = Path(__file__).resolve().parent.parent / "README.md"


@pytest.mark.skipif(not README.exists(), reason="README.md is not next to the tests")
def test_readme_examples():
    result = doctest.testfile(
        str(README), module_relative=False, optionflags=doctest.ELLIPSIS
    )
    assert result.attempted > 0
    assert result.failed == 0

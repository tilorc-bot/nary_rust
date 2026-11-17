import nary as nr
import pytest


@pytest.fixture
def xyz():
    return tuple(nr.NumberKind(name) for name in "xyz")

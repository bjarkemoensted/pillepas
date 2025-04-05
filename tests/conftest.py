import pathlib
import pytest


_here = pathlib.Path(__file__).parent


@pytest.fixture(scope="session")
def data():
    pass

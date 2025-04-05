import json
import pathlib
import pytest
import random
import string

from pillepas.data_tools import crypto
from pillepas import data_tools

_here = pathlib.Path(__file__).parent


@pytest.fixture(scope="session")
def data():
    res = data_tools.load_example_data()
    return res


@pytest.fixture(scope="session")
def data_path(tmp_path_factory, data):
    path = tmp_path_factory.mktemp("data") / "data.json"
    data_tools.save_data(data=data, path=path, crypt=None)
    return path


@pytest.fixture(scope="session")
def crypt_good():
    crypt = crypto.Crypt(password='shhhhhhhh')
    return crypt


@pytest.fixture(scope="session")
def crypt_bad():
    crypt = crypto.Crypt(password='hunter2')
    return crypt


@pytest.fixture(scope="session")
def data_path_encrypted(data, tmp_path_factory, crypt_good):
    path = tmp_path_factory.mktemp("data") / "data_encrypted.json"
    data_tools.save_data(data=data, path=path, crypt=crypt_good)
    return path

import pathlib
import pytest

from pillepas.crypto import Cryptor

_here = pathlib.Path(__file__).parent


@pytest.fixture(scope="session")
def pass1():
    return "iamapassword"


@pytest.fixture(scope="session")
def pass2():
    return "hunter2"


@pytest.fixture(scope="session")
def cryptor1(pass1):
    return Cryptor(pass1)


@pytest.fixture(scope="session")
def cryptor2(pass2):
    return Cryptor(pass2)


# @pytest.fixture(scope="class")
# def wrapped_fixtures(request, pass1, cryptor1, pass2, cryptor2):
#     request.cls.client = client
#     request.cls.client = client_1

# @pytest.mark.usefixtures("wrapped_fixtures")
# class TestStaticPages(unittest.TestCase):

#     @classmethod
#     def setUpClass(self):
#         self.value = "ABC"

#     def test_base_route(self):
#         response = self.client
#         assert response  == 'FLASK_ENV'
#         assert self.client_1  == 'FLASK_ENV_1'
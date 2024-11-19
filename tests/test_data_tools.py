from pillepas import data_tools


def test_tautology():
    assert True


def test_example_data(data):
    assert isinstance(data, dict)


def test_read(data_path):
    d = data_tools.load_data(path=data_path)
    assert isinstance(d, dict)


def test_password(data_path_encrypted, crypt_good, crypt_bad):
    assert data_tools.password_correct(path=data_path_encrypted, crypt=crypt_good)
    assert not data_tools.password_correct(path=data_path_encrypted, crypt=crypt_bad)


def test_is_encrypted(data_path_encrypted, data_path):
    assert data_tools.is_encrypted(path=data_path_encrypted)
    assert not data_tools.is_encrypted(path=data_path)

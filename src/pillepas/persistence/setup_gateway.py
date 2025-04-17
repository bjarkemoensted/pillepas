from pathlib import Path

from pillepas import config
from pillepas.crypto import CryptoError, Cryptor
from pillepas.persistence.gateway import Gateway
from pillepas.persistence.data import FieldContainer
from pillepas.user_inputs import prompt_password


fields = FieldContainer.create()


def _create(path: Path):
    if not path.exists():
        password = prompt_password(f"Enter password (leave blank to not encrypt): ", confirm=True)
        c = Cryptor(password)
        return Gateway(path=path, cryptor=c)

    c = Cryptor(password=None)
    prompt = f"{path} is encrypted - enter password: "

    while True:
        try:
            res = Gateway(path=path, cryptor=c)
            return res
        except CryptoError:
            pass

        password = prompt_password(prompt=prompt)
        c = Cryptor(password=password)
        prompt = f"Invalid password, try again: "
    #


def setup_gateway(path: Path=None) -> Gateway:
    if path is None:
        path = config.determine_data_file()

    gateway = _create(path=path)
    missing_keys = filter(lambda k: k not in gateway, (field.key for field in fields))
    
    d = {k: None for k in missing_keys}
    gateway.set_values(**d)
    
    return gateway


if __name__ == '__main__':
    g = setup_gateway()

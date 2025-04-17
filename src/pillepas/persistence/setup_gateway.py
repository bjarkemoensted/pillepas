from pathlib import Path

from pillepas.crypto import CryptoError, Cryptor
from pillepas.persistence.gateway import Gateway
from pillepas.persistence.data import form_fields
from pillepas.user_inputs import prompt_password


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




def setup_gateway(path: Path) -> Gateway:
    gateway = _create(path=path)
    missing = filter(lambda k: k not in gateway, (field.key for field in form_fields))
    
    d = {k: None for k in missing}
    gateway.set_values(**d)
    
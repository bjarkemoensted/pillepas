from pathlib import Path

from pillepas import config
from pillepas.crypto import Cryptor, CryptoError
from pillepas.persistence.gateway import Gateway
from pillepas.cli import user_inputs


def make_cryptor() -> Cryptor:
    """Prompts for a password, interpreting empty string as no password"""
    
    password = user_inputs.prompt_password(f"Enter password (leave blank to not encrypt): ", confirm=True)
    res = Cryptor(password)
    return res


def make_gateway() -> Gateway:
    """Creates a gateway. Prompts for new password if no data is stored. Otherwise prompts if data is encrypted."""
    path = config.get_data_file()
    
    # If no data is stored yet, prompt for password, accepting blank string as no password
    if not path.exists():
        c = make_cryptor()
        return Gateway(cryptor=c)

    # Otherwise, try reading data. If encrypted, (re)prompt for password until it works
    c = Cryptor(password=None)
    prompt = f"Data in {path} is encrypted - enter password: "

    while True:
        try:
            res = Gateway(cryptor=c)
            return res
        except CryptoError:
            pass

        password = user_inputs.prompt_password(prompt=prompt)
        c = Cryptor(password=password)
        prompt = f"Invalid password, try again: "
    #


def change_data_dir(gateway: Gateway, new_dir: Path):
    """Wrapping the steps for changing data dir into a single method."""

    config.set_data_dir(new_dir)
    gateway.move_data(new_dir)
from getpass import getpass
from nacl.exceptions import CryptoError
from pathlib import Path

from pillepas import config
from pillepas.persistence.crypto import Cryptor
from pillepas.persistence.file_handlers import FileHandler, EncryptionFileHandler


ENCRYPTED_EXT = ".encrypted"


def _encrypted_path(path: Path) -> Path:
    """Returns the input path, but with a suffix indicated that the file is encrypted"""
    res = path.with_suffix(path.suffix+ENCRYPTED_EXT)
    return res


def _prompt_password(prompt: str=None, confirm=False) -> str:
    """Prompts for a password to use for encryption.
    prompt: optional string for prompting for the password. Defaults to the getpass default.
    confirm: Optional bool (default: False) indicating whether the user must confirm their password."""

    kwargs = dict() if prompt is None else dict(prompt=prompt)
    password = getpass(**kwargs)
    if confirm:
        if password and password != getpass("Confirm password: "):
            raise RuntimeError("First and second attempts differed")
        #
    
    return password


class Gateway:
    """Intended to handle reading/writing of data, along with any preprocessing.
    Uses the builtin get/set/del magic methods for items, so stuff like
    my_gateway["foo"] = "bar"
    adds value "bar" at key "foo", then updates the gateway's file."""
    
    def __init__(self, path: Path, cryptor: Cryptor=None):
        """path (pathlib.Path) - the path where data are stored
        cryptor (Cryptor, optional) - Cryptor instance which can handle encrypting+decrypting"""

        self._path = path
        self._cryptor = cryptor
        self._filehandler = FileHandler() if self._cryptor is None else EncryptionFileHandler(cryptor=self._cryptor)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self.read()
    
    def change_cryptor(self, cryptor: Cryptor=None) -> None:
        """Changes the gateway's Cryptor instance.
        The new cryptor can be a different cryptor instance, e.g. when changing a password, or None,
        if disabling encryption."""
        
        if not isinstance(cryptor, Cryptor):
            raise TypeError
        self.wipe()
        self._cryptor = cryptor
        self.save()
    
    @property
    def path(self) -> Path:
        """Path for the stored data. Automatically adds a suffix to denote an encrypted file"""
        
        res = _encrypted_path(self._path) if self._cryptor else self._path
        return res
    
    def read(self) -> dict:
        """Reads data from disk"""
        try:
            res = self._filehandler.read(self.path)
        except FileNotFoundError:
            res = dict()
        return res

    def save(self) -> None:
        """Saves the stored data to disk"""
        self._filehandler.write(self._data, self.path)
    
    def wipe(self):
        """Remove data from disk"""
        self.path.unlink(missing_ok=True)
    
    def set_values(self, **kwargs):
        """Set a bunch of key-value pairs, then save"""
        for k, v in kwargs.items():
            self._data[k] = v
        
        self.save()
    
    def __getitem__(self, key):
        res = self._data[key]
        return res
    
    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()
    
    def __delitem__(self, key):
        del self._data[key]
        self.save()
    
    def __str__(self) -> str:
        data_str = f"{', '.join(f'{k}={repr(v)}' for k, v in self._data.items())}"
        res = f"{self.__class__.__name__}({data_str})"
        return res
    #


def setup_gateway(path: Path, max_password_retries: int|None=3) -> Gateway:
    """Helper method for interactively setting up a gateway instance for a given path."""
    
    plaintext, enc = (p.exists() for p in (path, _encrypted_path(path)))
    
    # If we find a plaintext datafile
    if plaintext:
        # Throw error if we find both plaintext + encrypted, which shouldn't happen
        if enc:
            raise RuntimeError(f"Found both plaintext and encrypted data files for {path}. This should not happen.")
        
        # Make unencrypted gateway
        return Gateway(path=path)
    elif not any(plaintext, enc):
        # If no datafile is found, prompt for optional password
        password = _prompt_password(prompt="Enter password (leave blank for no encryption): ", confirm=True)
        cryptor = Cryptor(password=password)
        return Gateway(path=path, cryptor=cryptor)
    
    # If there's an encrypted file, repeatedly prompt for password
    if max_password_retries is None:
        max_password_retries = float("inf")
    
    prompt = None  # Use default prompt the first time
    n_attempts = 0
    while n_attempts < max_password_retries:
        password = _prompt_password(prompt=prompt)
        cryptor = Cryptor(password=password)
        try:
            return Gateway(path=path, cryptor=cryptor)
        except CryptoError:
            pass
        
        n_attempts += 1
        prompt = "Invalid password, try again: "
    #


if __name__ == '__main__':
    pass

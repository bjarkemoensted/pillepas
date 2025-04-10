from getpass import getpass
import json
from nacl.exceptions import CryptoError
from pathlib import Path
from typing import Iterable

from pillepas import config
from pillepas.persistence.crypto import Crypt


class Gateway:
    """Intended to handle reading/writing of data, along with any preprocessing"""
    
    encrypted_ext = ".encrypted"
    
    def __init__(self, path: Path, defaults: dict=None, sensitive_keys: Iterable=None):
        """path (pathlib.Path): the path where data are stored
        defaults: dict containing default values (defaults to empty dict)
        sensitive_keys: Iterable of sensitive keys which should not be stored unless using encryption."""

        self._path = path
        self._defaults = defaults if defaults is not None else dict()
        self._sensitive_keys = set([]) if sensitive_keys is None else set(sensitive_keys)
        self._data = None
        self._path_enc = self.path.with_suffix(self.encrypted_ext)
        self.use_encryption = None
        self._crypt = None
    
    def setup(self):
        """Sets up the gateway. Looks for existing data file and determines whether encryption is used."""
        
        if self._path.exists():
            if self._path_enc.exists():
                raise RuntimeError(f"Found plaintext and encrypted file. This should not happen.")
            # If unencrypted, toggle encryption off and read the existing data
            self._toggle_encryption_off()
            self.read()
        elif self._path_enc.exists():
            # If encrypted data are found on disk, prompt for password and read
            prompt = None
            while True:
                # Keep prompting for password until read is succesful
                self.prompt_password(prompt=prompt)
                try:
                    self.read()
                    return
                except CryptoError:
                    prompt = "Invalid password, try again: "
                #
            #
        else:
            # For first-time setup, ask user to re-enter password
            self.prompt_password(prompt="Enter password (leave blank to store data unencrypted)", confirm=True)
            self._data = self._defaults
            self.save()
        #
    
    @property
    def _read(self):
        method = self.path.read_bytes if self._use_encryption else self.path.read_text
        return method
    
    @property
    def _save(self):
        method = self.path.write_bytes if self._use_encryption else self.path.write_text
        return method
    
    def read(self) -> None:
        """Reads data from disk"""
        raw = self._read()
        json_ = self._crypt.decrypt(raw) if self._use_encryption else raw

        d = json.loads(json_)
        self._data = d

    def save(self) -> None:
        """Saves the stored data to disk"""
        d = {k: v for k, v in self._data.items() if self._use_encryption or k not in self._sensitive_keys}
        json_ = json.dumps(d, sort_keys=True, indent=2)
        
        s = self._crypt.encrypt(json_) if self._use_encryption else json_
        self._save(s)
    
    
    @property
    def path(self) -> Path:
        """Path for the stored data. Automatically adds a suffix to denote an encrypted file"""
        match self.use_encryption:
            case True:
                return self._path
            case False:
                return self._path_enc
            case _:
                raise RuntimeError(f"Must specify encryption!")
            #
        #
    
    def _toggle_encryption_on(self, password: str):
        """Sets encryption to on"""
        self._crypt = Crypt(password=password)
        self.use_encryption = True
    
    def _toggle_encryption_off(self):
        """Sets encryption to off"""
        self._crypt = None
        self.use_encryption = False
    
    def prompt_password(self, prompt: str=None, confirm=False):
        """Prompts for a password to use for encryption.
        prompt: optional string for prompting for the password. Defaults to the getpass default.
        confirm: Optional bool (default: False) indicating whether the user must confirm their password."""

        kwargs = dict() if prompt is None else dict(prompt=prompt)
        password = getpass(**kwargs)
        if confirm:
            if password != getpass("Confirm password: "):
                raise RuntimeError("First and second attempts differed")
            #
        self._toggle_encryption(password=password)
    
    def wipe(self):
        """Remove data from disk"""
        self._path_enc.unlink()
        self._path.unlink()


if __name__ == '__main__':
    g = Gateway(config.CONFIG_FILE)
    print(g.file_exists())
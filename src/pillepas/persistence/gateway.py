import json
from pathlib import Path

from pillepas import config
from pillepas.crypto import Cryptor
from pillepas.user_inputs import prompt_password


_passthrough = Cryptor(password=None)


class CorruptedError(Exception):
    pass


class Gateway:
    """Intended to handle reading/writing of data, along with any preprocessing.
    Uses the builtin get/set/del magic methods for items, so stuff like
    my_gateway["foo"] = "bar"
    adds value "bar" at key "foo", then updates the gateway's file."""
    
    def __init__(self, path: Path, cryptor: Cryptor=None):
        """path (pathlib.Path) - the path where data are stored
        cryptor (Cryptor, optional) - Cryptor instance which can handle encrypting+decrypting"""
            
        self.path = path
        self._cryptor = _passthrough if cryptor is None else cryptor
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = None
        
        try:
            self._data = self.read()
        except FileNotFoundError:
            self._data = dict()
            self.save()

    
    def change_cryptor(self, cryptor: Cryptor=None) -> None:
        """Changes the gateway's Cryptor instance.
        The new cryptor can be a different cryptor instance, e.g. when changing a password, or None,
        if disabling encryption."""
        
        if cryptor is None:
            cryptor = _passthrough

        if not isinstance(cryptor, Cryptor):
            raise TypeError
        
        # Set the new cryptor and save data
        self.check_corrupt()
        self._last_hash = None
        self._cryptor = cryptor
        self.save()
    
    def move_data(self, new_path: Path):
        new_path.parent.mkdir(parents=True, exist_ok=True)
        self.path.rename(new_path)
        self.path = new_path
    
    def _json(self) -> str:
        s = json.dumps(self._data, sort_keys=True, indent=2)
        return s
    
    @property
    def file_hash(self):
        raw = self.path.read_bytes()
        s = self._cryptor.decrypt(raw)
        return hash(s)
    
    @property
    def data_hash(self):
        return hash(self._json())
    
    def check_corrupt(self):
        if self._last_hash and self._last_hash != self.file_hash:
            raise CorruptedError
        #

    def read(self) -> dict:
        """Reads data from disk"""
        
        raw = self.path.read_bytes()
        s = self._cryptor.decrypt(raw)
        self._last_hash = hash(s)
        res = json.loads(s)
        
        return res

    def save(self) -> None:
        """Saves the stored data to disk"""
        
        if self._last_hash and self._last_hash != self.file_hash:
            raise CorruptedError
        
        s = self._json()
        self._last_hash = hash(s)
        raw = self._cryptor.encrypt(s)
        self.path.write_bytes(raw)
    
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
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()
    
    def __delitem__(self, key):
        del self._data[key]
        self.save()
    
    def __contains__(self, item):
        return item in self._data
    
    def __str__(self) -> str:
        data_str = f"{', '.join(f'{k}={repr(v)}' for k, v in self._data.items())}"
        res = f"{self.__class__.__name__}({data_str})"
        return res
    #


if __name__ == '__main__':
    import tempfile    
    tempdir = tempfile.TemporaryDirectory()
    
    # Make the path instance, add filename if provided, otherwise reference the folder
    path = Path(tempdir.name) / "data.stuff"

    
    g = Gateway(path=path, cryptor=Cryptor("1"))
    other_cryptor = cryptor=Cryptor("2")
    

    g.change_cryptor(other_cryptor)
    

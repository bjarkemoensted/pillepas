import json
from pathlib import Path
from typing import Any

from pillepas.persistence.crypto import Cryptor


class FileHandler:
    """File handler for reading/writing from/to a path object.
    Just making this to make it simpler to abstract away any steps involving en/de-cryption,
    by passing data through hook methods immediately before saving and immediately after reading."""

    # Read/write plaintext for normal files
    read_method = "read_text"
    write_method = "write_text"

    def read_hook(self, raw: str) -> str:
        """Passthrough for normal reading"""
        return raw

    def read(self, path: Path) -> Any:
        raw = getattr(path, self.read_method)()
        s = self.read_hook(raw)
        res = json.loads(s)
        return res
    
    def write_hook(self, s: str) -> str:
        """Passthrough for normal writing"""
        return s
    
    def write(self, data: Any, path: Path):
        s = json.dumps(data, sort_keys=True, indent=2)
        raw = self.write_hook(s)
        getattr(path, self.write_method)(raw)
    #


class EncryptionFileHandler(FileHandler):
    """Handler for using a Crypt instance to encrypt/decrypt before writing/reading."""

    # Read/write bytes for encrypted files
    read_method = "read_bytes"
    write_method = "write_bytes"
    
    def __init__(self, cryptor: Cryptor):
        self.cryptor = cryptor
        super().__init__()
    
    def write_hook(self, s: str) -> str:
        """Encrypt immediately before writing"""
        raw = self.cryptor.encrypt(s)
        return raw
    #

    def read_hook(self, raw: bytes) -> str:
        """Decrypt immediately after reading"""
        s = self.cryptor.decrypt(raw)
        return s
    #


if __name__ == '__main__':
    pass

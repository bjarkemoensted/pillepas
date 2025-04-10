from nacl import pwhash, secret


def _salt():
    """Random salt value for this module"""
    salt = b'\xff\xb5L6\x87\\\x88\xbf\xf4\xcaw\xfau\xda\xbd\xd5'
    return salt


def _box_from_password(password: bytes) -> secret.SecretBox:
    """Generates a 'secret box' for encrypting/decrypting data."""

    kdf = pwhash.argon2i.kdf
    salt = _salt()
    key = kdf(secret.SecretBox.KEY_SIZE, password, salt=salt)
    box = secret.SecretBox(key)
    return box


def _encode(s: str, encoding: str) -> bytes:
    res = bytes(s.encode(encoding))
    return res
    
def _decode(b: bytes, encoding: str) -> str:
    res = b.decode(encoding)
    return res


class Crypt:
    """Helper class for taking care of handling encryption/decryption given a password"""
    
    encoding = "utf-8"
    
    def __init__(self, password: str):
        password_bytes = _encode(password, self.encoding)
        self._box = _box_from_password(password=password_bytes)

    def encrypt(self, s: str):
        b = _encode(s, self.encoding)
        res = self._box.encrypt(b)
        return res

    def decrypt(self, b: bytes):
        res_bytes = self._box.decrypt(b)
        res = _decode(res_bytes, self.encoding)
        return res


if __name__ == '__main__':
    import time
    now = time.time()
    crypt = Crypt("hest")
    print(f"Ran in {time.time() - now:.2f}s.")
    ssh = crypt.encrypt("hmmmm")
    hmm = crypt.decrypt(ssh)
    print(hmm)
    
    crypt2 = Crypt("hest2")
    print(crypt2.decrypt(ssh))
from nacl import pwhash, secret


def _salt():
    salt = b'\xff\xb5L6\x87\\\x88\xbf\xf4\xcaw\xfau\xda\xbd\xd5'
    return salt


def _box_from_password(password: bytes):
    kdf = pwhash.argon2i.kdf
    salt = _salt()
    key = kdf(secret.SecretBox.KEY_SIZE, password, salt=salt)
    box = secret.SecretBox(key)
    return box


class Crypt:
    encoding = "utf-8"
    
    def __init__(self, password: str):
        password_bytes = self._encode(password)
        self._box = _box_from_password(password=password_bytes)

    def _encode(self, s: str) -> bytes:
        res = bytes(s.encode(self.encoding))
        return res
    
    def _decode(self, b: bytes) -> str:
        res = b.decode(self.encoding)
        return res
    
    def encrypt(self, s: str):
        b = self._encode(s=s)
        res = self._box.encrypt(b)
        return res

    def decrypt(self, b: bytes):
        res_bytes = self._box.decrypt(b)
        res = self._decode(res_bytes)
        return res


if __name__ == '__main__':
    import time
    now = time.time()
    crypt = Crypt("hest")
    print(f"Ran in {time.time() - now:.2f}s.")
    ssh = crypt.encrypt("hmmmm")
    hmm = crypt.decrypt(ssh)
    print(hmm)
    
    crypt2 = Crypt("hest")
    print(crypt2.decrypt(ssh))
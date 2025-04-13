from nacl import pwhash, secret
import threading
from concurrent.futures import ProcessPoolExecutor


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


class Cryptor:
    """Helper class for taking care of handling encryption/decryption given a password"""
    
    encoding = "utf-8"
    
    def __init__(self, password: str, parallelize=True):
        """password (str) - the password used to encrypt
        parallelize (bool, default=True) - whether to create the underlying SecretBox instance in a
            separate process. Creating a box takes ~3 seconds, so it's nice to not have to wait if it's
            not immediately needed."""

        self.parallelize = parallelize
        self._box = None
        # private vars for a process pool executor and future object if parallelizing
        self._box_future = None
        self._executor = None
        
        self._setup_box(password=password)
        
    def _setup_box(self, password: str):
        """Sets up the secret box for encryption."""

        password_bytes = _encode(password, self.encoding)
        if self.parallelize:
            # Start the process creating the box. 
            self._executor = ProcessPoolExecutor(
                max_workers=1,  # We just need one worker
                max_tasks_per_child=1  # Limit tasks per child to force 'spawn' process start (fork is deprecated)
            )
            self._box_future = self._executor.submit(_box_from_password, password_bytes)
        else:
            self._box = _box_from_password(password_bytes)
    
    @property
    def box(self) -> secret.SecretBox:
        """Returns the secret box. If not yet available, wait for the worker process to finish."""
        if self._box is None:
            self._box = self._box_future.result()
            self._executor.shutdown()
            #
        
        return self._box

    def encrypt(self, s: str) -> bytes:
        """Encrypts the input string"""
        b = _encode(s, self.encoding)
        res = self.box.encrypt(b)
        return res

    def decrypt(self, b: bytes) -> str:
        """Decrypts the input bytes"""
        res_bytes = self.box.decrypt(b)
        res = _decode(res_bytes, self.encoding)
        return res
    #


if __name__ == '__main__':
    from nacl.exceptions import CryptoError
    parallelize = True
    import time
    
    now = time.time()
    crypt = Cryptor("hest", parallelize=parallelize)
    crypt2 = Cryptor("hest2", parallelize=parallelize)

    print(f"Set up in {time.time() - now:.2f}s.")
    ssh = crypt.encrypt("hmmmm")
    hmm = crypt.decrypt(ssh)
    print(hmm)
    
    try:
        crypt2.decrypt(ssh)
    except CryptoError:
        print("Decrypt w wrong password failed")
    
    print(f"Ran in {time.time() - now:.2f}s.")
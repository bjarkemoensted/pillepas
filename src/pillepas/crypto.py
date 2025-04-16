from nacl import pwhash, secret
from nacl.exceptions import CryptoError
from concurrent.futures import ProcessPoolExecutor


ENCODING = "utf-8"


def _salt():
    """Random salt value for this module"""
    salt = b'\xff\xb5L6\x87\\\x88\xbf\xf4\xcaw\xfau\xda\xbd\xd5'
    return salt


def _encode(s: str) -> bytes:
    res = bytes(s.encode(ENCODING))
    return res


def _decode(b: bytes) -> str:
    res = b.decode(ENCODING)
    return res


def _box_from_password(password: str) -> secret.SecretBox:
    """Generates a 'secret box' for encrypting/decrypting data."""

    password_bytes = _encode(password)
    kdf = pwhash.argon2i.kdf
    salt = _salt()
    key = kdf(secret.SecretBox.KEY_SIZE, password_bytes, salt=salt)
    box = secret.SecretBox(key)
    return box


class pending:
    pass


class Cryptor:
    """Helper class for taking care of handling encryption/decryption given a password"""
    
    def __init__(self, password: str, parallelize=True):
        """password (str) - the password used to encrypt
        parallelize (bool, default=True) - whether to create the underlying SecretBox instance in a
            separate process. Creating a box takes ~3 seconds, so it's nice to not have to wait if it's
            not immediately needed."""

        self.parallelize = parallelize
        self._box = pending
        # private vars for a process pool executor and future object if parallelizing
        self._box_future = None
        self._executor = None
        
        self._setup_box(password=password)
        
    def _setup_box(self, password: str):
        """Sets up the secret box for encryption."""
        
        if not password:
            self._box = None
            return 
        
        if self.parallelize:
            # Start the process creating the box. 
            self._executor = ProcessPoolExecutor(
                max_workers=1,  # We just need one worker
                max_tasks_per_child=1  # Limit tasks per child to force 'spawn' process start (fork is deprecated)
            )
            self._box_future = self._executor.submit(_box_from_password, password)
        else:
            self._box = _box_from_password(password)
    
    @property
    def box(self) -> secret.SecretBox:
        """Returns the secret box. If not yet available, wait for the worker process to finish."""
        if self._box is pending:
            self._box = self._box_future.result()
            self._executor.shutdown()
            #
        
        return self._box

    def encrypt(self, s: str) -> bytes:
        """Encrypts the input string"""
        res = _encode(s)
        if self.box is not None:
            res = self.box.encrypt(res)
            
        return res

    def decrypt(self, b: bytes) -> str:
        """Decrypts the input bytes"""
        
        res = b
        if self.box is not None:
            try:
                res = self.box.decrypt(res)
            except ValueError:
                raise CryptoError
        
        try:
            res = _decode(res)
        except UnicodeDecodeError:
            raise CryptoError
        
        return res
    #


if __name__ == '__main__':
    pass

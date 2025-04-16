import functools
from nacl.exceptions import CryptoError
import random
import string
from unittest import TestCase

from pillepas.crypto import Cryptor


PASS1 = "i am a password"
PASS2 = "hunter2"


@functools.cache
def make_cryptor(password: str) -> Cryptor:
    """Make a cryptor for the input password, and cache it. Used during testing to speed up things,
    do not use with real passwords."""
    return Cryptor(password=password)


class TestCryptor(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pass1 = PASS1
        cls.pass2 = PASS2

        cls.cryptor1 = make_cryptor(cls.pass1)
        cls.cryptor2 = make_cryptor(cls.pass2)
        
        rs = random.Random(42)
        chars = list(string.printable)
        cls.random_strings = tuple(
            ''.join([rs.choice(chars) for _ in range(rs.randint(0, 20))]) for _ in range(100)
        )
        
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()
    
    
    def test_encryption_gives_bytes(self):
        for s in self.random_strings:
            self.assertIsInstance(self.cryptor1.encrypt(s), bytes)
        #
    
    def test_decryption_recovers_string(self):
        for s in self.random_strings:
            c = self.cryptor1.encrypt(s)
            s2 = self.cryptor1.decrypt(c)
            self.assertEqual(s, s2)
        #
    
    def test_using_wrong_password_fails(self):
        s = "abc"
        c = self.cryptor1.encrypt(s)
        f = functools.partial(self.cryptor2.decrypt, c)
        self.assertRaises(CryptoError, f)
    #


if __name__ == '__main__':
    tg = TestCryptor()
    tg.setUp()
    res = tg.test_no_pass()
    tg.tearDown()

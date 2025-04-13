import functools
from nacl.exceptions import CryptoError
from pathlib import Path
import random
import string
import tempfile
from unittest import TestCase

from pillepas.persistence.crypto import Cryptor
from pillepas.persistence.gateway import Gateway


@functools.cache
def _make_cryptor(password: str) -> Cryptor:
    return Cryptor(password=password)


class TestCryptor(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pass1 = "i am a password"
        cls.pass2 = "hunter2"

        cls.cryptor1 = _make_cryptor(cls.pass1)
        cls.cryptor2 = _make_cryptor(cls.pass2)
        
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


class TestGateway(TestCryptor):
    @staticmethod
    def _read_json_directly(gateway: Gateway):
        """Helper method for reading and parsing json from the gateway's file"""
        res = gateway._filehandler.read(gateway.path)
        return res
    
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "data.json"
        self.gateway_nopass = Gateway(path=self.path)
        self.gateway_encrypted = Gateway(path=self.path, cryptor=self.cryptor1)
    
    def tearDown(self):
        self.tempdir.cleanup()
        
    def test_data_save(self):
        """Test that data automatically gets stored"""
        
        d = dict(a=1, b=2)
        self.gateway_nopass.set_values(**d)
        
        d2 = self._read_json_directly(self.gateway_nopass)
        self.assertEqual(d, d2)
        self.gateway_nopass["c"] = 3
        d3 = self._read_json_directly(self.gateway_nopass)
        self.assertEqual(self.gateway_nopass["c"], d3["c"])
    #
    
    def test_read_encrypted_data_fails(self):
        """Test that using a cryptor with the wrong password throws an error when attempting to read encrypted data"""
        
        self.gateway_encrypted["a"] = 42
        self.assertRaises(CryptoError, lambda: Gateway(path=self.path, cryptor=self.cryptor2))
    
    def test_file_cleanup(self):
        g = self.gateway_nopass
        g["a"] = "a"
        self.assertTrue(g.path.exists())
        g.wipe()
        self.assertFalse(g.path.exists())



if __name__ == '__main__':
    tg = TestGateway()
    tg.setUp()
    res = tg.test_no_pass()
    tg.tearDown()
    
from unittest.mock import patch
from unittest import TestCase
from nacl.exceptions import CryptoError
from pathlib import Path
import tempfile

from pillepas import config
from pillepas.persistence.gateway import CorruptedError, Gateway
from pillepas.utils import is_in_home_dir

from tests.test_cryptography import make_cryptor, PASS1, PASS2



class TestGateway(TestCase):
    
    def make_temp_path(self) -> Path:
        """Helper method for creating a path to a temp file/folder, and adding cleanup actions"""
        
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        
        res = Path(tempdir.name)
        
        return res
    
    def make_gateway(self):
        g = Gateway()
        assert not is_in_home_dir(g.path)
        
        return g
    
    def setUp(self):
        self.example_data = dict(a=1, b=2, c=3)
        
        mock_config = self.make_temp_path() / "data_location.txt"
        self.patcher = patch('pillepas.config.CONFIG_PATH', mock_config)
        
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        
        return super().setUp()
    
    def tearDown(self):
        return super().tearDown()
        
    def test_data_save(self):
        """Test that data automatically gets stored"""
        
        g = self.make_gateway()
        g.set_values(**self.example_data)
        
        
        d2 = g.read()
        self.assertEqual(self.example_data, d2)
        
        g["c"] = 3
        d3 = g.read()
        self.assertEqual(g["c"], d3["c"])
    
    def test_file_cleanup(self):
        g = self.make_gateway()
        g["a"] = "a"
        self.assertTrue(g.path.exists())
        g.wipe()
        self.assertFalse(g.path.exists())
    
    def test_corruption_detection(self):
        self.assertAlmostEqual(2, 2)
        g1 = Gateway()
        g2 = Gateway()
        g1["key"] = "value"
        
        self.assertRaises(CorruptedError, lambda: g2.set_values(otherkey="otherval"))
    
    def test_move_data(self):
        g = self.make_gateway()
        g.set_values(**self.example_data)
        old_path = g.path
        
        new_path = self.make_temp_path()
        g.move_data(new_path)
        
        self.assertFalse(old_path.exists())  # Check if the old file is gone
        self.assertTrue(g.path.is_file())  # Check that the new path is a file
        self.assertEqual(g.read(), self.example_data)  # Check that data are unchanged
    
    def test_update_data_file(self):
        
        g = Gateway()
        g.set_values(**self.example_data)
        
        new_path = self.make_temp_path()
        config.set_data_dir(new_path)
        g.move_data(new_path)
        
        g2 = Gateway()
        p2 = g2.path
        self.assertEqual(new_path, p2.parent)
        self.assertEqual(g._data, g2._data)
    
    def test_change_cryptor(self):
        g = self.make_gateway()
        g.set_values(**self.example_data)
        
        other_cryptor = make_cryptor(PASS2)
        g.change_cryptor(other_cryptor)
    #


class TestGatewayEncryption(TestGateway):
    
    def make_gateway(self):
        return Gateway(cryptor=self.c1)
    
    def setUp(self):
        self.c1 = make_cryptor(PASS1)
        self.c2 = make_cryptor(PASS2)
        return super().setUp()
    
    def test_read_encrypted_data_fails(self):
        """Test that using a cryptor with the wrong password throws an error when attempting to read encrypted data"""
        
        g = Gateway(cryptor=self.c1)
        g["a"] = 42
        
        self.assertRaises(CryptoError, lambda: Gateway(cryptor=self.c2))
        self.assertRaises(CryptoError, lambda: Gateway())
    #

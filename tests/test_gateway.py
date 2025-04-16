from unittest.mock import patch
from unittest import TestCase
from nacl.exceptions import CryptoError
from pathlib import Path
import tempfile

from pillepas import config
from pillepas.persistence.gateway import CorruptedError, Gateway

from tests.test_cryptography import make_cryptor, PASS1, PASS2



class TestGateway(TestCase):
    
    def make_temp_path(self, filename: str=None) -> Path:
        """Helper method for creating a path to a temp file/folder, and adding cleanup actions"""
        
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        
        # Make the path instance, add filename if provided, otherwise reference the folder
        res = Path(tempdir.name)
        if filename:
             res = res / filename

        return res
    
    def make_gateway(self):
        return Gateway(path=self.path)
    
    def setUp(self):
        self.example_data = dict(a=1, b=2, c=3)
        
        mock_config = self.make_temp_path(config.CONFIG_PATH.name)
        self.patcher = patch('pillepas.config.CONFIG_PATH', mock_config)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.path = config.determine_data_file()
        
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
        g1 = Gateway(path=self.path)
        g2 = Gateway(path=self.path)
        g1["key"] = "value"
        
        self.assertRaises(CorruptedError, lambda: g2.set_values(otherkey="otherval"))
    
    def test_move_data(self):
        g = self.make_gateway()
        g.set_values(**self.example_data)
        
        new_path = self.make_temp_path(filename=config._data_filename)
        g.move_data(new_path)
        
        # Check if the old file is gone
        self.assertFalse(self.path.exists())
        self.assertEqual(g.read(), self.example_data)
    
    def test_update_data_file(self):
        
        p1 = config.determine_data_file()
        g = Gateway(path=p1)
        g.set_values(**self.example_data)
        
        new_path = self.make_temp_path(filename=config._data_filename)
        config.set_data_file(new_path)
        
        p2 = config.determine_data_file()
        self.assertEqual(new_path, p2)
        
        g2 = Gateway(path=p2)
        self.assertEqual(g._data, g2._data)
    #


class TestGatewayEncryption(TestGateway):
    
    def setUp(self):
        self.c1 = make_cryptor(PASS1)
        self.c2 = make_cryptor(PASS2)
        return super().setUp()
    
    def test_read_encrypted_data_fails(self):
        """Test that using a cryptor with the wrong password throws an error when attempting to read encrypted data"""
        
        g = Gateway(path=self.path, cryptor=self.c1)
        g["a"] = 42
        
        
        self.assertRaises(CryptoError, lambda: Gateway(path=self.path, cryptor=self.c2))
        self.assertRaises(CryptoError, lambda: Gateway(path=self.path))
    #

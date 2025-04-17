from getpass import getuser
import pathlib
from unittest.mock import patch
from unittest import TestCase

from pillepas import config


class TestFileUtils(TestCase):
    def setUp(self):
        self.path_strings = [
            "~",
            "~/temp",
            "~/temp/some_file.ext"
        ]
        self.home = pathlib.Path.home()

    def test_conversion(self):
        for s in self.path_strings:
            p = config._path_from_str(s)
            
            if s.startswith("~"):
                steps = [p]+list(p.parents)  # path must be home dir, or one of its parents must be
                self.assertIn(self.home, steps)
            #
        #
    
    def test_recover(self):
        for s in self.path_strings:
            p = config._path_from_str(s)
            
            s2 = config._path_to_str(p)
            self.assertEqual(s, s2)
        #
    #
    
    def test_recover_absolute(self):
        """Test that dropping the "~" doesn't prevent obtaining the original paths"""

        for s_original in self.path_strings:
            s_absolute = config._path_from_str(s_original).expanduser().resolve()
            p = config._path_from_str(s_absolute)
            
            s_recovered = config._path_to_str(p)
            self.assertEqual(s_original, s_recovered)
        #
    #

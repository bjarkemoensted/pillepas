import pathlib
from unittest import TestCase

from pillepas.utils import path_from_str, path_to_str


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
            p = path_from_str(s)
            
            if s.startswith("~"):
                steps = [p]+list(p.parents)  # path must be home dir, or one of its parents must be
                self.assertIn(self.home, steps)
            #
        #
    
    def test_recover(self):
        for s in self.path_strings:
            p = path_from_str(s)
            
            s2 = path_to_str(p)
            self.assertEqual(s, s2)
        #
    #
    
    def test_recover_absolute(self):
        """Test that dropping the "~" doesn't prevent obtaining the original paths"""

        for s_original in self.path_strings:
            s_absolute = path_from_str(s_original).expanduser().resolve()
            p = path_from_str(s_absolute)
            
            s_recovered = path_to_str(p)
            self.assertEqual(s_original, s_recovered)
        #
    #

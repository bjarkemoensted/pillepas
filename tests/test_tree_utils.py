from unittest import TestCase

from pillepas.cli import tree_utils


class TestTree(TestCase):
    
    
    def test_attach(self):
        root = tree_utils.MenuNode("foo")
        bar = tree_utils.MenuNode("bar", parent=root)
        
        self.assertTrue(len(root.children) > 0)
        
        baz = tree_utils.LeafNode("baz", action=lambda: None, parent=bar)
        self.assertTrue(len(bar.children) > 0)


if __name__ == '__main__':
    pass

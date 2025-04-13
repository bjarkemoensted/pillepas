import abc
from anytree import NodeMixin, RenderTree
from simple_term_menu import TerminalMenu
from typing import Callable, Iterable, Optional, Tuple



class Node(abc.ABC, NodeMixin):
    """Node class for representing a nested hierarchy of menus.
    The overarching principle here is that an instance of this class represents a node
    in a tree of menus.
    Each node has the responsibility for
    1) Collecting an input from the user (e.g. selecting a submenu),
    2) Acting on the input via a callback (e.g. saving an updated configuration to a file), and
    3) Determine"""
    
    def __init__(self, name: str, callback: Callable=None, parent=None, children=None):
        """name (str) - The name of the node/menu."""
        self.name = name
        self._disp = f"{name} ({self.__class__.__name__})"
        self.callback = callback
        self._menu_cache_key = None
        self._menu = None
        self.parent = parent
        if children:
            self.children = children
        #

    @abc.abstractmethod
    def get_input(self) -> dict|None:
        raise NotImplementedError
    
    def _children_as_strings(self) -> tuple:
        res = tuple(map(repr, self.children))
        return res
    
    def escape(self):
        if self.parent is not None:
            self.root()
        #
    
    @property
    def title(self) -> str:
        c = "*"
        n_edge = 3
        space = "  "
        s = f"{n_edge*c}{space}{self.name}{space}{n_edge*c}"
        return s
    
    @property
    def menu(self) -> TerminalMenu:
        entries = self._children_as_strings()
        if not entries:
            raise ValueError("Can't produce a menu with no options")
        
        needs_recreate = entries != self._menu_cache_key
        if needs_recreate:
            self._menu = TerminalMenu(menu_entries=entries, title=self.title, clear_screen=True)
            self._menu_cache_key = entries
        
        return self._menu
    
    def __call__(self):
        data = self.get_input()
        if data is None:
            data = dict()
        
        if self.callback:
            self.callback(**data)
        
        if self.parent:
            self.parent()
    
    def __repr__(self):
        return self.name
    
    def __str__(self):
        lines = []
        for pre, fill, node in RenderTree(self):
            line = f"{pre}{node._disp}"
            lines.append(line)
        
        res = "\n".join(lines)
        return res


class MenuNode(Node):
    def get_input(self):
        i = self.menu.show()
        if i is None:
            return self.escape()
            
        res = self.children[i]
        res()


class Prompt(Node):
    def get_input(self):
        res = input(f"Enter value for {self.name}: ")
        return res


class Session:
    
    def run(self):
        pass


main_menu = MenuNode(name="Main")


a = Prompt(name="a", parent=main_menu)
b = Prompt(name="b", parent=main_menu)

sub_menu = MenuNode(name="Sub menu", parent=main_menu)

c = Prompt(name="c", parent=sub_menu)
d = Prompt(name="d", parent=sub_menu)


if __name__ == '__main__':
    pass
    #main_menu()
    
    print(main_menu)
    main_menu()
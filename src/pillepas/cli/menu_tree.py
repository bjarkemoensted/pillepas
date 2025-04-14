from anytree import NodeMixin, RenderTree
from simple_term_menu import TerminalMenu
from typing import Callable


class Node(NodeMixin):
    """Node class for representing a nested hierarchy of menus.
    The overarching principle here is that an instance of this class represents a node
    in a tree of menus.
    Each node has the responsibility for
    1) Displaying possible actions to the user
    2) Performing a selected action, e.g. moving to another node, prompting for input and saving, etc.
    3) If appropriate, navigate to another node (e.g. go to the selected submenu, go back to main menu, etc)"""
    
    def __init__(self, name: str, action: Callable=None, display_method: Callable=None, parent=None, children=None):
        """name (str) - The name of the node/menu.
        action (callable, optional) - what to do if the node is selected from a menu.
            Defaults to displaying a menu with its children, if any exist.
        display_method (callable, optional) - A method for representing the node as a string. Defaults to using name.
        parent + children are used by NodeMixin to determine tree structure."""
        
        self.name = name
        if not action:
            action = self.show_menu
        self.action = action
        self.display_method = display_method
        self._menu_key = None  # Key for determining if menu options are identical (to allow pre-selection)
        self._menu = None  # Cached menu

        self.parent = parent
        if children:
            self.children = children
        #

    def display(self) -> str:
        """Get a string representation of the node for e.g. menu entries"""
        if self.display_method:
            return self.display_method()
        return repr(self)
    
    def make_menu(self) -> TerminalMenu:
        """Creates a menu for choosing a child node.
        Recreates the menu because the way we display each node might change.
        Reuses selection from existing menu the selectable children are the same."""

        entries = tuple(child.display() for child in self.children)
        if not entries:
            raise ValueError("Can't produce a menu with no options")
        
        # Start cursor at the same position as last time we showed the menu (if the entries are the same)
        key = tuple(child.name for child in self.children)
        cursor_index = None
        if self._menu_key == key:
            cursor_index = self._menu.chosen_menu_index
        
        # Update the menu and its key
        self._menu_key = key
        self._menu = TerminalMenu(
            menu_entries=entries,
            title=self.title,
            clear_screen=True,
            cursor_index=cursor_index
        )
        
        return self._menu
    
    def show_menu(self):
        """Display a menu to select a child node"""
        menu = self.make_menu()
        i = menu.show()
        if i is None:
            return self.escape()
            
        selected = self.children[i]
        selected()
    
    def __call__(self):
        """Run the 'action' callable, then fall back to the parent node, if one exists."""
        self.action()
        if self.parent:
            self.parent()
    
    def escape(self):
        """Go to the root node, if one exists"""
        if self.parent is not None:
            self.root()
        #
    
    @property
    def title(self) -> str:
        """Display a menu title"""
        c = "*"
        n_edge = 3
        space = "  "
        s = f"{n_edge*c}{space}{self.name}{space}{n_edge*c}"
        return s
    
    def __repr__(self):
        return f"{self.name} ({self.__class__.__name__})"
    
    def __str__(self):
        lines = []
        for pre, fill, node in RenderTree(self):
            line = f"{pre}{node.display()}"
            lines.append(line)
        
        res = "\n".join(lines)
        return res

    def _pre_attach(self, parent):
        """Enforce node type"""
        if not isinstance(parent, Node):
            raise TypeError
        #
    #

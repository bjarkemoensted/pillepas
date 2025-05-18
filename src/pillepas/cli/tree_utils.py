import abc
from anytree import RenderTree, Node
import enum
import logging
logger = logging.getLogger(__name__)
from simple_term_menu import TerminalMenu
from typing import Callable, override


class Escape(enum.Enum):
    """Sentinel values to help control submenu flow."""
    SOFT = enum.auto()
    HARD = enum.auto()


class BaseNode(Node, abc.ABC):
    """Represents a callable node in a nested hiearchy of user interactions.
    The overall idea here is that we need a fairly complex system of menus and submenus for accepting
    and processing user inputs via the terminal. This gets complicated quickly, so we leverage a tree
    structure to separate the concerns related to the menu structure and functionality.
    
    The overarching principle here is that calling a node should
    1) Perform some action, then
    2) Navigate to an appropriate node, if applicable
    
    Override the 'action' method to implement specific behaviors, such as displaying a menu of a node's children,
    prompting for a text input and processing it, etc."""
    
    # Class variable where subclasses can store a reference to the 'root' node class
    _root_class = None
    _allow_children = True
    _revert_after_call = True  # Whether the node should default to reverting to parent, or execute repeatedly
    
    @classmethod
    def get_root_node_class(cls):
        """Get the root node class. This is automatically set for child classes via the __init_subclass__ method.
        Would it have been simpler to just hardcode the base class directly? Yes.
        Would it have been more readable? Also yes.
        Would it feel as 'clean' to directly reference the root instead of using the tree structure to set it
        recursively? No."""
        
        if cls._root_class is None:
            return cls  # If the class var is None, cls IS the root class
        # Otherwise, the class var should have been updated wen subclassing
        return cls._root_class
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Set the root class to the root class of parent class
        cls._root_class = cls.__base__.get_root_node_class()
    
    def __init__(self, name: str, display: Callable|str=None, parent=None, children=None):
        """name (str) - The name of the node/menu.
        display (callable|str, optional) - a string or callable to represent the node in a parent menu.
            Defaults to a standard representation of the node.
        parent + children are used by the Node class to determine tree structure."""
        
        self.name = name
        self._disp = display
        self.parent = parent
        if children:
            self.children = children
        #
    
    def display(self):
        """Get a string representation of the node for e.g. menu entries"""
        
        if isinstance(self._disp, str):
            return self._disp
        elif self._disp is None:
            return self.name
        else:
            return self._disp()
        #
    
    def add(self, *nodes):
        """Add node as a child. Returns self to allow method chaining."""
        for node in nodes:
            node.parent = self
        return self
    
    @abc.abstractmethod
    def action(self) -> None|Escape:
        raise NotImplementedError
    
    def escape(self, hard=False) -> Escape:
        """Handle escape. If hard, will exit the entire menu. If soft, will revert to root menu, unless
        we're already at the root, in which case we exit completely."""
        if hard or self.parent is None:
            return Escape.HARD
        
        return Escape.SOFT
    
    def __call__(self):
        """Run the 'action' callable, then fall back to the parent node, if one exists."""

        logger.debug(f"{self} called.")
        
        run = True
        while run:
            ret = self.action()
            
            logger.debug(f"Node {self} got {ret}")
            run = not self.is_leaf
            
            if (ret is Escape.HARD) or (ret is Escape.SOFT and not self.is_root):
                logger.debug(f"{self} propagating {ret}")
                return ret
            
            #
        return ret

    @property
    def title(self) -> str:
        """Display a menu title"""
        c = "*"
        n_edge = 3
        space = "  "
        s = f"{n_edge*c}{space}{self.name}{space}{n_edge*c}"
        return s
    
    def __repr__(self):
        return f"<node: {self.name}>"
    
    def __str__(self):
        return f"{self.name} ({self.__class__.__name__})"
    
    def as_ascii(self):
        """Display the menu tree as ASCII"""
        lines = []
        for pre, fill, node in RenderTree(self):
            line = f"{pre}{node.display()}"
            lines.append(line)
        
        res = "\n".join(lines)
        return res

    def _pre_attach(self, parent):
        """Enforce node type so all nodes are instances of the root node class.
        This is to ensure that we can rely on functionality like the 'display' class method for the entire tree."""
        
        root_class = self.get_root_node_class()
        if not isinstance(parent, root_class):
            raise TypeError(f"All nodes must inherit from {root_class}. Got parent class {parent.__class__}")
        if not parent._allow_children:
            raise RuntimeError(f"Can't attach child node to {parent} ({parent.__class__} is a leaf class)")
    #


class MenuNode(BaseNode):
    """Represents a sub-menu.
    When called, this node displays a menu with its child nodes. The selected node is called.
    Reverts to the root node on escape."""

    _revert_after_call = False
    
    def __init__(self, *args, **kwargs):
        self._menu_key = None  # Key for determining if menu options are identical (to allow pre-selection)
        self._menu_cached = None  # Cached menu
        super().__init__(*args, **kwargs)

    @override
    def action(self):
        """Display a menu of child nodes, and call the selected node."""
        
        # Choose a child via a terminal menu
        menu = self.make_menu()
        i = menu.show()
        
        # If no selection (e.g. if user pressed escape), call escape method
        if i is None:
            return self.escape()
        
        # Call the selected node
        child = self.children[i]

        res = child()
        logger.debug(f"Node {self} received {res} from child {child}.")

        return res
    
    def make_menu(self) -> TerminalMenu:
        """Creates a menu for choosing a child node.
        Recreates the menu because the way we display each node might change.
        Reuses selection from existing menu the selectable children are the same."""

        logger.debug(f"{self} is creating a menu")
        
        entries = tuple(child.display() for child in self.children)
        if not entries:
            raise ValueError("Can't produce a menu with no options")
        
        # Start cursor at the same position as last time we showed the menu (if the entries are the same)
        key = tuple(child.name for child in self.children)
        cursor_index = None
        if self._menu_key == key:
            cursor_index = self._menu_cached.chosen_menu_index
        
        # Update the menu and its key
        self._menu_key = key
        self._menu_cached = TerminalMenu(
            menu_entries=entries,
            title=self.title,
            clear_screen=True,
            clear_menu_on_exit=False,
            cursor_index=cursor_index,
            raise_error_on_interrupt=True
        )
        
        return self._menu_cached
    #


class LeafNode(BaseNode):
    """Represents a leaf node, in which some action is performed."""

    # This class doesn't call child nodes, so enforce ...leaf-ness(?) to avoid confusion
    _allow_children = False
    
    def __init__(self, name, action: Callable, **kwargs):
        """action (callable) - the callable to run if the node is called."""

        self._action = action
        super().__init__(name, **kwargs)
    
    @override
    def action(self):
        return self._action()
    #

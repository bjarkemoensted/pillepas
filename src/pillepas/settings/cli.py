from anytree import NodeMixin, RenderTree
from simple_term_menu import TerminalMenu
from typing import Iterable, Optional, Tuple



class MenuNode(TerminalMenu, NodeMixin):
    
    def __init__(self, menu_entries: Iterable, parent=None, add_indices=False, **kwargs):
        self._map = dict()
        entries_as_string = []
        for i, elem in enumerate(menu_entries):
            s = elem
            if not isinstance(elem, str):
                s = str(elem)
                self._map[s] = elem
            
            if add_indices and len(menu_entries) <= 9:
                s = f"[{i+1}] {s}"
            entries_as_string.append(s)
            
        self.parent = parent
        super().__init__(entries_as_string, **kwargs)

    def escape_callback(self):
        if self.parent is not None:
            pass
        raise RuntimeError("Oh noes")

    @property
    def chosen_menu_entry(self):
        e = super().chosen_menu_entry
        if e is None:
            return self.escape_callback()
        return self._map[e]

    @property
    def chosen_menu_entries(self):
        ents = super().chosen_menu_entries
        print(ents)
        if ents is None:
            return self.escape_callback()

        return tuple(self._map.get(e, e) for e in ents)

    def _pre_detach(self, parent):
        print("_pre_detach", parent)
    def _post_detach(self, parent):
        print("_post_detach", parent)
    def _pre_attach(self, parent):
        print("_pre_attach", parent)
    def _post_attach(self, parent):
        print("_post_attach", parent)


# terminal_menu = MenuNode(
#     arr,
#     multi_select=True,
#     multi_select_select_on_accept=False,
#     show_multi_select_hint=True,
# )


def spam(*args, **kwargs):
    print(f"EYYYY callback got {args=}, {kwargs=}")


def main():
    arr = ["dog", "cat", "mouse", "squirrel"]
    terminal_menu = MenuNode(
        arr,
        add_indices=True,
        multi_select=True,
        multi_select_select_on_accept=False,
        show_multi_select_hint=True,
    )
    menu_entry_indices = terminal_menu.show()
    print(menu_entry_indices)
    print(terminal_menu.chosen_menu_entries)



if __name__ == '__main__':
    main()

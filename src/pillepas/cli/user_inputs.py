from getpass import getpass
from pathlib import Path
from simple_term_menu import TerminalMenu
from typing import Callable

from pillepas import config
from pillepas.utils import path_from_str, path_looks_like_file


DEFAULT_MENU_SETTINGS = dict(
    exit_on_shortcut=False,
    clear_screen=True,
    show_shortcut_hints=True
)


def select_with_menu(options: list|tuple, options_str: list|tuple=None, title: str=None, current=None, **kwargs):
    """Prompts the user to select one value from a list of allowed values. Returns the selected option.
    options: The allowed values to choose from
    options_str: Optional string representations of the allowed options. If not provided, one is generated using
        the standard repr method.
    title: Optional menu title
    current: Optional current value. If provided, the menu cursor starts at the corresponding option.
    kwargs: Passed on to the TerminalMenu constructor."""
    
    kw = {k: v for k, v in DEFAULT_MENU_SETTINGS.items()}
    kw.update(kwargs)
    
    # Represent options as strings if no string representations are provided
    if options_str is None:
        options_str = [repr(elem) for elem in options]

    # Check that the list have same length
    if len(options) != len(options_str):
        raise RuntimeError

    # Set cursor to current value
    cursor_index = None if current is None else options.index(current)

    # Use a menu to select an option
    menu = TerminalMenu(
        menu_entries=options_str,
        title=title,
        cursor_index=cursor_index,
        **kw
    )
    i = menu.show()

    # Return the selected option (None if nothing was selected)
    if i is None:
        return i
    else:
        return options[i]


def get_input(msg: str=None, validator: Callable[[str], bool|None]=None, invalid_msg: str=None) -> str|None:
    """Prompts user for input.
    msg (str, optional) - The message to display when prompting
    validator: Optional callable which returns a boolean indicating whether input is valid. Re-prompts if not.
    invalid_msg (str, optional) - Message to display on invalid input. Defaults to a standard message."""
    
    if invalid_msg is None:
        invalid_msg = "Invalid input, try again: "

    while True:
        args = () if msg is None else (msg,)
        try:
            s = input(*args)
        except KeyboardInterrupt:
            return None
        
        if validator is None or validator(s):
            return s
        
        msg = invalid_msg
    #


def _prompt_yes_no(base_prompt: str, default: bool=None) -> bool|None:
    """Prompts user to confirm something with yes or no. Returns the corresponding boolean.
    default indicates the value to default to. If None (default) no default boolean will be used.
    Returns None if no boolean can be parsed from result."""

    tail = "y/n"
    d = {"y": True, "yes": True, "n": False, "no": False}
    if default is not None:
        def_ = bool(default)
        d[""] = def_
        tail = "Y/n" if def_ else "y/N"
    
    prompt = f"{base_prompt.strip()} ({tail}): "
    clean = lambda s: s.strip().lower()
    validator = lambda s: clean(s) in d
    s = get_input(msg=prompt, validator=validator)
    if s is None:
        return
    
    res = d[clean(s)]
    return res
    

def prompt_password(prompt: str=None, confirm=False) -> str:
    """Prompts for a password to use for encryption.
    prompt: optional string for prompting for the password. Defaults to the getpass default.
    confirm: Optional bool (default: False) indicating whether the user must confirm their password."""

    kwargs = dict() if prompt is None else dict(prompt=prompt)
    password = getpass(**kwargs)
    if confirm:
        if password and password != getpass("Confirm password: "):
            raise RuntimeError("First and second attempts differed")
        #

    return password
    #


def _validate_dir(s: str):
    p = path_from_str(s)
    # Force input without a file extension
    if path_looks_like_file(p):
        print("Enter path to a folder, not a file")
        return False
    return True


def prompt_directory(msg: str=None) -> Path|None:
    """Prompts for a new location for data storage. Asks whether to create if missing."""
    
    if not msg:
        msg = "Enter path: "

        
    
    s = get_input(msg=msg, validator=_validate_dir)
    if s is None:
        return s
    
    p = path_from_str(s)
    
    
    if not p.exists():
        msg = f"Path {p} does not exist - create it?"
        do_it = _prompt_yes_no(base_prompt=msg, default=True)
    
        if do_it:
            p.mkdir(parents=False, exist_ok=False)
        else:
            return None
        #
    
    return p


if __name__ == '__main__':
    dir_ = prompt_directory()
    print(dir_)

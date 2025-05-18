import pathlib


def path_to_str(path: pathlib.Path) -> str:
    """Represent a path as a string. If the path in the home dir, uses "~" to represent home dir."""
    
    path = path.expanduser()
    
    # Attempt to express path relative to home dir
    try:
        path = (pathlib.Path("~") / path.relative_to(pathlib.Path.home()))
    except ValueError:
        pass  # fails if not a subdirectory of home, so just ignore
    
    return str(path)


def path_from_str(s: str) -> pathlib.Path:
    """Turns string into path"""
    return pathlib.Path(s).expanduser().resolve()


def path_looks_like_file(path: pathlib.Path) -> bool:
    """"Helper method for identifying paths that are probably file paths."""
    res = path.suffixes or (path.exists() and path.is_file())
    return res


def is_in_home_dir(path: pathlib.Path) -> bool:
    try:
        path = path.resolve()
        home = pathlib.Path.home().resolve()
        path.relative_to(home)
        return True
    except ValueError:
        return False

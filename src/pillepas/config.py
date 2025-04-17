import logging
import pathlib
import platformdirs
import yaml

_here = pathlib.Path(__file__).parent.resolve()


APPNAME = "pillepas"
logger = logging.getLogger(APPNAME)

URL = "https://app.apoteket.dk/pillepas/borger/bestilling"

_data_filename = "data.stuff"


def _get_config_path() -> pathlib.Path:
    """Get the path to a config file. This one is fixed"""
    
    dir_s = platformdirs.user_config_dir(APPNAME, ensure_exists=True)
    p = pathlib.Path(dir_s).resolve()
    
    return p    


CONFIG_PATH = _get_config_path() / "data_location.txt"


def determine_data_file() -> pathlib.Path:
    try:
        s = CONFIG_PATH.read_text()
        res = _path_from_str(s)
    except FileNotFoundError:
        res = CONFIG_PATH.parent / _data_filename
    
    return res


def set_data_file(path: pathlib.Path):
    oldpath = determine_data_file()
    
    if not path.suffixes:
        path = path / _data_filename
    
    path.parent.mkdir(exist_ok=True, parents=True)
    
    if path.exists() and not path.is_file():
        raise RuntimeError(f"Provide a file path - got {path}")
    
    s = _path_to_str(path)
    CONFIG_PATH.write_text(s)
    if oldpath.exists():
        oldpath.rename(path)


def _path_to_str(path: pathlib.Path) -> str:
    """Represent a path as a string. If the path in the home dir, uses "~" to represent home dir."""
    
    path = path.expanduser()
    
    try:
        path = (pathlib.Path("~") / path.relative_to(pathlib.Path.home()))
    except ValueError:
        pass
    
    return str(path)


def _path_from_str(s: str) -> pathlib.Path:
    """Turns string into path"""
    return pathlib.Path(s).expanduser().resolve()


def _read_fields() -> dict:
    p = _here / 'data' / "fields.yaml"
    return yaml.safe_load(p.read_text())


if __name__ == '__main__':
    pass

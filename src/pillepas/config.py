import logging
import pathlib
import platformdirs
import yaml

from pillepas.utils import path_from_str, path_to_str, path_looks_like_file

_here = pathlib.Path(__file__).parent.resolve()


APPNAME = "pillepas"
logger = logging.getLogger(APPNAME)

URL = "https://app.apoteket.dk/pillepas/borger/bestilling"

# Path to file containing the data storage location. This is fixed, in the app's config dir
_config_dir_str = platformdirs.user_config_dir(APPNAME, ensure_exists=True)
CONFIG_PATH = pathlib.Path(_config_dir_str).resolve() / "data_location.txt"

DATA_FILENAME = "data.stuff"


def _default_data_dir():
    return CONFIG_PATH.parent


def _determine_data_dir() -> pathlib.Path:
    """Figures out where data is stored. Tries to read the path from the app's config dir.
    Reverts to the config dir if no path is stored there."""
    try:
        s = CONFIG_PATH.read_text()
        res = path_from_str(s)
    except FileNotFoundError:
        res = _default_data_dir()
    
    return res


def get_data_file():
    dir_ = _determine_data_dir()
    res = dir_ / DATA_FILENAME
    return res


def set_data_dir(path: pathlib.Path):        
    if path_looks_like_file(path):
        raise RuntimeError(f"Path looks like a file ({path}). Must provide path to a directory.")
    
    path.mkdir(exist_ok=True, parents=True)
    
    s = path_to_str(path)
    CONFIG_PATH.write_text(s)


if __name__ == '__main__':
    pass

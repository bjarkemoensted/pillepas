import json
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
    
    try:
        p = (pathlib.Path("~") / p.relative_to(pathlib.Path.home()))
    except ValueError:
        pass
    
    return p    


CONFIG_PATH = _get_config_path() / "data_location.txt"


def determine_data_file() -> pathlib.Path:
    try:
        s = CONFIG_PATH.read_text()
        res = pathlib.Path(s)
    except FileNotFoundError:
        res = CONFIG_PATH.parent / _data_filename
    
    return res


def set_data_file(path: pathlib.Path):
    oldpath = determine_data_file()
    
    if path.exists() and not path.is_file():
        raise RuntimeError(f"Provide a file path - got {path}")
    
    path.parent.mkdir(parents=True, exist_ok=True)
    s = str(path)
    CONFIG_PATH.write_text(s)
    oldpath.rename(path)


def _read_fields():
    p = _here / "fields.yaml"
    return yaml.safe_load(p.read_text())


fields = _read_fields()


if __name__ == '__main__':
    pass

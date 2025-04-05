import logging
import pathlib
import platformdirs
import yaml

_here = pathlib.Path(__file__).parent.resolve()


APPNAME = "pillepas"
logger = logging.getLogger(APPNAME)

URL = "https://www.apoteket.dk/pillepas"  # TODO FIX!!!


def _get_config_path():
    dir_ = platformdirs.user_config_dir(APPNAME)
    res = pathlib.Path(dir_).expanduser()
    res.mkdir(parents=True, exist_ok=True)
    return res
    
    
CONFIG_PATH = _get_config_path()


if __name__ == '__main__':
    pass

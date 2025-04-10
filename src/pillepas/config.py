import logging
import pathlib
import platformdirs
import yaml

_here = pathlib.Path(__file__).parent.resolve()


APPNAME = "pillepas"
logger = logging.getLogger(APPNAME)

URL = "https://app.apoteket.dk/pillepas/borger/bestilling"


def _get_config_path():
    dir_ = platformdirs.user_config_dir(APPNAME)
    res = pathlib.Path(dir_).expanduser()
    res.mkdir(parents=True, exist_ok=True)
    return res
    
    
CONFIG_DIR = _get_config_path()
CONFIG_FILE = CONFIG_DIR / "settings.json"

DATA_PATH = CONFIG_DIR / "data.json"  # TODO prompt for it and store in the config path

if __name__ == '__main__':
    pass

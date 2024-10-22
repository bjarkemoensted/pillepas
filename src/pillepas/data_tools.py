import os
import pathlib
import platformdirs

from pillepas import config


def get_config_dir_path() -> pathlib.Path:
    try:
        path_str = os.environ[config.config_env_var]
    except KeyError:
        path_str = platformdirs.user_config_dir(config.appname)
    
    res = pathlib.Path(path_str).expanduser()
    return res


def get_data_path() -> pathlib.Path:
    res = get_config_dir_path() / config.config_data_filename
    return res

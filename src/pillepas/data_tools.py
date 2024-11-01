
import json
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
    res.mkdir(parents=True, exist_ok=True)
    return res


def get_data_path() -> pathlib.Path:
    res = get_config_dir_path() / config.config_data_filename
    return res


def load_data():
    stuff = get_data_path().read_text()
    res = json.loads(stuff)
    return res


if __name__ == '__main__':
    with open("sandbox_data.json", "r") as f:
        data = json.load(f)
    
    print(data)
    
    print(get_data_path())
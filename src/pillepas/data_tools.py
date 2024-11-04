import copy
import json
import os
import pathlib
import platformdirs
import warnings

from pillepas import config
from pillepas import crypto


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


def load_data(path=None, crypt: crypto.Crypt=None):
    if path is None:
        path = get_data_path()
    
    if crypt is None:
        data_json = path.read_text()
    else:
        data_encrypted = path.read_bytes()
        data_json = crypt.decrypt(data_encrypted)

    res = json.loads(data_json)
    return res


def save_data(data: dict, path=None, crypt: crypto.Crypt=None):
    if path is None:
        path = get_data_path()
    
    data_json = json.dumps(data, indent=4)
    
    if crypt is None:
        path.write_text(data_json)
    else:
        data_encrypted = crypt.encrypt(data_json)
        path.write_bytes(data_encrypted)
    #


def preprocess_for_storage(data: dict):
    """Prepares a dict read from the form for saving.
    Removes the 'volatile' fields (e.g. travel start date, which will likely change before next usage).
    Orders the remaining by field type, so the result has a 'constant' and 'aggregate' key."""

    res = dict()
    for k, v in data.items():
        try:
            type_ = config.field2type[k]
        except KeyError:
            warnings.warn(f"Disregarding unrecognized input fields: '{k}'", RuntimeWarning)
            continue
        
        if type_ == "volatile":
            continue
        
        if type_ not in res:
            res[type_] = dict()
        
        res[type_][k] = v
    
    return res


def iterate_changed_values(new_values: dict, old_values: dict=None):
    """Takes 2 dictionaries and iterates over keys and values where the new values differ from the old.
    So this will provide tuples like
    (key, new, old)
    where the new and old values are different for the given key.
    In cases where a key only exists in one of the dicts, None will be used for the value."""
    
    if old_values is None:
        old_values = dict()

    # Iterating over the keys in the order they appear in the new/old dicts
    seen = set([])
    keys = list(new_values.keys()) + list(old_values.keys())
    
    for k in keys:
        if k in seen:
            continue
        
        seen.add(k)
        new = new_values.get(k)
        old = old_values.get(k)
        
        if new != old:
            yield k, new, old
        #
    #


def update_data(new_data: dict, existing_data: dict=None):
    """Takes new and old data in the format
        {category: {field: value, ...}, ..., aggregated_category: [{field: value, ...}, ...]}
    and returns the old data updated with the new.
    Updated means for normal categories that the new values replace the old, and fields that only appear in
    the old data are deleted.
    For aggregated categories, the new data is simply appended to the list.
    This means any decisions regarding which values to keep in cases of conflicts etc must be made prior
    to calling this method."""

    if existing_data is None:
        existing_data = dict()

    res = copy.deepcopy(existing_data)    
    
    for category, new_values in new_data.items():
        new_values = copy.deepcopy(new_values)
        
        # Append aggregate categories to the existing list of values
        if category in config.aggregate_field2id:
            res[category] = res.get(category, []) + [new_values]
            continue
        
        if category not in res:
            res[category] = dict()
            
        # Otherwise keep the new values
        old_values = res.get(category, dict())
        for field, new, _ in iterate_changed_values(new_values=new_values, old_values=old_values):
            if new is None:
                del res[category][field]
            else:
                res[category][field] = new
            #
        #

    return res


if __name__ == '__main__':
    recorded = json.loads((pathlib.Path(__file__).parent.parent.parent / "deleteme_recorded.json").read_text())
    
    data = preprocess_for_storage(recorded)
    prepped = update_data(new_data=data, existing_data=None)
    
    from pprint import pprint
    
    here = pathlib.Path(__file__).parent
    testfile = here / "delemete.json"
    
    crypt = crypto.Crypt(password='hunter2')
    save_data(data=prepped, path=testfile, crypt=crypt)
    
    crypt = None
    loaded = load_data(path=testfile, crypt=crypt)
    pprint(loaded)
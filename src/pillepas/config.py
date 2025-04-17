import dataclasses
import logging
import pathlib
import platformdirs
from typing import Dict, List, Iterable, Optional
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


def _read_fields():
    p = _here / "fields.yaml"
    return yaml.safe_load(p.read_text())


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


@dataclasses.dataclass
class Field:
    category: str
    key: str
    name: str
    label: str
    tags: list = dataclasses.field(default_factory=list)
    #tags: Optional[Iterable[str]] = None
    
    def matches(self, **kwargs) -> bool:
        """Determine whether the field matches input criteriea.
        For example:
        my_field.matches(category='some_category')
        returns all fields with the specified category.
        Properties with multiple values (e.g. 'tags' can be specified as either a single value,
        or a list/tuple of values, i.e.
        my_field.matches(tags='some_tag'))
        or
        my_field.matches(tags=['some_tag', 'some_other_tag']))"""

        lookups = ["tags"]  # The attributes where we must check if values are contained, rather than equality
        
        for k, v in kwargs.items():
            if k in lookups:
                # If lookup attribute, all specified values must be contained
                lookfor_vals = v if isinstance(v, (list, tuple)) else [v]
                has_vals = getattr(self, k)
                if not all(val in has_vals for val in lookfor_vals):
                    return False
                #
            else:
                # Otherwise, the attribute must match the specified one
                if getattr(self, k) != v:
                    return False
                #
            #
        
        return True


class FieldContainer:
    stuff: List[Field]
    
    def __init__(self, fields: dict):
        self.stuff = []
        for category, entries in fields.items():
            for data in entries:
                
                try:
                    data["tags"] = [s.strip() for s in data["tags"].split(",")]
                except KeyError:
                    pass
                d = Field(category=category, **data)
                self.stuff.append(d)
            #
        #
    
    def lookup(self, **kwargs):
        """Lookup fields matching the specified criteria"""
        res = [d for d in self.stuff if d.matches(**kwargs)]
        return res
    
    
field_data = _read_fields()

fields = FieldContainer(field_data)


if __name__ == '__main__':
    from pprint import pprint
    
    #pprint(fields.lookup(category="medicine", tags=["append"]))
    
    print(CONFIG_PATH.resolve())
    p = determine_data_file()
    print(p.resolve())
    

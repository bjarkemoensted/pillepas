from __future__ import annotations
import logging

logger = logging.getLogger(__name__)
from typing import Iterable

from pillepas.user_inputs import (
    select_with_menu,
    prompt_password,
    prompt_directory
)
from pillepas.cli.tree_utils import MenuNode, LeafNode
from pillepas import config
from pillepas.crypto import Cryptor, CryptoError
from pillepas.persistence import data
from pillepas.persistence.gateway import Gateway


class GatewayInterface(Gateway):
    """Exposes various methods that act on a gateway, some using user inputs."""

    def __init__(self, path: Path, cryptor: Cryptor=None):
        super().__init__(path=path, cryptor=cryptor)
        missing_keys = filter(lambda k: k not in self, (field.key for field in data.FIELDS))
        
        d = {k: None for k in missing_keys}
        self.set_values(**d)
        
    def prompt_password(self):
        """Prompts user for password, then updates the gateway's password"""
        password = prompt_password()
        cryptor = Cryptor(password=password) if password else None
        self.change_cryptor(cryptor=cryptor)
    
    def make_menu_single(self, key: str, options: list|tuple, title: str=None, default_value_selected=None):
        """Uses a terminal menu to select a value from a list of options.
        The value is then saved to the specified key in the gateway.
        If the key is already stored in the gateway, the cursor starts at that value.
        Otherwise, the cursor starts at default_value_selected if specified."""

        if default_value_selected is not None and default_value_selected not in options:
            raise ValueError(f"Default selection must be among the allowed options")
        
        _title = title
        
        def prompt_and_set():
            current = self.get(key)
            if current is None:
                current = default_value_selected
            
            title = _title
            if not title:
                title = f"Select value for {key}"
            
            val = select_with_menu(options=options, title=title, current=current)
            self[key] = val

        return prompt_and_set
    
    def choose_parameter(self, parameter_name: str, title: str=None):
        parameter = data.FIELDS[parameter_name]
        return self.make_menu_single(key=parameter.key, options=parameter.valid_values, title=title)
    
    def change_data_dir(self):
        current = config.determine_data_file().parent
        current_s = config._path_to_str(current)
        msg = f"Enter new folder for storing data (currently using {current_s}): "
        
        new_dir = prompt_directory(msg=msg)
        logger.debug(f"Got new data dir: {new_dir}")
        config.set_data_file(new_dir)
        new_path = config.determine_data_file()
        logger.debug(f"Updated data dir in config: {new_path}")
        self.move_data(new_path)
    #

    @classmethod
    def create_with_prompt(cls) -> GatewayInterface:
        path = config.determine_data_file()
        if not path.exists():
            password = prompt_password(f"Enter password (leave blank to not encrypt): ", confirm=True)
            c = Cryptor(password)
            return cls(path=path, cryptor=c)

        c = Cryptor(password=None)
        prompt = f"{path} is encrypted - enter password: "

        while True:
            try:
                res = cls(path=path, cryptor=c)
                return res
            except CryptoError:
                pass

            password = prompt_password(prompt=prompt)
            c = Cryptor(password=password)
            prompt = f"Invalid password, try again: "
        #


def build_menu() -> MenuNode:
    g = GatewayInterface.create_with_prompt()
    main = MenuNode(name="Main menu")
    
    settings = MenuNode(
        "Settings", parent=main
    ).add(
        LeafNode("Change password", action=g.prompt_password)
    ).add(
        LeafNode(
            "Store sensitive data",
            action=g.choose_parameter("save_sensitive"),
        )
    ).add(
        LeafNode(
            "Change data directory",
            action=g.change_data_dir
        )
    )
    
    data_menu = MenuNode(
        "Data"
    )
    
    
    return main
    
    


if __name__ == '__main__':
    import logging
    
    from pathlib import Path
    path = Path("/tmp/deleteme.json")

    logpath = path.parent / "log.log"
    logpath.unlink(missing_ok=True)
    logging.basicConfig(level=logging.DEBUG, filename=str(logpath))

    menu = build_menu()
    try:
        menu()
    except:
        pass
    finally:
        print(logpath.read_text())
    
    
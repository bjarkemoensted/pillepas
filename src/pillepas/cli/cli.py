from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from typing import Iterable

from pillepas.user_inputs import (
    select_with_menu,
    prompt_password,
    prompt_data_dir
)
from pillepas.cli.tree_utils import MenuNode, LeafNode
from pillepas import config
from pillepas.crypto import Cryptor, CryptoError
from pillepas import const
from pillepas.persistence.gateway import Gateway


class GatewayInterface:
    """Exposes various methods that act on a gateway, some using user inputs."""

    def __init__(self, gateway: Gateway):
        self.gateway = gateway
        
    def prompt_password(self):
        """Prompts user for password, then updates the gateway's password"""
        password = prompt_password()
        cryptor = Cryptor(password=password) if password else None
        self.gateway.change_cryptor(cryptor=cryptor)
    
    def make_menu_single(self, key: str, options: list|tuple, title: str=None, default_value_selected=None):
        """Uses a terminal menu to select a value from a list of options.
        The value is then saved to the specified key in the gateway.
        If the key is already stored in the gateway, the cursor starts at that value.
        Otherwise, the cursor starts at default_value_selected if specified."""

        if default_value_selected is not None and default_value_selected not in options:
            raise ValueError(f"Default selection must be among the allowed options")
        
        _title = title
        
        def prompt_and_set():
            current = self.gateway.get(key)
            if current is None:
                current = default_value_selected
            
            title = _title
            if not title:
                title = f"Select value for {key}"
            
            val = select_with_menu(options=options, title=title, current=current)
            self.gateway[key] = val

        return prompt_and_set
    
    def menu_from_const(self, const: const.Var, title: str=None):
        return self.make_menu_single(key=const.s, options=const.valid_values, title=title)
    
    def change_data_dir(self):
        new_dir = prompt_data_dir()
        config._set_data_dir(new_dir)
        self.gateway.move_data(new_dir)
    #


def setup_gateway(path: Path) -> Gateway:
    if not path.exists():
        password = prompt_password(f"Enter password (leave blank to not encrypt): ", confirm=True)
        c = Cryptor(password)
        return Gateway(path=path, cryptor=c)
    
    c = Cryptor(password=None)
    prompt = f"{path} is encrypted - enter password: "
    
    while True:
        try:
            res = Gateway(path=path, cryptor=c)
            return res
        except CryptoError:
            pass
        
        password = prompt_password(prompt=prompt)
        c = Cryptor(password=password)
        prompt = f"Invalid password, try again: "
    #


def build_menu(gateway: Gateway) -> MenuNode:
    g = GatewayInterface(gateway=gateway)
    main = MenuNode(name="Main menu")
    
    settings = MenuNode(
        "Settings", parent=main
    ).add(
        LeafNode("Change password", action=g.prompt_password)
    ).add(
        LeafNode(
            "Store sensitive data",
            action=g.menu_from_const(const=const.save_sensitive),
        )
    ).add(
        LeafNode(
            "Change data directory",
            action=g.change_data_dir
        )
    )
    
    #data = MenuNode
    
    
    return main
    
    


if __name__ == '__main__':
    import logging
    
    from pathlib import Path
    path = Path("/tmp/deleteme.json")

    logpath = path.parent / "log.log"
    logpath.unlink(missing_ok=True)
    logging.basicConfig(level=logging.DEBUG, filename=str(logpath))
    
    
    gateway = setup_gateway(path)
    print(gateway)
    
    menu = build_menu(gateway=gateway)
    try:
        menu()
    except:
        pass
    finally:
        print(logpath.read_text())
    
    
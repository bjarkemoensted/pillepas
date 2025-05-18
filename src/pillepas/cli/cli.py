from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


from pillepas.cli import actions, user_inputs
from pillepas.cli.tree_utils import MenuNode, LeafNode
from pillepas import config
from pillepas.utils import path_to_str


class CLISession:
    def __init__(self):
        self.gateway = actions.make_gateway()
    
    def change_password(self):
        cryptor = actions.make_cryptor()
        self.gateway.change_cryptor(cryptor=cryptor)

    def change_dir(self):
        current = self.gateway.path.parent
        current_s = path_to_str(current)

        msg = f"Enter new folder for storing data (currently using {current_s}): "
        new_dir = user_inputs.prompt_directory(msg=msg)
        if not new_dir:
            logger.debug(f"No new directory provided. Aborting.")
            return

        logger.debug(f"Got new data dir: {new_dir}")
        actions.change_data_dir(gateway=self.gateway, new_dir=new_dir)
    
    def revert_data_dir(self):
        dir_ = config._default_data_dir()
        msg = f"Change data directory to default ({dir_})?"
        if user_inputs._prompt_yes_no(msg, default=True):
            actions.change_data_dir(gateway=self.gateway, new_dir=dir_)


def build_menu() -> MenuNode:
    sess = CLISession()
    main = MenuNode(name="Main menu")
    
    settings = MenuNode(
        "Settings", parent=main
    ).add(
        LeafNode("Change password", action=sess.change_password)
    ).add(
        LeafNode(
            "Change data directory",
            action=sess.change_dir
        )
    ).add(
        LeafNode(
            "Revert to default data storage directory",
            action=sess.revert_data_dir
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
    finally:
        print(logpath.read_text())
    
    
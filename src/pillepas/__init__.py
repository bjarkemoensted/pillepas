from importlib.metadata import version
import logging

__version__ = version("pillepas")

logging.getLogger(__name__).addHandler(logging.NullHandler())

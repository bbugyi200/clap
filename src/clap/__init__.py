"""(C)ommand (L)ine (A)rgument (P)arsing.

A thin wrapper around the standard Python argparse library.
"""

import logging as _logging

from ._core import (
    Arguments,
    MainType,
    NewCommand,
    Parser,
    main_factory,
    new_command_factory,
)


__all__ = [
    "Arguments",
    "MainType",
    "NewCommand",
    "Parser",
    "main_factory",
    "new_command_factory",
]

__author__ = "Bryan M Bugyi"
__email__ = "bryanbugyi34@gmail.com"
__version__ = "0.3.0"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())

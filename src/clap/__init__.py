"""(C)ommand (L)ine (A)rgument (P)arsing.

A thin wrapper around the standard argparse library.
"""

__author__ = "Bryan M Bugyi"
__email__ = "bryanbugyi34@gmail.com"
__version__ = "0.2.1"

from .api import (
    Arguments,
    MainType,
    NewCommand,
    Parser,
    main_factory,
    new_command_factory,
)

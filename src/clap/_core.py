"""The clap package's catch-all module.

You should only add code to this module when you are unable to find ANY other
module to add it to.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version as get_version
import inspect
import os
from pathlib import Path
import re
import signal
import sys
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Optional,
    Protocol,
    Sequence,
    Type,
    cast,
    runtime_checkable,
)

from bugyi.lib.meta import scriptname
from bugyi.lib.types import literal_to_list
from logrus import (
    Log,
    LogFormat,
    Logger,
    LogLevel,
    get_default_logfile,
    init_logging,
)
from pydantic import BaseSettings


class MainType(Protocol):
    """Type of the `main()` function returned by `main_factory()`."""

    def __call__(self, argv: Sequence[str] = None) -> int:
        """This method captures the `main()` function's signature."""


@runtime_checkable
class ConfigType(Protocol):
    """Application Configuration Protocol

    In other words, his class describes what an application Config object
    should look like.
    """

    @classmethod
    def from_cli_args(cls, argv: Sequence[str]) -> "ConfigType":
        """Constructs a new Config object from command-line arguments."""


def main_factory(
    run: Callable[[ConfigType], int], config: Type[ConfigType]
) -> MainType:
    """Factory used to create a new `main()` function.

    Args:
        run: A function that acts as the real entry point for a program.
        config: A pydantic.BaseSettings type that represents our applications
          config.

    Returns:
        A generic main() function to be used as a script's entry point.
    """

    def main(argv: Sequence[str] = None) -> int:
        if argv is None:  # pragma: no cover
            argv = sys.argv

        cfg = config.from_cli_args(argv)

        verbose: int = getattr(cfg, "verbose", 0)
        logs: List[Log] = getattr(cfg, "logs", [])

        init_logging(logs=logs, verbose=verbose)

        logger = Logger("clap", cfg=cfg).bind_fargs(argv=argv)

        # The following log messages will obviously only be visible if the
        # corresponding log level really is enabled, but stating the obvious in
        # this case seemed like the right thing to do so ??\_(???)_/??.
        logger.trace("TRACE level logging enabled.")
        logger.debug("DEBUG level logging enabled.")

        try:
            status = run(cfg)
        except KeyboardInterrupt:  # pragma: no cover
            logger.info("Received SIGINT signal. Terminating script...")
            return 128 + signal.SIGINT.value
        except Exception:  # pragma: no cover
            logger.exception(
                "An unrecoverable error has been raised. Terminating script..."
            )
            return 1
        else:
            return status

    return main


class Config(BaseSettings, allow_mutation=False):
    """Default CLI arguments / app configuration."""

    logs: List[Log]
    verbose: int


def Parser(
    *args: Any, name: str = None, **kwargs: Any
) -> argparse.ArgumentParser:
    """Wrapper for argparse.ArgumentParser."""
    if name is None:
        name = scriptname(up=1)

    stack = list(inspect.stack())
    stack.pop(0)
    frame = stack.pop(0).frame

    if kwargs.get("description") is None:
        try:
            kwargs["description"] = frame.f_globals["__doc__"]
        except KeyError:
            pass

    if kwargs.get("formatter_class") is None:
        kwargs["formatter_class"] = _HelpFormatter

    valid_log_levels = sorted(cast(List[str], literal_to_list(LogLevel)))
    valid_log_formats = sorted(cast(List[str], literal_to_list(LogFormat)))

    parser = argparse.ArgumentParser(*args, **kwargs)
    parser.add_argument(
        "-L",
        "--log",
        metavar="FILE[:LEVEL][@FORMAT]",
        dest="logs",
        action="append",
        nargs="?",
        const="+",
        default=[],
        type=_log_type_factory(name),
        help=(
            "This option can be used to enable a new logging handler. FILE"
            " should be either a path to a logfile or one of the following"
            " special file types: [1] 'stderr' to log to standard error"
            " (enabled by default), [2] 'stdout' to log to standard out, [3]"
            " 'null' to disable all console (e.g. stderr) handlers, or [4]"
            " '+[NAME]' to choose a default logfile path (where NAME is an"
            " optional basename for the logfile). LEVEL can be any valid log"
            f" level (i.e. one of {valid_log_levels}) and FORMAT can be any"
            f" valid log format (i.e. one of {valid_log_formats}). NOTE: This"
            " option can be specified multiple times and has a default"
            " argument of %(const)r."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "How verbose should the output be? This option can be specified"
            " multiple times (e.g. -v, -vv, -vvv, ...)."
        ),
    )

    caller_module = inspect.getmodule(frame)
    package = getattr(caller_module, "__package__", None)
    if package:
        assert caller_module is not None
        try:
            package_version = get_version(package)
            version = f"{package} {package_version}"

            package_location = _get_package_location(
                caller_module.__file__, package
            )
            version += f"\n    from {package_location}"

            while stack:
                exe_fname = stack.pop(0).filename
                if os.access(exe_fname, os.X_OK):
                    version += f"\n    by {_shorten_homedir(exe_fname)}"
                    break

            pyversion = ".".join(str(x) for x in sys.version_info[:3])
            version += f"\n    using Python {pyversion}"

            try:
                clap_version = get_version(__package__)
            except PackageNotFoundError:
                from . import __version__

                clap_version = __version__

            version += f"\n{__package__} {clap_version}"

            clap_location = _get_package_location(__file__, __package__)
            version += f"\n    from {clap_location}"

            parser.add_argument("--version", action="version", version=version)
        except PackageNotFoundError:
            pass

    return parser


def _log_type_factory(name: str) -> Callable[[str], Log]:
    def log_type(arg: str) -> Log:
        # This regex will match arguments of the form 'FILE[:LEVEL][@FORMAT]'.
        pttrn = (
            r"^(?P<file>[^:@]+)(?::(?P<level>[^:@]+))?(?:@(?P<format>[^:@]+))?"
        )
        match = re.match(pttrn, arg)
        if not match:
            raise argparse.ArgumentTypeError(
                f"Bad log specification ({arg!r}). Must match the following"
                f" regular expression: {pttrn!r}"
            )

        file = match.group("file")
        # If FILE is of the form '+[NAME]'...
        if file.startswith("+"):
            # Then we use a default logfile location.
            logfile_stem = file[1:]
            if not logfile_stem:
                logfile_stem = name
            file = str(get_default_logfile(logfile_stem))

        # If `--log null` is specified on the command-line...
        if file == "null":
            # HACK: The intention here is to disable logging to the console
            # (i.e. 'stderr' or 'stdout'). The actual effect is that only
            # CRITICAL logging messages will get logged to stderr. This
            # approaches a real solution since CRITICAL is used so infrequently
            # in practice, but is not technically correct.
            return Log(file="stderr", format="nocolor", level="CRITICAL")

        format_ = cast(Optional[LogFormat], match.group("format"))
        # If format is unset and this is a console logger...
        if format_ is None and file in ["stdout", "stderr"]:
            format_ = "color"
        # Else if format is unset and this is a file logger...
        elif format_ is None:
            format_ = "json"

        level = cast(Optional[LogLevel], match.group("level"))
        if level is not None:
            level = cast(LogLevel, level.upper())

        return Log(file=file, format=format_, level=level)

    return log_type


def _get_package_location(file_path: str, package: str) -> str:
    file_parent = Path(file_path).parent
    result = str(file_parent)

    package_subpath = package.replace(".", "/")
    result = "".join(result.rsplit(package_subpath, 1))

    result = _shorten_homedir(result)
    result = result.rstrip("/")

    return result


def _shorten_homedir(path: str) -> str:
    home = str(Path.home())
    return path.replace(home, "~")


class _HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Custom argparse.HelpFormatter that uses raw descriptions and sorts optional
    arguments alphabetically.
    """

    def add_arguments(self, actions: Iterable[argparse.Action]) -> None:
        actions = sorted(actions, key=_argparse_action_key)
        super().add_arguments(actions)


def _argparse_action_key(action: argparse.Action) -> str:
    opts = action.option_strings
    if opts:
        return opts[-1].lstrip("-")
    else:
        return action.dest


class NewCommand(Protocol):
    """Type of the function returned by `new_command_factory()`."""

    def __call__(
        self,
        name: str,
        *,
        help: str,  # pylint: disable=redefined-builtin
        **kwargs: Any,
    ) -> argparse.ArgumentParser:
        """This method captures the `new_command()` function's signature."""


def new_command_factory(
    parser: argparse.ArgumentParser,
    *,
    dest: str = "command",
    required: bool = True,
    description: str = None,
    **kwargs: Any,
) -> NewCommand:
    """Returns a `new_command()` function that can be used to add subcommands.

    Args:
        parser: The argparse parser that we want to add subcommands to.
        dest: The attribute name that the subcommand name will be stored under
          inside the Namespace object.
        required: Will this subcommand be required or optional?
        description: This argument describes what the subcommand is used for.
        kwargs: These keyword arguments are relayed to the
          ``parser.add_subparsers()`` function call.
    """
    subparsers = parser.add_subparsers(
        dest=dest, required=required, description=description, **kwargs
    )

    def new_command(
        name: str,
        *,
        help: str,  # pylint: disable=redefined-builtin
        **inner_kwargs: Any,
    ) -> argparse.ArgumentParser:
        return subparsers.add_parser(
            name,
            formatter_class=parser.formatter_class,
            help=help,
            description=help,
            **inner_kwargs,
        )

    return new_command

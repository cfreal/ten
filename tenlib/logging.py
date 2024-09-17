"""Everything related to logging.

Ten exposes a `log` objet that you can use to log various messages:

```python
>>> log.info('Hello')
>>> log.debug('There')
```

To set the verbosity of logging in the CLI (default: none), use `set_cli_level`.

Additionally, logs are written to a log file (in `~/ten.log` by default).
To set the level of logging in this file, use `set_level`. Change the path using
`set_file`.

```python
>>> log.info('Hello')
>>> logging.set_cli_level('DEBUG')
>>> log.error('Woops!')
[07/13/22 17:49:07] ERROR    Woops !                                   <stdin>:1
```
"""
from __future__ import annotations

import logging
import os
from typing import IO
from logging import Handler, Logger

from rich.console import Console
from rich.logging import RichHandler

from tenlib.flow.console import get_console

__all__ = [
    "logger",
    "log",
    "set_level",
    "set_cli_level",
    "set_file",
    "CRITICAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
    "SUCCESS",
    "FAILURE",
    "TRACE",
]

DEFAULT_FILE_LEVEL: int = logging.DEBUG
FILE_CONSOLE_WIDTH: int = 80

__cli_handler: CLIHandler = None
__file_handler: Handler | None = None


def logger(name: str | None = "ten") -> TenLogger:
    """Returns a logger with the specified name or, if name is None, returns the root
    logger of the hierarchy.
    """
    return logging.getLogger(name)


class CLIHandler(RichHandler):
    """A custom CLI handler that can be disabled."""

    enabled: bool = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        if self.enabled:
            super().emit(record)

    def __repr__(self) -> str:
        level = logging.getLevelName(self.level)
        return f"<CLIHandler enabled={self.enabled} level={level}>"


def _create_cli_handler() -> None:
    global __cli_handler
    __cli_handler = CLIHandler(console=get_console())
    _get_root_logger().addHandler(__cli_handler)


def set_cli_level(level: int | str | None) -> None:
    """Sets the threshold for the CLI logger to `level`. Setting it to `None` disables
    CLI logging.

    >>> set_cli_level("DEBUG")
    >>> set_cli_level(logging.INFO)
    >>> set_cli_level(None)
    """
    # Disabling CLI logging is done by setting the handler's enabled attribute to False,
    # not removing the handler itself. If we did so, the default "lastResort" handler
    # would be used instead.
    global __cli_handler

    if level is None:
        __cli_handler.enabled = False
    else:
        __cli_handler.enabled = True
        __cli_handler.setLevel(level)


def _remove_file_handler() -> None:
    global __file_handler

    if __file_handler:
        __file_handler.console.file.close()
        _get_root_logger().removeHandler(__file_handler)
        __file_handler = None


def set_level(level: int | str | None) -> None:
    """Sets the threshold for the file logger to `level`. Setting it to `None` disables
    file logging.

    >>> set_level("DEBUG")
    >>> set_level(logging.INFO)
    >>> set_level(None)
    """
    if level is None:
        return _remove_file_handler()

    # If the file logger is not set yet, we set it to /dev/null so that we can set its
    # level without creating a file
    if not __file_handler:
        set_file(os.devnull)

    __file_handler.setLevel(level)


def set_file(file: str | IO[str] | None) -> None:
    """Set the location of the log file.

    Args:
        file: The path to the log file or a file object. Setting it to `None` disables
            file logging.

    Example:

        >>> logging.set_file('/tmp/test.log')
        >>> logging.set_file(open('/tmp/test2.log', 'a+'))
        >>> logging.set_file(None)
    """
    global __file_handler

    if file is None:
        return _remove_file_handler()

    if isinstance(file, str):
        file = open(file, "a+")

    # Create a new handler if none exist
    if __file_handler is None:
        console = Console(file=file, color_system="truecolor", width=FILE_CONSOLE_WIDTH)
        __file_handler = RichHandler(console=console)
        __file_handler.setLevel(DEFAULT_FILE_LEVEL)
        _get_root_logger().addHandler(__file_handler)
    # Change the file of the already existing one
    else:
        old_file = __file_handler.console.file
        __file_handler.console.file = file
        old_file.close()


def _get_root_logger() -> Logger:
    return logger(None)


def _define_log_level(levelName, levelNum, methodName=None):
    """Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    Source: https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945
    """
    if not methodName:
        methodName = levelName.lower()

    # Removed checks as we only call this function with unique, constant level names
    # if hasattr(logging, levelName):
    #     raise AttributeError(f"{levelName} already defined in logging module")
    # if hasattr(logging, methodName):
    #     raise AttributeError(f"{methodName} already defined in logging module")
    # if hasattr(logging.getLoggerClass(), methodName):
    #     raise AttributeError(f"{methodName} already defined in logger class")

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)


# Create logging levels

_define_log_level("SUCCESS", 25)
_define_log_level("FAILURE", 26)
_define_log_level("TRACE", 9)


class TenLogger(logging.Logger):
    """A logger class that adds convenience methods for logging at the new levels."""

    def trace(self, msg, *args, **kwargs) -> None:
        if self.isEnabledFor(TRACE):
            self._log(TRACE, msg, args, **kwargs)

    def success(self, msg, *args, **kwargs) -> None:
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kwargs)

    def failure(self, msg, *args, **kwargs) -> None:
        if self.isEnabledFor(FAILURE):
            self._log(FAILURE, msg, args, **kwargs)


logging.setLoggerClass(TenLogger)

# Reference logging levels

# Original
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

# Added
SUCCESS = logging.SUCCESS
FAILURE = logging.FAILURE
TRACE = logging.TRACE

# Kill urllib3's HTTPs logging

logging.getLogger("urllib3").setLevel(logging.ERROR)

# Add our default handler

logging.basicConfig(level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[])

_create_cli_handler()

log = logger()

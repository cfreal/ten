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

import logging
from typing import IO
from logging import Handler, Logger

from rich.console import Console
from rich.logging import RichHandler

from tenlib.config import config

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

__cli_handler: Handler = None
__file_handler: Handler = None


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

    if hasattr(logging, levelName):
        raise AttributeError(f"{levelName} already defined in logging module")
    if hasattr(logging, methodName):
        raise AttributeError(f"{methodName} already defined in logging module")
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError(f"{methodName} already defined in logger class")

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


def logger(name="ten") -> Logger:
    """Return a logger with the specified name or, if name is None, return a
    logger which is the root logger of the hierarchy.
    """
    return logging.getLogger(name)


def set_cli_level(level):
    """Sets the threshold for the CLI logger to `level`."""
    if not __cli_handler:
        _create_default_cli_handler()
    __cli_handler.setLevel(level)


def set_level(level):
    """Sets the threshold for the file logger to `level`."""
    if not __file_handler:
        _create_default_file_handler()

    __file_handler.setLevel(level)


def set_file(file: str | IO[str]) -> None:
    """Set the location of the log file.

    Example:

        >>> logging.set_file('/tmp/test.log')
        >>> logging.set_file(open('/tmp/test2.log', 'a+'))
    """
    if not __file_handler:
        _create_default_file_handler()

    if isinstance(file, str):
        file = open(file, "w")

    old_file = __file_handler.console.file
    __file_handler.console.file = file
    old_file.close()


def _get_root_logger() -> Logger:
    return logger(None)


def _set_cli_handler(handler: Handler):
    global __cli_handler

    __cli_handler = __replace_handler(__cli_handler, handler, logging.CRITICAL)


def _set_file_handler(handler: Handler):
    global __file_handler

    __file_handler = __replace_handler(__file_handler, handler, logging.DEBUG)


def __replace_handler(old_handler: Handler, handler: Handler, default_level) -> Handler:
    """Replaces previous handler with new one. If there was no handler, set the
    log level to `default_level`.
    """
    root_logger = _get_root_logger()

    if old_handler:
        level = old_handler.level
        root_logger.removeHandler(old_handler)
    else:
        level = default_level

    handler.setLevel(level)
    root_logger.addHandler(handler)

    return handler


def _create_default_cli_handler():
    console = Console(stderr=True)
    handler = RichHandler(console=console)
    _set_cli_handler(handler)


def _create_default_file_handler():
    file = open(config.log_file, "a+")
    console = Console(file=file, color_system="truecolor")
    handler = RichHandler(console=console)
    _set_file_handler(handler)


# Create logging levels

_define_log_level("SUCCESS", 25)
_define_log_level("FAILURE", 26)
_define_log_level("TRACE", 11)

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

_create_default_file_handler()

log = logger("ten")

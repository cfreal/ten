"""This module provides different styles to display `msg_*` messages.

See `tenlib.flow.msg_info` to check the display functions, and
`tenlib.flow.set_message_formatter` to change the display style.
"""

from abc import ABC, abstractmethod
from enum import Enum
from tenlib.flow.console import get_console
from rich.console import Console


__all__ = [
    "MessageFormatter",
    "NewschoolMessageFormatter",
    "OldschoolMessageFormatter",
    "OtherOldschoolMessageFormatter",
    "SlickMessageFormatter",
    "CircleMessageFormatter",
    "IconMessageFormatter",
    "BackgroundMessageFormatter",
]


class MessageFormatter(ABC):
    """Wrapper to display information in a pretty way.

    The list of possible calls is as follows:

    * `MessageFormatter.info`
    * `MessageFormatter.success`
    * `MessageFormatter.failure`
    * `MessageFormatter.error`
    * `MessageFormatter.warning`
    * `MessageFormatter.debug`
    """

    CLEAR_LINE = "\r\x1b[K"

    def __init__(self, *, console: Console = None):
        """
        Params:
            console: Console to write to.
        """
        self._console = console

    @property
    def console(self) -> Console:
        return self._console or get_console()

    def _output(self, *objects, **kwargs) -> None:
        self.console.print(*objects, **kwargs)

    def print(self, *objects, **kwargs) -> None:
        """Displays a message."""
        return self._output(*objects, **kwargs)

    def bin_print(self, data: bytes) -> None:
        """Prints binary `data` and flushes the stream.

        Args:
            data (bytes)
        """
        try:
            self.console.file.buffer.write(data)
        except TypeError:
            raise TypeError("MessageFormatter.bin_print() expects a byte-like object")
        self.console.file.buffer.flush()

    @abstractmethod
    def info(self, *objects, **kwargs) -> None:
        """Displays an information message."""

    @abstractmethod
    def warning(self, *objects, **kwargs) -> None:
        """Displays a warning message."""

    @abstractmethod
    def error(self, message, **kwargs) -> None:
        """Displays an error message."""

    @abstractmethod
    def success(self, message, **kwargs) -> None:
        """Displays a success message."""

    @abstractmethod
    def failure(self, message, **kwargs) -> None:
        """Displays a failure message."""

    @abstractmethod
    def debug(self, message, **kwargs) -> None:
        """Displays a debug message."""

    def clear(self) -> None:
        """Clears last line."""
        self.console.file.write(self.CLEAR_LINE)


class Status(Enum):
    INFO = 1
    SUCCESS = 2
    FAILURE = 3
    ERROR = 4
    WARNING = 5
    DEBUG = 6


class PrefixMessageFormatter(MessageFormatter):
    """Displays a prefix indicating the status of the message."""

    # Prefix to add to the message
    _PREFIX = {
        Status.INFO: "[b blue]*[/]",
        Status.FAILURE: "[b red]-[/]",
        Status.ERROR: "[b red]x[/]",
        Status.SUCCESS: "[b green]+[/]",
        Status.WARNING: "[b yellow]![/]",
        Status.DEBUG: "[b magenta]D[/]",
    }
    # Styles to apply to the whole message
    _STYLES = {
        Status.INFO: None,
        Status.FAILURE: None,
        Status.ERROR: None,
        Status.SUCCESS: None,
        Status.WARNING: None,
        Status.DEBUG: None,
    }

    def _status(self, status: Status, *objects, **kwargs):
        """Displays a message along with a status.
        Arguments of the format string will be colored in a color indicating the
        status. For instance, arguments for the success function will be in
        green, and failure in red.
        """
        return self._output(
            self._PREFIX[status], *objects, style=self._STYLES[status], **kwargs
        )

    def info(self, *objects, **kwargs):
        self._status(Status.INFO, *objects, **kwargs)

    def warning(self, *objects, **kwargs):
        self._status(Status.WARNING, *objects, **kwargs)

    def error(self, *objects, **kwargs):
        self._status(Status.ERROR, *objects, **kwargs)

    def success(self, *objects, **kwargs):
        self._status(Status.SUCCESS, *objects, **kwargs)

    def failure(self, *objects, **kwargs):
        self._status(Status.FAILURE, *objects, **kwargs)

    def debug(self, *objects, **kwargs):
        self._status(Status.DEBUG, *objects, **kwargs)

    def clear(self):
        """Clears last line."""
        self.console.file.write(self.CLEAR_LINE)


class SlickMessageFormatter(PrefixMessageFormatter):
    """Status is indicated as a colored pipe at the beginning of every line.

    Examples:
        >>> o = SlickMessageFormatter()
        >>> o.info('Something')
        | Something
    """

    _PREFIX = {
        Status.INFO: "[b blue]|[/]",
        Status.FAILURE: "[b red]|[/]",
        Status.ERROR: "[b red]|[/]",
        Status.SUCCESS: "[b green]|[/]",
        Status.WARNING: "[b yellow]|[/]",
        Status.DEBUG: "[b magenta]|[/]",
    }


class OldschoolMessageFormatter(PrefixMessageFormatter):
    """Status is indicated as `[+]`, `[-]`, `[*]`, etc. at the beginning of
    every line, with the icon colored.

    Examples:
        >>> o = OtherOldschoolMessageFormatter()
        >>> o.info('Something')
        [*] Something
        >>> o.success('Something else')
        [+] Something else
    """

    _PREFIX = {
        Status.INFO: "[[blue]*[/]]",
        Status.FAILURE: "[[red]-[/]]",
        Status.ERROR: "[[red]x[/]]",
        Status.SUCCESS: "[[green]+[/]]",
        Status.WARNING: "[[yellow]![/]]",
        Status.DEBUG: "[[magenta]D[/]]",
    }


class OtherOldschoolMessageFormatter(PrefixMessageFormatter):
    """Status is indicated as `[+]`, `[-]`, `[*]`, etc. at the beginning of
    every line, colored and bold.

    Examples:
        >>> o = OldschoolMessageFormatter()
        >>> o.info('Something')
        [i] Something
        >>> o.success('Something else')
        [+] Something else
    """

    _PREFIX = {
        Status.INFO: "[b blue]\[*][/]",
        Status.FAILURE: "[b red]\[-][/]",
        Status.ERROR: "[b red]\[x][/]",
        Status.SUCCESS: "[b green]\[+][/]",
        Status.WARNING: "[b yellow]\[!][/]",
        Status.DEBUG: "[b magenta]\[D][/]",
    }


class NewschoolMessageFormatter(PrefixMessageFormatter):
    """Status is be indicated as a colored symbol at the beginning of every
    line. Requires UTF-8.

    Examples:
        >>> o = NewschoolOutput()
        >>> o.info('Something')
        · Something
        >>> o.success('Success')
        ✔ Success
        >>> o.failure('Failure')
        ✖ Failure
        >>> o.print('test')
         test
    """

    _PREFIX = {
        Status.INFO: "[b blue]·[/]",
        Status.FAILURE: "[b red]✖[/]",
        Status.ERROR: "[b red]✖[/]",
        Status.SUCCESS: "[b green]✔[/]",
        Status.WARNING: "[b yellow]▲[/]",
        Status.DEBUG: "[b magenta]⊙[/]",
    }


class IconMessageFormatter(PrefixMessageFormatter):
    """Status is be indicated as a colored symbol at the beginning of every
    line. Requires UTF-8.

    Examples:
        >>> o = NewschoolOutput()
        >>> o.info('Something')
         ·  Something
        >>> o.success('Success')
         ✔  Success
        >>> o.failure('Failure')
         ✖  Failure
        >>> o.print('test')
        test
    """

    _PREFIX = {
        Status.INFO: "[b blue on black] · [/]",
        Status.FAILURE: "[b red on black] ✖ [/]",
        Status.ERROR: "[b red on black] ✖ [/]",
        Status.SUCCESS: "[b green on black] ✔ [/]",
        Status.WARNING: "[b yellow on black] ▲ [/]",
        Status.DEBUG: "[b magenta on black] ⊙ [/]",
    }


class CircleMessageFormatter(MessageFormatter):
    """Status is be indicated as a colored circle at the beginning of every
    line. Requires UTF-8.
    """

    _PREFIX = {
        Status.INFO: "[b blue]·[/]",
        Status.FAILURE: "[b red]·[/]",
        Status.ERROR: "[b red]·[/]",
        Status.SUCCESS: "[b green]·[/]",
        Status.WARNING: "[b yellow]·[/]",
        Status.DEBUG: "[b magenta]·[/]",
    }


class BackgroundMessageFormatter(MessageFormatter):
    """Status is be indicated as a symbol, and the background of the whole line
    will be colored. Requires UTF-8.
    """

    _FORMAT = {
        Status.INFO: "·",
        Status.FAILURE: "✖",
        Status.ERROR: "✖",
        Status.SUCCESS: "✔",
        Status.WARNING: "▲",
        Status.DEBUG: "⊙",
    }

    _STYLES = {
        Status.INFO: "on blue",
        Status.FAILURE: "on red",
        Status.ERROR: "on red",
        Status.SUCCESS: "on green",
        Status.WARNING: "on yellow",
        Status.DEBUG: "on magenta",
    }

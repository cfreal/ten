"""This module provides different styles to display `msg_*` messages.

See `tenlib.flow.msg_info` to check the display functions, and
`tenlib.flow.set_message_formatter` to change the display style.
"""

from tenlib.flow.console import get_console
from rich.console import Console


__all__ = [
    "MessageFormatter",
    "NewschoolMessageFormatter",
    "OldschoolMessageFormatter",
    "SlickMessageFormatter",
    "CircleMessageFormatter",
    "BackgroundMessageFormatter",
]


class MessageFormatter:
    """Wrapper to display information in a pretty way.
    When displaying a message, a status, a format string and its parameters must
    be given. A few stati are available: `INFO`, `SUCCESS`, `ERROR`, `WARNING`,
    `DEBUG`. The status will be prepended to the displayed line, and every
    parameter of a format string will be colored.

    This message formatter displays a colored character indicating the status at
    the beginning of every line: `+` for success, `-` for failure, `i` for
    information, etc.

    The list of possible calls is as follows:

    * `MessageFormatter.info`
    * `MessageFormatter.success`
    * `MessageFormatter.failure`
    * `MessageFormatter.error`
    * `MessageFormatter.warning`
    * `MessageFormatter.debug`
    """

    _INFO = "INFO"
    _SUCCESS = "SUCCESS"
    _FAILURE = "FAILURE"
    _ERROR = "ERROR"
    _WARNING = "WARNING"
    _DEBUG = "DEBUG"

    _FORMAT = {
        "INFO": "[b blue]*[/] {}",
        "FAILURE": "[b red]-[/] {}",
        "ERROR": "[b red]x[/] {}",
        "SUCCESS": "[b green]+[/] {}",
        "WARNING": "[b yellow]![/] {}",
        "DEBUG": "[b magenta]D[/] {}",
    }

    CLEAR_LINE = "\r\x1b[K"

    def __init__(self, *, console: Console = None):
        """
        Params:
            console: Console to write to.
        """
        self._console = console

    @property
    def console(self):
        return self._console or get_console()

    def _output(self, message, **kwargs):
        self.console.print(message, **kwargs)

    def print(self, message="", **kwargs):
        """Displays a message."""
        return self._output(message, **kwargs)

    def bin_print(self, data: bytes):
        """Prints binary `data` and flushes the stream.

        Args:
            data (bytes)
        """
        try:
            self.console.file.buffer.write(data)
        except TypeError:
            raise TypeError("MessageFormatter.bin_print() expects a byte-like object")
        self.console.file.buffer.flush()

    def status(self, status, message, **kwargs):
        """Displays a message along with a status.
        Arguments of the format string will be colored in a color indicating the
        status. For instance, arguments for the success function will be in
        green, and failure in red.
        """
        return self._output(self._FORMAT[status].format(message), **kwargs)

    def info(self, message, **kwargs):
        self.status(self._INFO, message, **kwargs)

    def warning(self, message, **kwargs):
        self.status(self._WARNING, message, **kwargs)

    def error(self, message, **kwargs):
        self.status(self._ERROR, message, **kwargs)

    def success(self, message, **kwargs):
        self.status(self._SUCCESS, message, **kwargs)

    def failure(self, message, **kwargs):
        self.status(self._FAILURE, message, **kwargs)

    def debug(self, message, **kwargs):
        self.status(self._DEBUG, message, **kwargs)

    def clear(self):
        """Clears last line."""
        self.console.file.write(self.CLEAR_LINE)


class SlickMessageFormatter(MessageFormatter):
    """Status is indicated as a colored pipe at the beginning of every line.

    Examples:
        >>> o = SlickOutput()
        >>> o.info('Something')
        | Something
    """

    _FORMAT = {
        "INFO": "[b blue]|[/] {}",
        "FAILURE": "[b red]|[/] {}",
        "ERROR": "[b red]|[/] {}",
        "SUCCESS": "[b green]|[/] {}",
        "WARNING": "[b yellow]|[/] {}",
        "DEBUG": "[b magenta]|[/] {}",
    }


class OldschoolMessageFormatter(MessageFormatter):
    """Status is indicated as `[+]`, `[-]`, `[i]`, etc. at the beginning of
    every line.

    Examples:
        >>> o = OldSchoolOutput()
        >>> o.info('Something')
        [i] Something
        >>> o.success('Something else')
        [+] Something else
    """

    _FORMAT = {
        "INFO": "[[blue]*[/]] {}",
        "FAILURE": "[[red]-[/]] {}",
        "ERROR": "[[red]x[/]] {}",
        "SUCCESS": "[[green]+[/]] {}",
        "WARNING": "[[yellow]![/]] {}",
        "DEBUG": "[[magenta]D[/]] {}",
    }


class NewschoolMessageFormatter(MessageFormatter):
    """Status is be indicated as a colored symbol at the beginning of every
    line. Requires UTF-8.

    Examples:
        >>> o = NewschoolOutput()
        >>> o.info('Something')
        » Something
        >>> o.success('Success')
        ✔ Success
        >>> o.failure('Failure')
        ✖ Failure
        >>> o.print('test')
         test
    """

    _FORMAT = {
        "INFO": "[b blue]·[/] {}",
        "FAILURE": "[b red]✖[/] {}",
        "ERROR": "[b red]✖[/] {}",
        "SUCCESS": "[b green]✔[/] {}",
        "WARNING": "[b yellow]▲[/] {}",
        "DEBUG": "[b magenta]⊙[/] {}",
    }


class CircleMessageFormatter(MessageFormatter):
    """Status is be indicated as a colored circle at the beginning of every
    line. Requires UTF-8.
    """

    _FORMAT = {
        "INFO": "[b blue]·[/] {}",
        "FAILURE": "[b red]·[/] {}",
        "ERROR": "[b red]·[/] {}",
        "SUCCESS": "[b green]·[/] {}",
        "WARNING": "[b yellow]·[/] {}",
        "DEBUG": "[b magenta]·[/] {}",
    }


class BackgroundMessageFormatter(MessageFormatter):
    """Status is be indicated as a symbol, and the background of the whole line
    will be colored. Requires UTF-8.
    """

    _FORMAT = {
        "INFO": "[on blue]· {}[/]",
        "FAILURE": "[on red]✖ {}[/]",
        "ERROR": "[on red]✖ {}[/]",
        "SUCCESS": "[on green]✔ {}[/]",
        "WARNING": "[on yellow]▲ {}[/]",
        "DEBUG": "[on magenta]⊙ {}[/]",
    }

"""Holds the general configuration.
"""
# TODO Get config values from ~/ten.conf
# TODO Disallow editing properly

__all__ = [
    "config",
    "Configuration",
]


from typing import NoReturn


class Configuration:
    BURP_PROXY: str = "http://localhost:8080"
    """Proxy to use when calling `tenlib.http.Session.burp()`."""
    MESSAGE_FORMATTER: str = "OtherOldschoolMessageFormatter"
    """Default message formatter, or `None` to randomize."""
    OPEN_SCRIPT_COMMAND: tuple[str, ...] = None
    """Command to run to open a file when calling the `ten` utility, or `None` to use
    the default behaviour.
    """
    LOG_LINE_WIDTH: int = 200
    """Number of characters to display per line in the log file."""

    def __setattribute__(self) -> NoReturn:
        raise AttributeError(
            "Configuration attributes cannot be changed programmatically"
        )


config = Configuration()

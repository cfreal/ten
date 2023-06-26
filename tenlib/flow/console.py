"""Stores the console object used by ten.
"""

from rich.console import Console


__all__ = ["get_console"]

__console = None


def get_console() -> Console:
    """Returns the underlying rich console."""
    global __console
    if not __console:
        __console = Console(highlight=False, emoji=False, markup=True)
    return __console

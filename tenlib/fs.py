r"""Classes and function related to the filesystem (FS).
Heavily based on `pathlib`, this submodule overrides some methods to allow
easier and faster scripting.

Examples:

    For simple operations, use the function wrappers, such as:

        >>> read_text('/tmp/file.txt')
        'contents of file'
        >>> read_bytes('/tmp/file.txt')
        b'contents of file'
        >>> # The write method supports both bytes and str.
        >>> write('/tmp/file.txt', 'new contents')
        >>> write('/tmp/file.txt', b'new contents in bytes')
        >>> exists('/tmp/other_file.txt')
        False

    Otherwise, you can use the `tenlib.fs.Path` class:

        >>> p = Path('/tmp/random_dir/file.txt')
        >>> p.exists()
        False
        >>> # Creates the file, and superdirectories if required
        >>> p.touch(dirs=True)
        >>> p.exists()
        True
        >>> p.write('some contents\n')
        >>> p.append('additional contents')
        >>> p.read_text()
        'some_contents\nadditional contents'

    You can handle directories using the standard `pathlib` API:

        >>> p = Path('/tmp/')
        >>> p2 = p / 'sub_directory'
        >>> list(p2.glob('**/*.py'))
        [
            fs.Path('/tmp/sub_directory/file1.py'),
            fs.Path('/tmp/sub_directory/dir/file2.py'),
            fs.Path('/tmp/sub_directory/file3.py')
        ]

"""

from __future__ import annotations

import functools
import pathlib


__all__ = [
    "Path",
    "read_text",
    "read_bytes",
    "mkdir",
    "exists",
    "write",
]

StrOrBytes = bytes | str


# TODO Make window compatible
class Path(pathlib.PosixPath):
    """Wrapper around `pathlib.Path` that provides a few extra functions."""

    def write(self, data: StrOrBytes) -> int:
        """Writes `data` to file.

        Args:
            data (str, bytes): Data to write in the file
        """

        if isinstance(data, (bytes, bytearray)):
            return self.write_bytes(data)
        else:
            return self.write_text(data)

    def append(self, data: StrOrBytes) -> int:
        """Append `data` to file.

        Args:
            data (str, bytes): Data to append to the file
        """
        mode = isinstance(data, (bytes, bytearray)) and "ab" or "a"
        with self.open(mode=mode) as f:
            return f.write(data)

    def touch(
        self, mode: int = 0o666, exist_ok: bool = True, parents: bool = False
    ) -> Path:
        """Wrapper for `Path.touch` that returns the instance, and creates sub-
        directories if `parents` is set (default: `False`).

        Returns:
            itself
        """
        if parents:
            self.parent.mkdir(parents=True, exist_ok=True)
        super().touch(mode, exist_ok)
        return self

    def ptouch(self, mode: int = 0o666, exist_ok: bool = True) -> Path:
        """Wrapper for `Path.touch` that creates every sub directory.

        Returns:
            itself
        """
        return self.touch(mode, exist_ok, parents=True)


# Wrappers


def read_text(path: str) -> str:
    """Returns the contents of file `path` as `str`."""
    return _to_path(path).read_text()


def read_bytes(path: str) -> bytes:
    """Returns the contents of file `path` as `bytes`."""
    return _to_path(path).read_bytes()


def mkdir(
    path: str, mode: int = 0o777, parents: bool = False, exist_ok: bool = False
) -> Path:
    """Creates a directory `path`."""
    return _to_path(path).mkdir(mode, parents, exist_ok)


def exists(path: str) -> bool:
    """Returns whether file `path` exists."""
    return _to_path(path).exists()


def write(path: str, data: StrOrBytes) -> Path:
    """Writes `data` to file `path`.

    Args:
        path (str): Path to the file
        data (str, bytes): Data to write in the file
    """
    return _to_path(path).write(data)


def wrapper_read(function):
    """Returns a function which, instead of reading data from the first
    parameter, reads data from a file.
    """

    @functools.wraps(function)
    def read_function(path, *args, **kwargs):
        data = read_bytes(path)
        return function(data, *args, **kwargs)

    return read_function


def wrapper_write(function):
    """Returns a function which writes data to a file instead of returning it."""

    @functools.wraps(function)
    def write_function(path, data, *args, **kwargs):
        data = function(data, *args, **kwargs)
        return write(path, data)

    return write_function


def _to_path(path) -> Path:
    if isinstance(path, Path):
        return path
    return Path(path)

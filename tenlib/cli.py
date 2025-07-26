"""CLI tools for ten.
"""

import platform
import sys
from typing import NoReturn

from ten import *
from tenlib.struct.proxy import TenDict, TenList
from tenlib.config import config


@entry
@arg("transforms", "Transforms to apply")
@arg("python", "If set, data is displayed as python code")
@arg("keep_newline", "If not set, the last newline of the input is removed")
def transform(
    *transforms: str, python: bool = False, keep_newline: bool = False
) -> None:
    """Applies one or several transforms from the transform module of ten.

    Examples:

        $ echo -n 'a=3&b=2' | tf qs.parse json.encode
        {"a": "3", "b": "2"}
        $ echo -n 'a=3&b=2' | tf qs.parse json.encode -p
        '{"a": "3", "b": "2"}'
        $ cat /etc/passwd | tf base64.encode
        cm9vdDp4OjA6MDpyb290Oi9yb290Oi9iaW4vYmFzaApkYWVtb24...
    """
    data = sys.stdin.buffer.read()
    if not keep_newline and data.endswith(b"\n"):
        data = data[:-1]

    for modfunc in transforms:
        module, func = modfunc.split(".")

        instance = getattr(tf, module, None)

        if not instance:
            return msg_error(f"Unknown module [red]{module}")

        instance = getattr(instance, func, None)

        if not instance:
            return msg_error(f"Unknown transform [red]{module}.{func}")

        data = instance(data)

    if python:
        pprint(data)
    elif isinstance(data, bytes):
        sys.stdout.buffer.write(data)
    elif isinstance(data, str):
        print(data)
    else:
        if isinstance(data, TenDict):
            data = data.__wo__
        if isinstance(data, TenList):
            data = data.data
        pprint(data, indent=4)


PATTERN = """\
#!/usr/bin/env python3

from ten import *


@entry
def main():
    ...


main()
"""


def _get_program_path(program: str) -> str | None:
    """Checks if a program exists in the system's PATH and returns its full path."""
    paths = (
        os.path.join(path, program) for path in os.environ["PATH"].split(os.pathsep)
    )
    return next((p for p in paths if os.access(p, os.X_OK)), None)


def _linux_open(path: str) -> None | NoReturn:
    """Opens a file in the default application on Linux."""

    if "DISPLAY" in os.environ and (editor := _get_program_path("xdg-open")):
        options = ()
    elif editor := _get_program_path("editor"):
        options = ("--",)
    elif "EDITOR" in os.environ:
        editor = os.environ["EDITOR"]
        options = ("--",)

    if editor:
        os.execv(editor, (editor,) + options + (path,))
    # else:
    # msg_error("No suitable program found to open the file.")


@entry
@arg("filename", "File to create")
def ten(filename: str, force: bool = False) -> None:
    """Creates a new ten script and opens it.

    If the file already exists, it will not be overwritten, unless you specify the
    `--force` option.
    """

    path = Path(filename)

    if not force and path.exists():
        msg_info("File exists")
    else:
        path.write(PATTERN)
        path.chmod(0o740)

    if config.OPEN_SCRIPT_COMMAND is not None:
        shell.call(config.OPEN_SCRIPT_COMMAND + (str(path),))
        return

    match platform.system():
        case "Windows":
            pass
        case "Linux":
            _linux_open(path)
        case "Darwin":
            shell.call(("open", str(path)))

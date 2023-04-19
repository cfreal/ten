"""This module allows you to run commands. The functions are simple wrappers for 
`subprocess.Popen`.
"""

from subprocess import PIPE, STDOUT, Popen

__all__ = ["background", "call", "get_output", "PIPE", "STDOUT", "Popen"]


def _cmd_as_argv(cmd: list[str] | str) -> list[str]:
    if isinstance(cmd, str):
        return ["/bin/sh", "-c", cmd]
    return cmd


def background(cmd: str | list[str], **kwargs) -> Popen:
    """Runs process in the background."""
    return Popen(_cmd_as_argv(cmd), **kwargs)


def call(cmd: str | list[str], **kwargs) -> Popen:
    """Runs process to completion. Stores the output (stdout, stderr).

    >>> p = shell.call("ls -alh")
    >>> stdout = p.stdout.read()
    """
    kwargs["stdout"] = PIPE
    kwargs["stderr"] = PIPE
    process = Popen(_cmd_as_argv(cmd), **kwargs)
    process.wait()
    return process


def get_output(
    cmd: str | list[str], text: bool = True, **kwargs
) -> tuple[str | bytes, str | bytes]:
    """Returns the output of the process.

    Args:
        cmd: Command to execute
        text: If True (default), return result as `str`. Otherwise, `bytes`.
        kwargs: extra arguments for `subprocess.Popen`

    Returns:
        tuple[str | bytes, str | bytes]: stdout and stderr, as str or bytes.
    """
    kwargs["text"] = text
    process = call(cmd, **kwargs)
    stdout = process.stdout.read()
    stderr = process.stderr.read()
    process.stdout.close()
    process.stderr.close()
    return stdout, stderr


def escape(cmd: str) -> str:
    """Escapes an argument for a shell command.

    Example:

        >>> shell.escape("abc'def")
        "'abc'\''def'"
    """
    return "'" + cmd.replace("'", "'\\''") + "'"

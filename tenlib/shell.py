"""This module allows you to run commands. The functions are simple wrappers for 
`subprocess.Popen`.


If you want to obtain the output of a command, use `output`:

```
>>> stdout, stderr = shell.output("ls -alh")
```

If you're not interested in the output and just want to run a command, use `call`:

```
>>> process = shell.call("sleep 3")
```

Finally, to get a `Popen` object and have the process run in the background, use
`process`:

```
>>> process = shell.process("/bin/process")
>>> process.stdin.write(b"hi\\n")
>>> process.stdout.read()
b"hello!\\n"
>>> process.stdin.close()
>>> process.wait()
```

"""

from subprocess import PIPE, STDOUT, Popen, TimeoutExpired

__all__ = ["process", "call", "output", "PIPE", "STDOUT", "Popen"]


def _is_shell(cmd: list[str] | str) -> bool:
    return isinstance(cmd, str)


def _pipe_maybe(kwargs) -> None:
    for key in ["stdin", "stdout", "stderr"]:
        kwargs.setdefault(key, PIPE)


def process(command: str | list[str], **kwargs) -> Popen:
    """Runs process in the background.

    Args:
        command: Command to execute
        kwargs: extra arguments for `subprocess.Popen`
    """
    _pipe_maybe(kwargs)
    return Popen(command, shell=_is_shell(command), **kwargs)


def _execute_process(
    command: str | list[str], timeout: int, **kwargs
) -> tuple[Popen, str | bytes, str | bytes]:
    """Creates a process and waits for it to finish, or a timeout to occur.
    If a timeout occurs, the process is killed, waited for, and the exception is raised.
    """
    p = process(command, **kwargs)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except TimeoutExpired:
        p.stderr.close()
        p.stdout.close()
        p.kill()
        p.wait()
        raise

    return p, stdout, stderr


def call(command: str | list[str], timeout: int = None, **kwargs) -> Popen:
    """Runs process to completion. The output (stdout and stderr) is discarded.

    Args:
        command: Command to execute
        timeout: If the process does not terminate after timeout seconds, raises a
            `TimeoutExpired` exception.
        kwargs: extra arguments for `subprocess.Popen`

    >>> p = shell.call("ls -alh")
    >>> stdout = p.stdout.read()
    """
    process, _, _ = _execute_process(command, **kwargs, timeout=timeout)
    return process


def output(
    command: str | list[str], text: bool = True, timeout: int = None, **kwargs
) -> tuple[str | bytes, str | bytes]:
    """Returns the output of the process.

    Args:
        command: Command to execute
        text: If True (default), return result as `str`. Otherwise, `bytes`.
        timeout: If the process does not terminate after timeout seconds, raises a
            `TimeoutExpired` exception.
        kwargs: extra arguments for `subprocess.Popen`

    Returns:
        tuple[str | bytes, str | bytes]: stdout and stderr, as str or bytes.
    """
    _, stdout, stderr = _execute_process(command, **kwargs, timeout=timeout, text=text)
    return stdout, stderr


def escape(cmd: str) -> str:
    """Escapes an argument for a shell command. This is only compatible with linux.

    Example:

        >>> shell.escape("abc'def")
        "'abc'\''def'"
    """
    return "'" + cmd.replace("'", "'\\''") + "'"

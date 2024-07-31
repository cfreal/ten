"""Main input/output functions.

Here's a base `ten` python file layout: 

```python
#!/usr/bin/env python

from ten import *


@entry
def main():
    ...


main()
```

The main coroutine's parameters are automatically mapped to a `argparse`
argument (see `entry`).

To display messages, use `msg_*` functions (`msg_info` or `msg_success` for
instance).

If you script fails, you can stop the execution at any time using `leave`,
`failure` or `error`. Additionally, use `assume` to ensure a condition is valid.
If it is not, the script will exit.

Execution can be paused using `pause`, or delayed using `sleep`.

To inform the user of progress in real time, use `msg_status`, `progress`, or
`track`, or use the `inform` decorator.

Most of the heavy lifting for display is done by the 
[`rich` library](https://rich.readthedocs.io/en/stable/).
"""

import random
import argparse
import functools
import inspect
import re
from types import SimpleNamespace, NoneType
from typing import (
    Callable,
    Type,
    Optional,
    Iterable,
    NoReturn,
    Any,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
import time

from rich.text import Text, TextType
from rich.console import RenderableType
from rich.progress import (
    Progress,
    ProgressColumn,
    filesize,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.prompt import Prompt
from rich.status import Status

from tenlib import logging
from tenlib.flow.console import get_console
from tenlib.flow import messageformatter
from tenlib.config import config
from tenlib.exception import TenError, TenExit, TenFailure

__all__ = [
    "entry",
    "arg",
    "msg_info",
    "msg_failure",
    "msg_error",
    "msg_success",
    "msg_warning",
    "msg_print",
    "msg_debug",
    "msg_clear",
    "msg_status",
    "bin_print",
    "leave",
    "failure",
    "error",
    "assume",
    "inform",
    "pause",
    "sleep",
    "progress",
    "track",
    "ask",
    "trace",
    "set_message_formatter",
    "set_random_message_formatter",
]

__message_formatter: messageformatter.MessageFormatter = None

try:
    import rich_argparse
except ImportError:
    __ARGPARSE_FORMATTER = argparse.RawDescriptionHelpFormatter
else:
    __ARGPARSE_FORMATTER = rich_argparse.RawDescriptionRichHelpFormatter


def entry(entrypoint: Callable | Type) -> Callable[[], None]:
    """Converts the given coroutine or class into the program's entry point.
    Command line arguments are mapped to the parameters of the function or the object's
    `__init__`. Also, `tenlib.exception.TenExit` and `KeyboardInterrupt` exceptions will
    be caught and displayed nicely.

    Default values, as well as type hinting, are supported.

    The generic look of the program with a coroutine is:

    ```python
    #!/usr/bin/env python3
    from ten import *

    @entry
    def main():
        ...

    main()
    ```

    And with a class:

    ```python
    #!/usr/bin/env python3
    from ten import *

    @entry
    class Program:
        def __init__(self, ...):
            ...

        def run(self):
            ...

    Program()
    ```

    Examples:

        Creating a script with 1 required parameter, and 2 optional
        parameters:


            #!/usr/bin/env python3

            from ten import *

            @entry
            def exploit(url, username='admin', password='password'):
                \"""Exploits a post-authentication vulnerability on given URL.
                \"""
                msg_info(f'URL: {url}')
                msg_info(f'Username: {username}')
                msg_info(f'Password: {password}')
                ...

            exploit()

        Running the script:

            $ /tmp/exploit.py -h
            usage: boo.py [-h] [-u USERNAME] [-p PASSWORD] url

            Exploits a post-authentication vulnerability on given URL.

            positional arguments:
            url

            optional arguments:
            -h, --help            show this help message and exit
            -u USERNAME, --username USERNAME
            -p PASSWORD, --password PASSWORD
            $ /tmp/exploit.py 'http://target.com'
            ⊙ URL: http://target.com
            ⊙ Username: admin
            ⊙ Password: password
            $ /tmp/exploit.py 'http://target.com' -u user1000
            ⊙ URL: http://target.com
            ⊙ Username: user1000
            ⊙ Password: password
            $

        Alternatively, with a class:

            #!/usr/bin/env python3

            from ten import *

            @entry
            class Exploit:
                def __init__(self, url, username='admin', password='password'):
                    self.url = url
                    self.username = username
                    self.password = password

                def run(self):
                    msg_info(f'URL: {self.url}')
                    msg_info(f'Username: {self.username}')
                    msg_info(f'Password: {self.password}')
                    ...

            Exploit()

        Other supported functions declaration:

            @entry
            def exploit(url, table=None, fields=['user()', 'version()']):
                \"""Gets a URL, an SQL table (str) and a list of SQL fields.
                \"""
                ...

            @entry
            def sum_all(numeric_values: list[int]):
                \"""Takes a list of at least one int value as input.
                \"""
                msg_info(f'Sum: {sum(numeric_values)}')

            @entry
            def sum_all(numeric_values: [123.4, 567.8]):
                \"""Takes a list of at least one float value as input.
                \"""
                msg_info(f'Sum: {sum(numeric_values)}')

            @entry
            def add(a=3.12, b=4.12):
                \"""Adds two float numbers.
                \"""
                msg_success(f'Sum: {a + b}')

            @entry
            def force_opts(a, *, b, c):
                \"""Forces b and c to be optional arguments.
                \"""
                msg_success(f'Options: b={b!r} c={c!r}')

    """
    # If we have a class, call TheClass(**args).run()
    if isinstance(entrypoint, type):

        def run_main(*args, **kwargs):
            return entrypoint(*args, **kwargs).run()

    # If we have a function, call main(**args)
    else:

        def run_main(*args, **kwargs):
            return entrypoint(*args, **kwargs)

    @functools.wraps(entrypoint)
    def cli_main():
        args, kwargs = _prototype_to_args(entrypoint)
        logger = logging.logger(entrypoint.__module__)
        console = get_console()
        exit_code = 0

        try:
            return run_main(*args, **kwargs)
        except KeyboardInterrupt:
            msg_error("Execution interrupted ([b]Ctrl-C[/b])")
        except TenFailure as e:
            if e.message:
                msg_failure(e.message)
            exit_code = 1
        except TenExit as e:
            if e.message:
                msg_print(e.message)
        except Exception as e:
            msg_error(Text(type(e).__name__, style="bold"), Text(str(e)))
            logger.error(f"{type(e).__name__}: {e}", exc_info=True)
            console.print_exception()
            exit_code = 1
        finally:
            with console._lock:
                if console._live:
                    console._live.stop()
                    console._live = None
            if exit_code:
                exit(exit_code)

    return cli_main


def _doc_to_description(function):
    doc = function.__doc__
    if not doc:
        return None
    doc = doc.strip()
    # Find the smallest newline space prefix, but only if it is followed by a
    # character
    # We can't use textwrap.dedent() because it requires the first line to
    # be idented
    indent = re.findall(r"(\n[ \t]+)[^\s]", doc)
    if indent:
        indent = min(indent, key=len)
        return doc.replace(indent, "\n")
    return doc


def _prototype_to_args(function: type | Callable) -> tuple[list, dict]:
    """Creates an argument parser from a function prototype. If a parameter has
    a default value of type _int, bool, float or bytes_, or a `list` of those,
    the value sent from the command line arguments is converted into said type.
    Type annotation can be used to force the type of the command line arguments.
    In addition, parameters that come after the `*` metaparameter, have a
    default value, or are of type boolean or list, are mapped as an option.
    Then, parses the arguments from the command line and returns the args and kwargs.
    """
    from tenlib.fs import Path
    from tenlib.http import ScopedSession

    _PROTO_RAW_TYPES = (int, bool, float, bytes, str, Path, ScopedSession)
    s = inspect.signature(function)
    # If the function is actually a class, we want the hints from the constructor
    underlying_function = function.__init__ if inspect.isclass(function) else function
    type_hints = get_type_hints(underlying_function)

    parser = argparse.ArgumentParser(
        description=_doc_to_description(function),
        formatter_class=__ARGPARSE_FORMATTER,
    )
    # -h is already used by --help, so skip it
    shortcuts = {"-h"}

    function_arguments = []
    star_argument = None

    for k, p in s.parameters.items():
        arg_desc = SimpleNamespace()

        # Handle defaults and type
        arg_desc.nargs = None
        if p.default is not inspect._empty:
            arg_desc.default = p.default
        else:
            arg_desc.required = True

        # If a type is explicitly specified, use it
        if p.annotation is not inspect._empty:
            annotation = type_hints[k]
            aorigin = get_origin(annotation)
            aargs = get_args(annotation)

            # Unwrap Optional[...]
            if aorigin is Union and len(aargs) == 2 and aargs[1] is NoneType:
                annotation = aargs[0]
                aorigin = get_origin(annotation)
                aargs = get_args(annotation)

            if isinstance(annotation, type) and issubclass(annotation, list):
                arg_desc.nargs = "*"
                arg_desc.type = str
            elif aorigin is list:
                arg_desc.nargs = "*"
                arg_desc.type = aargs[0]
            else:
                arg_desc.type = annotation
        # Otherwise, deduce it from the default value
        elif p.default is not inspect._empty and p.default is not None:
            default_type = type(p.default)
            if issubclass(default_type, list):
                arg_desc.nargs = "*"
                try:
                    arg_desc.type = type(p.default[0])
                except IndexError:
                    arg_desc.type = str
            else:
                arg_desc.type = default_type

        # As a last resort, it has to be a string
        else:
            arg_desc.type = str

        if p.default is not inspect._empty:
            arg_desc.default = p.default

        if p.kind == p.VAR_POSITIONAL:
            arg_desc.nargs = "*"

        # Make boolean arguments optional, false by default
        if arg_desc.type is bool and not arg_desc.nargs:
            del arg_desc.type
            del arg_desc.nargs
            arg_desc.required = False
            if p.default is inspect._empty or not p.default:
                arg_desc.action = "store_true"
                # If there is not default, we set one ourselves, otherwise
                # there is no way to set the option to False
                arg_desc.default = False
            else:
                arg_desc.action = "store_false"
                arg_desc.default = True

        # Handle -p, --parameter

        # Do we make this parameter an option or a standard argument?
        as_opt = (
            # After '*'
            p.kind == p.KEYWORD_ONLY
            or
            # Has default value
            hasattr(arg_desc, "default")
            or
            # List argument, not star argument
            (arg_desc.nargs == "*" and p.kind != p.VAR_POSITIONAL)
        )

        # Handle -p, --parameter
        if as_opt:
            shortcut = "-" + k[0]
            if shortcut in shortcuts:
                shortcut = "-" + k[0].upper()

            longcut = "--" + k.replace("_", "-")
            # Help is already handled by argparse, so we cannot use it...
            # raise an exception
            if longcut == "--help":
                raise argparse.ArgumentError(
                    None, "Cannot use 'help' as an entry parameter name"
                )
            # If the shortcut is already used, map only the longcut
            elif shortcut in shortcuts:
                arg_names = (longcut,)
            # If the parameter is only one letter long, map it only as a shortcut
            elif len(k) == 1:
                arg_names = (shortcut,)
            # Otherwise, map both
            else:
                arg_names = (shortcut, longcut)

            shortcuts.add(shortcut)
        # Handle the standard
        else:
            del arg_desc.required
            arg_names = (k,)
            # This is the star argument
            if arg_desc.nargs == "*":
                star_argument = k
            else:
                function_arguments.append(k)

        # TODO: Handle that error better: it should not really be a ten error,
        # as we haven't even started the program yet
        # Verify that the type is supported
        if hasattr(arg_desc, "type") and not issubclass(
            arg_desc.type, _PROTO_RAW_TYPES
        ):
            raise TypeError(
                f"Unsupported type {arg_desc.type.__name__} for parameter {k}"
            )
        # Last annoying case: casting booleans from strings
        if getattr(arg_desc, "nargs", None) == "*" and arg_desc.type is bool:

            def str_to_bool(value):
                if value.lower() in ("1", "true", "yes"):
                    return True
                if value.lower() in ("0", "false", "no"):
                    return False
                raise ValueError(f"Invalid argument for type bool: {value!r}")

            arg_desc.type = str_to_bool

        try:
            arg_desc.help = function.__ten_doc__[k]
        except (AttributeError, KeyError):
            pass
        parser.add_argument(*arg_names, **vars(arg_desc))

    # Create the arguments as args, kwargs

    arg_desc = vars(parser.parse_args())

    args = [arg_desc.pop(name) for name in function_arguments]
    if star_argument is not None:
        args += arg_desc.pop(star_argument)

    return args, arg_desc


def arg(name: str, description: str):
    """Provides documentation for the parameter `name` of the `entry` function.
    The documentation is visible when the program is run with the `--help` flag.

    Example:

    ```python
    @entry
    @arg("name", "The name of the person to greet")
    def hello(name: str):
        msg_info(f"Hello, {name}!")
    ```
    """

    def wrapper(entry: Callable) -> Callable:
        if not hasattr(entry, "__ten_doc__"):
            entry.__ten_doc__ = {}
        entry.__ten_doc__[name] = description
        return entry

    return wrapper


def msg_print(*objects, **kwargs):
    """Displays a message."""
    get_message_formatter().print(*objects, **kwargs)


def msg_info(*objects, **kwargs):
    """Displays an info message."""
    get_message_formatter().info(*objects, **kwargs)


def msg_failure(*objects, **kwargs):
    """Displays a failure message."""
    get_message_formatter().failure(*objects, **kwargs)


def msg_error(*objects, **kwargs):
    """Displays an error message."""
    get_message_formatter().error(*objects, **kwargs)


def msg_success(*objects, **kwargs):
    """Displays a success message."""
    get_message_formatter().success(*objects, **kwargs)


def msg_warning(*objects, **kwargs):
    """Displays a warning message."""
    get_message_formatter().warning(*objects, **kwargs)


def msg_debug(*objects, **kwargs):
    """Displays a debug message."""
    get_message_formatter().debug(*objects, **kwargs)


def msg_clear():
    """Clears the current line."""
    get_message_formatter().clear()


def bin_print(data: bytes):
    """Prints bytes to stdout."""
    get_message_formatter().bin_print(data)


def msg_status(
    status: RenderableType,
    *,
    spinner: str = "dots",
    spinner_style: str = "status.spinner",
    speed: float = 1.0,
    refresh_per_second: float = 12.5,
) -> Status:
    """Display a status and spinner.
    See rich's [`Console.status`](https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.status).

    Example:

        ```python
        with msg_status("Doing something..."):
            # Do something slow
            ...
        ```

    Args:
        status (RenderableType): A status renderable (str or Text typically).
        spinner (str, optional): Name of spinner animation (see python -m rich.spinner).
            Defaults to "dots".
        spinner_style (StyleType, optional): Style of spinner. Defaults to
            "status.spinner".
        speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
        refresh_per_second (float, optional): Number of refreshes per second. Defaults
            to 12.5.

    Returns:
        Status: A Status object that may be used as a context manager.
    """
    return get_console().status(
        status,
        spinner=spinner,
        spinner_style=spinner_style,
        speed=speed,
        refresh_per_second=refresh_per_second,
    )


def leave(message=None, *args, **kwargs) -> NoReturn:
    """Displays a message if given, and exits.

    Raises:
        TenExit: to exit
    """
    raise TenExit(message, *args, **kwargs)


def failure(message: str = None) -> NoReturn:
    """Displays a failure message if given, and exits.

    Raises:
        TenFailure: to exit
    """
    raise TenFailure(message)


def error(message: str = None) -> NoReturn:
    """Displays an error message if given, displays the stack trace, and exits.

    Raises:
        TenError: to exit
    """
    raise TenError(message)


def pause(message: str = "Paused. Press ENTER to resume execution") -> None:
    """Pauses the execution of the program until `ENTER` is pressed.

    Args:
        message (str): A message to display before pausing
    """
    msg_debug(message, end="")
    input()


def assume(assumption: bool, message: str = "Assumption failed") -> None:
    """If given assumption is `False`, raises `tenlib.exception.TenFailure`.
    This function is the equivalent of `assert`, but it'll display a standard
    failure message and exit, without displaying a stack trace.

    In other words, if the assumption being false means the program has failed,
    but is not an error per-se, use `assume`. If you want an exception to be
    raised, use the built-in `assert`.

    This allows you to simplify code such as:

    ```python
    match = response.re.search(r'token="(.*?)"')
    if not match:
        failure('Response does not contain a token')
    ```

    to:

    ```python
    match = response.re.search(f'token="(.*?)"')
    assume(match, 'Response does not contain a token')
    ```

    Args:
        assumption (bool): Assumption to evaluate
        message (str): Message for the `TenFailure` exception
    """
    if not assumption:
        failure(message)


def inform(
    go: str = None, ok: str = None, ko: str = None, ko_exit: bool = False
) -> Callable[[Callable], Callable]:
    """This decorator will display a spinner and a message while a coroutine is
    running, and optionally a message after it is done.

    Args:
        go (str): Message to display while the coro executes
        ok (str): Message to display if the coro returns a result that evaluates
            to `True`.
        ko (str): Message to display if the coro returns a result that evaluates
            to `False`.
        ko_exit (bool): If set, the execution will stop if the coro does not
            find a result. Defaults to `False`.

    `ok` and `ko` can use the `{result}` format to display the result.

    Examples:

        Decorate a function that bruteforces a seed:

        ```python
        @inform(
            go='Bruteforcing seed...',
            ok='Seed found: {result}',
            ko='Unable to find seed'
        )
        def find_seed(token):
            for i in range(1000000):
                if hashing.md5(i) == token:
                    return i
            return None
        ```

        Decorate a login procedure: if it fails, the script will exit.

        ```python
        @inform(
            go='Trying to log in...',
            ok='Login successful',
            ko='Login failed, exiting',
            ko_exit=True
        )
        def login(session, user, password):
            r = await session.post('/login', {'u': user, 'p': password})
            return r.contains('login successful')
        ```
    """

    def inform_wrapper(function):
        @functools.wraps(function)
        def _inform_wrapper(*args, **kwargs):
            if go:
                with msg_status(go.format(args=args, kwargs=kwargs)):
                    result = function(*args, **kwargs)
            else:
                result = function(*args, **kwargs)

            if ok and result:
                msg_success(ok.format(result=result))

            if ko and not result:
                if ko_exit:
                    failure(ko.format(result=result))

                msg_failure(ko.format(result=result))

            return result

        return _inform_wrapper

    return inform_wrapper


def trace(function: Callable) -> Callable:
    """Decorator that displays a debug log line containing the function name,
    its parameters and the value returned.
    """
    logger = logging.logger(function.__module__)

    @functools.wraps(function)
    def traced_function(*args, **kwargs):
        # Not the cleanest way
        name = function.__qualname__
        is_method = int(inspect.ismethod(function))

        parameters = ", ".join(
            [f"{arg!r}" for arg in args[is_method:]]
            + [f"{k}={v!r}" for k, v in kwargs.items()]
        )
        returned = function(*args, **kwargs)
        logger.trace(f"{name}({parameters}) -> {returned!r}")

        return returned

    return traced_function


class _CompletedTotalColumn(ProgressColumn):
    def get_string_for_nb(self, nb: int) -> str:
        if nb is None:
            nb = 0
        nb = int(nb)
        unit, suffix = filesize.pick_unit_and_suffix(
            nb, ["", "K", "M", "G", "T", "P", "E", "Z", "Y"], 1000
        )
        ratio = nb / unit
        precision = 0 if unit == 1 else 1
        return f"{ratio:,.{precision}f}{suffix}"

    def render(self, task) -> Text:
        """Calculate common unit for completed and total."""
        completed = self.get_string_for_nb(task.completed)
        total = self.get_string_for_nb(task.total)
        return Text(f"{completed}/{total}", style="progress.download")


_progress_columns = [
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    _CompletedTotalColumn(),
    TextColumn("[progress.percentage]{task.percentage:.0f}%"),
    TimeElapsedColumn(),
    TimeRemainingColumn(),
]


def progress(transient: bool = True, **kwargs) -> Progress:
    """A [`Progress`](https://rich.readthedocs.io/en/stable/reference/progress.html#rich.progress.Progress) bar.

    Args:
        transient (bool): Clear the progress on exit. Defaults to False.
        **kwargs: see the documentation for `Progress`.
    """
    return Progress(
        *_progress_columns, transient=transient, **kwargs, console=get_console()
    )


def track(
    sequence: Iterable,
    description: str = "Working...",
    total: Optional[float] = None,
    transient: bool = True,
) -> Iterable:
    """Track progress when iterating over a sequence. This is a wrapper for
    [rich's `track`](https://rich.readthedocs.io/en/stable/reference/progress.html#rich.progress.Progress.track).

    Example:

        ```python
        for i in track(range(100), "Iterating over 100 numbers"):
            # do something
            ...
        ```

    Args:
        sequence (Iterable): A sequence (must support `len()`) you wish to iterate over.
        description (str, optional): Description of task show next to progress bar. Defaults to "Working".
        total (float, optional): Total number of steps. Default is len(sequence).
        transient (bool, optional): Clear the progress on exit. Defaults to True.

    Returns:
        Iterable: An iterable of the values in the sequence.
    """
    progress = Progress(
        *_progress_columns,
        transient=transient,
        console=get_console(),
    )

    with progress:
        yield from progress.track(sequence, total=total, description=description)


def sleep(seconds) -> None:
    """Alias for `time.sleep`."""
    return time.sleep(seconds)


def ask(
    prompt: TextType = "",
    *,
    password: bool = False,
    choices: Optional[list[str]] = None,
    show_default: bool = True,
    show_choices: bool = True,
    default: Any = ...,
) -> Any:
    """Shortcut to construct and run a prompt loop and return the result.
    Wrapper for `rich.prompt.Prompt`.

    Example:
        >>> filename = ask("Enter a filename")

    Args:
        prompt (TextType, optional): Prompt text. Defaults to "".
        password (bool, optional): Enable password input. Defaults to False.
        choices (list[str], optional): A list of valid choices. Defaults to None.
        show_default (bool, optional): Show default in prompt. Defaults to True.
        show_choices (bool, optional): Show choices in prompt. Defaults to True.
    """
    _prompt = Prompt(
        prompt,
        password=password,
        choices=choices,
        show_default=show_default,
        show_choices=show_choices,
        console=get_console(),
    )
    return _prompt(default=default)


def get_message_formatter() -> messageformatter.MessageFormatter:
    """Returns the `messageformatter.MessageFormatter` instance."""
    if not __message_formatter:
        set_message_formatter(config.message_formatter)
    return __message_formatter


def set_random_message_formatter() -> None:
    """Sets a random `messageformatter.MessageFormatter` as the message
    formatter.
    """
    MF = messageformatter.MessageFormatter
    formatters = [getattr(messageformatter, cls) for cls in messageformatter.__all__]
    formatters = [
        cls
        for cls in formatters
        if inspect.isclass(cls) and issubclass(cls, MF) and not inspect.isabstract(cls)
    ]
    formatter = random.choice(formatters)
    set_message_formatter(formatter)


def set_message_formatter(
    message_formatter: messageformatter.MessageFormatter
    | Type[messageformatter.MessageFormatter]
    | str,
) -> None:
    """Sets given `messageformatter.MessageFormatter` as the message formatter."""
    global __message_formatter

    if isinstance(message_formatter, str):
        if not message_formatter.endswith("MessageFormatter"):
            message_formatter += "MessageFormatter"
        message_formatter = getattr(messageformatter, message_formatter)

    if isinstance(message_formatter, type) and issubclass(
        message_formatter, messageformatter.MessageFormatter
    ):
        message_formatter = message_formatter()

    if not isinstance(message_formatter, messageformatter.MessageFormatter):
        raise TypeError(
            f"The object needs to be a MessageFormatter name, class, or instance, "
            f"not {message_formatter!r}"
        )

    __message_formatter = message_formatter

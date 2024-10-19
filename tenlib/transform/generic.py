import inspect
import functools
from typing import Any, Concatenate, ParamSpec, TypeVar, Callable, Union, overload
from tenlib.struct.proxy import TenDict, TenList

__all__ = ["multiform", "wrap_join_format", "to_bytes", "to_str", "strip", "not_empty"]


T = TypeVar("T")

OriginalParams = ParamSpec("OriginalParams")
OriginalRetType = TypeVar("OriginalRetType")
OriginalType = TypeVar("OriginalType", str, bytes)


def multiform(
    function: Callable[Concatenate[OriginalType, OriginalParams], OriginalRetType]
):
    """Decorator converting a function expecting a single argument of type str
    or bytes into a function that applies additionally to a string or every
    value of a `list`, `dict`, `set` or `tenlib.struct.proxy.TenDict`, and its
    sub-elements.
    """

    signature = inspect.signature(function)
    ptype = signature.parameters[next(iter(signature.parameters.keys()))].annotation
    if isinstance(ptype, str):
        ptype = eval(ptype)
    if ptype is inspect._empty:
        raise TypeError(
            "First argument of multiform-decored function should have a type annotation"
        )
    if ptype not in (bytes, str):
        raise TypeError(
            f"First argument of multiform-decored function should have a type of str or bytes, not {ptype.__name__}"
        )

    # Add correct signatures to the function, one by one, so that the return type is
    # correctly inferred

    @overload
    def mfunction(
        data: str | bytes, *args: OriginalParams.args, **kwargs: OriginalParams.kwargs
    ) -> OriginalRetType:
        ...

    @overload
    def mfunction(
        data: list, *args: OriginalParams.args, **kwargs: OriginalParams.kwargs
    ) -> list[OriginalRetType]:
        ...

    @overload
    def mfunction(
        data: set, *args: OriginalParams.args, **kwargs: OriginalParams.kwargs
    ) -> set[OriginalRetType]:
        ...

    @overload
    def mfunction(
        data: tuple, *args: OriginalParams.args, **kwargs: OriginalParams.kwargs
    ) -> tuple[OriginalRetType]:
        ...

    @overload
    def mfunction(
        data: dict[T, Any], *args: OriginalParams.args, **kwargs: OriginalParams.kwargs
    ) -> dict[T, OriginalRetType]:
        ...

    @overload
    def mfunction(
        data: int, *args: OriginalParams.args, **kwargs: OriginalParams.kwargs
    ) -> OriginalRetType:
        ...

    @overload
    def mfunction(
        data: bytearray, *args: OriginalParams.args, **kwargs: OriginalParams.kwargs
    ) -> OriginalRetType:
        ...

    @functools.wraps(function)
    def mfunction(
        data: Any,
        *args: OriginalParams.args,
        **kwargs: OriginalParams.kwargs,
    ) -> Any:
        if data is None:
            return None
        if isinstance(data, bytes):
            if ptype is str:
                data = data.decode()
            return function(data, *args, **kwargs)
        if isinstance(data, str):
            if ptype is bytes:
                data = data.encode()
            return function(data, *args, **kwargs)
        if isinstance(data, bytearray):
            return function(bytes(data), *args, **kwargs)
        if isinstance(data, int):
            return mfunction(str(data), *args, **kwargs)
        if isinstance(data, TenList):
            return TenList([mfunction(item, *args, **kwargs) for item in data])
        if isinstance(data, list):
            return [mfunction(item, *args, **kwargs) for item in data]
        if isinstance(data, set):
            return {mfunction(item, *args, **kwargs) for item in data}
        if isinstance(data, tuple):
            return tuple(mfunction(item, *args, **kwargs) for item in data)
        if isinstance(data, TenDict):
            return TenDict(mfunction(dict(data), *args, **kwargs))
        if isinstance(data, dict):
            return {k: mfunction(v, *args, **kwargs) for k, v in data.items()}
        raise TypeError(f"Cannot apply transform to type {type(data).__name__}")

    return mfunction


def wrap_join_format(
    wrapper: str = "{}", formatter: str = "{}", jointure: str = ",", empty: str = None
) -> Callable[[bytes], str]:
    """Generates a function that takes one parameter, `data`.
    For every byte in `data`, it will format them using `format`, join them
    using `jointure`, and wrap the whole thing using `wrapper`.
    If the given data is empty, and empty is set, the latter is returned
    instead.

    Examples:
        >>> wrap_join_format(b'ABC')
        '65,66,67'
        >>> wrap_join_format(formatter='{:c}', jointure='')(b'ABC')
        'ABC'
        >>> wrap_join_format('CONCAT({})', 'CHR(0x{:02x})')('ABC')
        'CONCAT(CHR(0x41),CHR(0x42),CHR(0x43))'
        >>> wrap_join_format(empty='something_else')('')
        'something_else'
    """

    @multiform
    def function(data: bytes) -> str:
        if not data and empty is not None:
            return empty
        return wrapper.format(jointure.join(formatter.format(b) for b in data))

    return function


@multiform
def to_bytes(data: bytes) -> bytes:
    """Converts the parameter into bytes."""
    # Due to the multiform decorator, data is of type bytes
    return data


@multiform
def to_str(data: str) -> str:
    """Converts the parameter to a string."""
    # Due to the multiform decorator, data is of type str
    return data


@multiform
def strip(data: bytes, chars=None) -> bytes:
    """Calls data.strip() on every element of the object."""
    return data.strip(chars)


def not_empty(data: list) -> list:
    """Removes empty items from a list."""
    return [item for item in data if item]


@multiform
def xor(a: bytes, b: bytes) -> bytes:
    """XORs `a` with key `b`. If `b` is smaller than `a`, it will be repeated.

    Example:

    >>> xor('A', 'B')
    b'\x03'
    >>> xor('ABCD', 'AB')
    b'\x00\x00\x02\x06'
    >>> xor('AB', 'ABCD')
    b'\x00\x00'
    """
    b = to_bytes(b)
    return bytes([x ^ b[i % len(b)] for i, x in enumerate(a)])

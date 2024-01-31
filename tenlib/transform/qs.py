import itertools
import urllib.parse

from tenlib.transform.generic import multiform, wrap_join_format


@multiform
def encode(data: bytes):
    """Wrapper for `urllib.parse.quote_plus`."""
    return urllib.parse.quote_plus(data)


encode_all = wrap_join_format("{}", "%{:02x}", "")


@multiform
def decode(data: str):
    """Wrapper for `urllib.parse.unquote_plus`."""
    return urllib.parse.unquote_plus(data)


def decode_bytes(data: str) -> bytes:
    """Wrapper for `urllib.parse.unquote_to_bytes`."""
    return urllib.parse.unquote_to_bytes(data)


# IIS Specific: %u00XX


@multiform
def iis_encode(data: bytes):
    """Performs an IIS encoding (`%u00XX`)."""
    # %25 -> %u0025, etc.
    return urllib.parse.quote(data).replace("%", "%u00")


iis_encode_all = wrap_join_format("{}", "%u00{:02x}", "")
"""`ABC` -> `%u0041%u0042%u0043`"""

# QS


def unparse(data: dict) -> str:
    """Converts a dictionary of parameters into a query string.

    Examples:
        >>> unparse({'k1': 'v1', 'k2': '', 'k3[k4]': 'v3 //'})
        'k1=v1&k2=&k3[k4]=v3+%2F%2F'
        >>> unparse({'a': ['b', {'d': 'e'}]})
        'a[0]=b&a[1][d]=e'
    """
    tuples = []
    for k, v in data.items():
        _unparse_flatten(tuples, k, v)
    return "&".join(
        "{}={}".format(
            encode(key).replace("%5B", "[").replace("%5D", "]"), encode(value)
        )
        for key, value in tuples
    )


def _unparse_flatten(data, key, item):
    if isinstance(item, dict):
        for k, v in item.items():
            _unparse_flatten(data, f"{key}[{k}]", v)
    elif isinstance(item, list):
        for i, v in enumerate(item):
            _unparse_flatten(data, f"{key}[{i}]", v)
    else:
        data.append((key, item))


@multiform
def parse(query: str, flat: bool = True) -> dict:
    """Splits the query string into a `dict` of parameters. If `flat` is `False`
    array keys such as `k[a][b]` are parsed as a multi-dimensional `dict`. Empty
    keys such as `k[]` take the next possible integer value.

    Args:
        flat (bool): If True, returns a one-dimensional
            `dict`. Otherwise, returns nested `dict` objects.

    Returns:
        dict

    Examples:
        >>> parse('k1=v1&k2=v2&k3[k4]=v3+%2f%2f')
        {'k1': 'v1', 'k2': '', 'k3[k4]': 'v3 //'}
        >>> parse('k[0]=0&k[3]=3&k[]=1', flat=False)
        {'k': {'0': '0', '3': '3', '1': '1'}}
    """
    parts = query.split("&")
    items = []

    for kv in parts:
        if not kv:
            continue
        kv = kv.split("=", 1)

        key = decode(kv[0])
        value = decode(kv[1] if len(kv) > 1 else "")
        items.append((key, value))

    if flat:
        return dict(items)

    deep = {}

    for key, value in items:
        keys = _parse_split_key(key)
        current = deep

        for key in keys[:-1]:
            # If the key is empty, we need to find the next numerical index that
            # is free
            # k[]=v0&k[]=v1 -> index 0 then index 1
            key = _parse_key_to_index(current, key)
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        key = _parse_key_to_index(current, keys[-1])
        current[key] = value

    return deep


def _parse_key_to_index(current, key):
    if key:
        return key
    return next(i for i in map(str, itertools.count()) if str(i) not in current)


def _parse_split_key(key):
    if "[" not in key or "]" not in key:
        return (key,)
    if "]" != key[-1]:
        raise ValueError(f"{key!r}: Array key must end with ]")

    p0 = key.index("[")
    main = key[:p0]
    rest = key[p0 + 1 : -1].split("][")

    if any("[" in key or "]" in key for key in rest):
        raise ValueError(f"{key!r}: Unable to parse key")
    if main == "":
        raise ValueError(f"{key!r}: Main key cannot be empty")
    return (main, *rest)

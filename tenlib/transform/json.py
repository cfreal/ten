import json

from tenlib.transform.generic import multiform
from tenlib import fs

__all__ = [
    "encode",
    "decode",
    "JSONDecodeError",
    "read",
    "write",
]

JSONDecodeError = json.JSONDecodeError


def encode(data, **kwargs) -> str:
    """Wrapper for `json.dumps()`."""
    return json.dumps(data, **kwargs)


@multiform
def decode(data: str, **kwargs):
    """Wrapper for `json.loads()`."""
    return json.loads(data, **kwargs)


read = fs.wrapper_read(decode)
write = fs.wrapper_write(encode)

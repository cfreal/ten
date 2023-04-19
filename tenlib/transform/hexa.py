from tenlib.transform.generic import multiform
from tenlib import fs


@multiform
def encode(data: bytes, *args) -> str:
    """Create a string of hexadecimal numbers from a bytes object.
    Wrapper for bytes.hex().

    Args:
        data: Data to encode in hexadecimal.
        sep: An optional single character or byte to separate hex bytes.
        bytes_per_sep: How many bytes between separators. Positive values count
        from the right, negative values count from the left.
    """
    return data.hex(*args)


@multiform
def decode(data: str) -> bytes:
    """Create a bytes object from a string of hexadecimal numbers.
    Wrapper for bytes.fromhex().

    Spaces between two numbers are accepted.

    Example:

        ```python
        bytes.fromhex('B9 01EF') -> b'\xb9\x01\xef'.
        ```
    """
    return bytes.fromhex(data)


read = fs.wrapper_read(decode)
write = fs.wrapper_write(encode)

"""A few utility functions.
"""

from typing import Iterable, Iterator


def repr_attrs(obj, attrs):
    """Returns a string representation of the object, with its name and selected
    attributes.
    """
    cls = type(obj).__name__
    attrs = [(k, getattr(obj, k)) for k in attrs]
    attrs = ", ".join(f"{k}={v!r}" for k, v in attrs)
    return f"{cls}({attrs})"


def niter(data: Iterable, n: int) -> Iterator[tuple]:
    """Yields `n` items for an iterable, then the next `n` items, etc.

    >>> for part in niter(range(10), 3)
    ...  print(part)
    (0, 1, 2)
    (3, 4, 5)
    (6, 7, 8)
    (9, )
    """
    if n <= 0:
        raise ValueError(f"niter(): n needs to be strictly positive: {n!r}")

    if isinstance(data, bytes):
        cast = bytes
    elif isinstance(data, str):
        cast = "".join
    else:
        cast = tuple

    got = []
    ngot = 0

    for item in iter(data):
        ngot += 1
        got.append(item)

        if ngot == n:
            ngot = 0
            yield cast(got)
            got = []

    if ngot:
        yield cast(got)

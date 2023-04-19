import random
import string as _string


def string(size: int = 8, charset: str = _string.ascii_letters + _string.digits) -> str:
    """Generates a random string.

    Example:

        >>> string(10)
        'VVclsHsC2H'
        >>> string(charset="abc")
        'bcacbbcc'

    Args:
        size (int): Size of the string
        charset (str): Charset to extract characters from

    Returns:
        str: Random string
    """
    return "".join(random.choice(charset) for _ in range(size))


def alpha(size: int = 8) -> str:
    """Generates a random alphanumeric string.

    Example:

        >>> alpha(10)
        'DerMRLuAyy'

    Args:
        size (int): Size of the string

    Returns:
        str: Random alphanumeric string
    """
    return string(size, charset=_string.ascii_letters)


def lower(size: int = 8) -> str:
    """Generates a random lowercase string.

    Example:

        >>> lower(10)
        'mkswzvglno'

    Args:
        size (int): Size of the string

    Returns:
        str: Random lowercase string
    """
    return string(size, charset=_string.ascii_lowercase)


def hexa(size: int = 40) -> str:
    """Generates a random hexadecimal string.

    Example:

        >>> hexa(10)
        '7f33d853ef'

    Args:
        size (int): Size of the string

    Returns:
        str: Random hexadecimal string
    """
    return string(size, charset="0123456789abcdef")


def digits(size: int = 8) -> str:
    """Generates a random digit string.

    Example:

        >>> digits(10)
        '3030278136'

    Args:
        size (int): Size of the string

    Returns:
        str: Random digit string
    """
    return string(size, charset=_string.digits)


def number(min: int = 0, max: int = 100000) -> int:
    """Generates a random integer between `min` and `max`, included.

    Example:

        >>> number(1, 10)
        8

    Args:
        min (int): Minimum value
        max (int): Maximum value

    Returns:
        int: Random integer
    """
    return random.randint(min, max)

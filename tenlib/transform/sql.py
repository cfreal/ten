from __future__ import annotations

from tenlib.transform.generic import wrap_join_format
from tenlib.transform.generic import multiform
from tenlib.transform.hexa import encode as hexa_encode


@multiform
def addslashes_single(data: str):
    """Replaces characters that need to be escaped in a backslash-escaped single
    quote string. Those characters are:

    * `'`
    * `\\`
    * `\\n`
    * `\\t`
    * `\\r`
    * `\\0`
    """
    t = {"\\": "\\\\", "'": "\\'", "\n": "\\n", "\t": "\\t", "\r": "\\r", "\0": "\\0"}
    data = "".join(t.get(c, c) for c in data)
    return f"'{data}'"


@multiform
def addslashes_double(data: str):
    """Replaces characters that need to be escaped in a backslash-escaped double
    quote string. Those characters are:

    * `"`
    * `\\`
    * `\\n`
    * `\\t`
    * `\\r`
    * `\\0`
    """
    t = {
        "\\": "\\\\",
        '"': '\\"',
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "\0": "\\0",
    }
    data = "".join(t.get(c, c) for c in data)
    return f'"{data}"'


@multiform
def xstring(data: bytes):
    """`ABC` -> `X'414243'`"""
    return f"X'{hexa_encode(data)}'"


@multiform
def singlequote(data: str) -> str:
    """`ABC'DEF` -> `'ABC''DEF'`"""
    return "'" + data.replace("'", "''") + "'"


@multiform
def doublequote(data: str) -> str:
    """`ABC"DEF` -> `"ABC""DEF"`"""
    return '"' + data.replace('"', '""') + '"'


@multiform
def ord(data: bytes) -> list[int]:
    """`b'ABC'` -> `[65, 66, 67]`"""
    return list(data)


sum_chr = wrap_join_format("{}", "CHR({})", "+", "TRIM(CHR(32))")
"""`'ABC'` -> `'CHR(65)+CHR(66)+CHR(67)'`"""

sum_char = wrap_join_format("{}", "CHAR({})", "+", "TRIM(CHAR(32))")
"""`'ABC'` -> `'CHAR(65)+CHAR(66)+CHAR(67)'`"""

pipes_chr = wrap_join_format("{}", "CHR({})", "||", "TRIM(CHAR(32))")
"""`'ABC'` -> `'CHR(65)||CHR(66)||CHR(67)'`"""

pipes_char = wrap_join_format("{}", "CHAR({})", "||", "TRIM(CHAR(32))")
"""`'ABC'` -> `'CHAR(65)||CHAR(66)||CHAR(67)'`"""

concat_char = wrap_join_format("CONCAT({})", "CHAR({})", ",", "TRIM(CHAR(32))")
"""`'ABC'` -> `'CONCAT(CHAR(65),CHAR(66),CHAR(67))'`"""

concat_chr = wrap_join_format("CONCAT({})", "CHR({})", ",", "TRIM(CHR(32))")
"""`'ABC'` -> `'CONCAT(CHR(65),CHR(66),CHR(67))'`"""

hexadecimal = wrap_join_format("0x{}", "{:02x}", "", "TRIM(0x20)")
"""`'ABC'` -> `'0x414243'`"""

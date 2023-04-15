import html

from tenlib.transform.generic import wrap_join_format
from tenlib.transform.generic import multiform
from tenlib import fs


@multiform
def encode(data: str) -> str:
    """Encodes HTML entities.
    `b'ABC&DEF'` -> `'ABC&amp;DEF'`
    """
    return html.escape(data)


@multiform
def decode(data: str) -> str:
    """Decodes HTML entities.
    `b'&#x41;BC&amp;DEF&nbsp;GHI'` -> `'ABC&DEF GHI'`
    """
    return html.unescape(data)


# hexa
encode_all = wrap_join_format("{}", "&#x{:02x};", "")
"""Converts every character into its hexadecimal html-entity equivalent.
`b'ABC&DEF'` -> `'&#x41;&#x42;&#x43;&#x26;&#x44;&#x45;&#x46;'`
"""
# decimal
encode_all_dec = wrap_join_format("{}", "&#{:02};", "")
"""Converts every character into its decimal html-entity equivalent.
`b'ABC&DEF'` -> `'&#65;&#66;&#67;&#38;&#68;&#69;&#70;'`
"""


read = fs.wrapper_read(decode)
write = fs.wrapper_write(encode)

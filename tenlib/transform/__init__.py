"""Regroups transformations such as: base64, HTML, hash, SQL, etc. The module is
imported as the `tf` global variable.

Each transformation type is regrouped in a module.
Most of them consist of `encode`/`decode` methods:

    >>> tf.base64.encode('test')
    'dGVzdA=='
    >>> tf.base64.decode('dGVzdA==')
    'test'
    >>> tf.hexa.encode('abc')
    '616263'
    >>> tf.hexa.decode('616263')
    'abc'
    >>> tf.json.encode(['abc', 123, "test"])
    '["abc", 123, "test"]'
    >>> tf.json.decode('["abc", 123, "test"]')
    ['abc', 123, 'test']

But others do not:

    >>> tf.sql.hexadecimal('abc')
    '0x616263'
    >>> tf.sql.singlequote('abc\\'def')
    "'abc''def'"
    >>> tf.sql.pipe_chr('abc')
    'CHR(97)|CHR(98)|CHR(99)'
    >>> tf.php.dot_chr('ABC')
    'chr(65).chr(66).chr(67)'

Most of these functions are wrappers for standard modules methods, but they have
a little improvement: they work on every standard data structure, such as `str`,
`bytes`, `int`, but also `list`, `dict`, etc.
`tenlib.struct.proxy.TenDict` objects are also supported.

    >>> tf.base64.encode(['item0', 'item1', 'item2'])
    ['aXRlbTA=', 'aXRlbTE=', 'aXRlbTI=']
    >>> tf.base64.encode({'k0': 'item0', 'k1': 'item1', 'k2': 'item3'})
    {'k0': 'aXRlbTA=', 'k1': 'aXRlbTE=', 'k2': 'aXRlbTM='}

Furthermore, the `decode`/`encode` modules also have `read` and `write`
functions:

    >>> tf.base64.read('my_file.base64')
    'something'
    >>> tf.base64.write('my_file.base64', 'some_data')
    >>> tf.json.read('file.json')
    {'content': 'of', 'file': 'here'}
    >>> tf.json.write('file2.json', [123, 456])

The `tenlib.transform.table` and `tenlib.transform.random` modules are a bit
different, but are often really useful.

Use `tenlib.transform.color` to colorize output.

Additionally, a `tf` script is available in `./tools`.

Examples:
    
    Simple usage on standard structures:

        >>> transform.base64.encode(['abc', 123, 'def'])
        ['YWJj', 'MTIz', 'ZGVm']
        >>> transform.html.decode({
        ...     'user': 'some&amp;user',
        ...     'password': 'my&lt;complex&gt;password'
        ... })
        {'user': 'some&user', 'password': 'my<complex>password'}
        >>> transform.html.decode(TenDict({
        ...     'user': 'some&amp;user',
        ...     'password': 'my&lt;complex&gt;password'
        ... })
        TenDict({'user': 'some&user', 'password': 'my<complex>password'})
    
    Reading and writing files:

        >>> transform.json.read('something.json')
        {'a': 'b', 'c': 'd'}
        >>> transform.json.write('something_else.json', [1, 2, 3])
        >>>
    
    Using the CLI:

        $ echo -n 'a=1&b=2&c=3' | tf -t qs.parse json.encode
        {"a": "1", "b": "2", "c": "3"}
        $ echo '{"abc":1,"def":"two"}' | tf -t json.decode base64.encode qs.unparse
        abc=MQ%3D%3D&def=dHdv
"""

from tenlib.transform import (
    base64,
    color,
    csv,
    case,
    hashing,
    hexa,
    html,
    js,
    json,
    php,
    qs,
    random,
    sql,
    table,
    url,
)
from tenlib.transform.generic import to_str, to_bytes, strip, not_empty, xor

# Transform: Convert data

Exploits need to manipulate data easily: encode it into base64, compute its hash, HTML-decode it, *etc.* That's what `transform` is for.

Each category of transformation is available as a submodule of `transform`.
When you do  `from ten import *`, `transform` is imported as `tf`, and the most used modules, such as `json` or `base64`, are included as root modules.

Each category of transformation is available as a submodule of `transform`.

```python
>>> from tenlib.transform import base64, html
>>> base64.decode('dGVzdA==')
b'test'
>>> html.decode('&lt;div&gt;test&lt;/div&gt;')
'<div>test</div>'
```

Methods support both `bytes` and `str` as input, as well as lists and dicts. Refer to [Multiform](#multiform) for more details.

Here are a few examples for the most common transformations.

## JSON

<table>
<tr><th>python</th><th>output</th></tr>

<tr>
<td>

```python
json.encode({"a": "b", "c": "d"})
```

</td>
<td>

```python
'{"a":"b","c":"d"}'
```

</td>
</tr>
<tr>
<td>

```python
json.decode('{"a": "b", "c": "d"}')
```

</td>
<td>

```python
{"a": "b", "c": "d"}
```

</td>
</tr>

</table>


## Base 64 encoding (base64)

<table>
<tr><th>python</th><th>output</th></tr>

<tr>
<td>

```python
base64.encode('test')
```

</td>
<td>

```python
'dGVzdA=='
```

</td>
</tr>
<tr>
<td>

```python
base64.decode('dGVzdA==')
```

</td>
<td>

```python
b'test'
```

</td>
</tr>

</table>

## Query string (qs)

Parse query string and URL-encode/decode.

<table>
<tr><th>python</th><th>output</th></tr>

<tr>
<td>

```python
qs.parse('k1=v1&k2=v2')
```

</td>
<td>

```python
{'k1': 'v1', 'k2': 'v2'}
```

</td>
</tr>

<tr>
<td>

```python
qs.unparse({'k1': 'v1', 'k2': 'v2'})
```

</td>
<td>

```python
'k1=v1&k2=v2'
```

</td>
</tr>

<tr>
<td>

```python
qs.decode('%41%42%43%3a%44%45%46')
```

</td>
<td>

```python
'ABC:DEF'
```

</td>
</tr>
<tr>
<td>

```python
qs.encode('ABC:DEF')
```

</td>
<td>

```python
'ABC%3aDEF'
```

</td>
</tr>
<tr>
<td>

```python
qs.encode_all('ABC:DEF')
```

</td>
<td>

```python
'%41%42%43%3a%44%45%46'
```

</td>
</tr>

</table>

## Table

Convert data formatted into a table (such as CSV) to a list (of list), and back.
This example converts an array of colon separated lines into a table.

<table>
<tr><th>python</th><th>output</th></tr>

<tr>
<td>

```python
table.split('''\
username:password:email
admin:dUD6s55:admin@site.com
moderator:123456!:moderator@site.com
user:Password1:user@gmail.com\
''', '\n', ':')
```

</td>
<td>

```python
[
    [b'username', b'password', b'email'],
    [b'admin', b'dUD6s55', b'admin@site.com'],
    [b'moderator', b'123456!', b'moderator@site.com'],
    [b'user', b'Password1', b'user@gmail.com'],
]
```

</td>
</tr>
<tr>
<td>

```python
table.join([
    [b'username', b'password', b'email'],
    [b'admin', b'dUD6s55', b'admin@site.com'],
    [b'moderator', b'123456!', b'moderator@site.com'],
    [b'user', b'Password1', b'user@gmail.com'],
], '\n', ':')
```

</td>
<td>

```python
'''\
username:password:email
admin:dUD6s55:admin@site.com
moderator:123456!:moderator@site.com
user:Password1:user@gmail.com\
'''
```

</td>
</tr>

</table>

## Hashing

<table>
<tr><th>python</th><th>output</th></tr>

<tr>
<td>

```python
hashing.md5('test')
```

</td>
<td>

```python
'098f6bcd4621d373cade4e832627b4f6'
```

</td>
</tr>
<tr>
<td>

```python
hashing.sha1('test')
```

</td>
<td>

```python
'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3'
```

</td>
</tr>

</table>

## Others

Lots of other transforms are available. Refer to the [documentation](../tenlib/transform/index.html) for more details.

## Multiform

As you may have seen, you can feed either bytes or strings to the conversion
functions, and they will handle the convertion into the proper type. This
behaviour also works with `dict`s and `list`s:

<table>
<tr><th>python</th><th>output</th></tr>

<tr>
<td>

```python
base64.encode('test')
```

</td>
<td>

```python
'dGVzdA=='
```

</td>
</tr>

<tr>
<td>

```python
base64.encode(b'test')
```

</td>
<td>

```python
'dGVzdA=='
```

</td>
</tr>

<tr>
<td>

```python
base64.encode([
    'test',
    b'test2',
    'test3'
])
```

</td>
<td>

```python
[
    'dGVzdA==',
    'dGVzdDI=',
    'dGVzdDM='
]
```

</td>
</tr>
<tr>
<td>

```python
qs.decode({
    'k1': '%41%42%43',
    'k2': '%44%45%46'
})
```

</td>
<td>

```python
{
    'k1': 'ABC',
    'k2': 'DEF'
}
```

</td>
</tr>

</table>

## CLI: the `tf` program

The `tf` program makes transforms available from the CLI as well:

```shell
$ echo 'dGVzdA==' | tf base64.decode
test
```

The filters can be chained. Here, we convert JSON into an URL-encoded string:

```shell
$ echo '{"a":"b","c":"d"}' | tf json.decode qs.unparse
a=b&c=d
```

Check the `--help` for further details.
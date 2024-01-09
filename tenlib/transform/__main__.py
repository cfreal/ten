#!/usr/bin/env python3

import sys

from ten import *
from tenlib.struct.proxy import TenDict


@entry
@arg("transforms", "Transforms to apply")
@arg("python", "If set, data is displayed as python code")
@arg("keep_newline", "If not set, the last newline of the input is removed")
def main(*transforms, python=False, keep_newline=False):
    """Applies one or several transforms from the transform module of ten.

    Examples:

        $ echo -n 'a=3&b=2' | tf qs.parse json.encode
        {"a": "3", "b": "2"}
        $ echo -n 'a=3&b=2' | tf qs.parse json.encode -p
        '{"a": "3", "b": "2"}'
        $ cat /etc/passwd | tf base64.encode
        cm9vdDp4OjA6MDpyb290Oi9yb290Oi9iaW4vYmFzaApkYWVtb24...
    """
    data = sys.stdin.buffer.read()
    if not keep_newline and data.endswith(b"\n"):
        data = data[:-1]

    for modfunc in transforms:
        module, func = modfunc.split(".")

        instance = getattr(tf, module, None)

        if not instance:
            return msg_error(f"Unknown module [red]{module}")

        instance = getattr(instance, func, None)

        if not instance:
            return msg_error(f"Unknown transform [red]{module}.{func}")

        data = instance(data)

    if python:
        pprint(data)
    elif isinstance(data, bytes):
        sys.stdout.buffer.write(data)
    elif isinstance(data, str):
        print(data)
    else:
        if isinstance(data, TenDict):
            data = dict(data)
        pprint(data, indent=4)


main()

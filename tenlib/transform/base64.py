import base64

from tenlib.transform.generic import multiform
from tenlib import fs


@multiform
def encode(data: bytes) -> str:
    return base64.b64encode(data).decode()


@multiform
def decode(data: bytes) -> bytes:
    return base64.b64decode(data)


read = fs.wrapper_read(decode)
write = fs.wrapper_write(encode)

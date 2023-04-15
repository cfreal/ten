import hashlib

from tenlib.transform.generic import multiform


@multiform
def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


@multiform
def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


@multiform
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

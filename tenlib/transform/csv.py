import csv
import io
from tenlib.struct.proxy import TenList, TenDict
from tenlib.transform.generic import multiform


def encode(data, fieldnames=None, **fmtparams):
    """Writes CSV data from `data` to a string and returns it."""
    with io.StringIO() as stream:
        _stream_write(stream, data, fieldnames=fieldnames, **fmtparams)
        return stream.getvalue()


def write(file, data, fieldnames=None, **fmtparams):
    """Writes CSV data from `data` to a file."""
    with open(file, "w") as stream:
        return _stream_write(stream, data, fieldnames=fieldnames, **fmtparams)


def _deduce_fieldnames(data):
    """Find out fieldnames from given data, which is a list of dicts."""
    # We want to preserve order, so we can't use a set
    keys = {key: None for row in data for key in row.keys()}

    return list(keys.keys())


@multiform
def decode(data: str, **fmtparams) -> TenList:
    """Reads CSV data from `data` and returns each row."""
    with io.StringIO(data) as stream:
        return _stream_read(stream, **fmtparams)


def read(file, **fmtparams) -> TenList:
    """Reads CSV data from a file and returns each row."""
    with open(file, newline="") as stream:
        return _stream_read(stream, **fmtparams)


def _stream_read(stream, **fmtparams) -> TenList:
    """Reads CSV data from a stream and returns each row."""
    reader = csv.DictReader(stream, **fmtparams)
    return TenList([TenDict(row) for row in reader])


def _stream_write(stream, data, fieldnames=None, **fmtparams):
    if data and isinstance(data[0], dict):
        if fieldnames is None:
            fieldnames = _deduce_fieldnames(data)
        writer = csv.DictWriter(stream, fieldnames=fieldnames, **fmtparams)
        writer.writeheader()
        writer.writerows(data)
    else:
        writer = csv.writer(stream, **fmtparams)
        if fieldnames:
            writer.writerow(fieldnames)
        writer.writerows(data)

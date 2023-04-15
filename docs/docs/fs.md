# Filesystem (files, directories)

Quickly access and edit files. Refer to [`tenlib.fs`'s documentation](../tenlib/fs.html) for details.

The FS module has a few functions to quickly manipulate files:

```python
from ten import *

if exists("/tmp/test.txt"):
    data = read_text("/tmp/test.txt")
else:
    data = compute()
    write("/tmp/test.txt", data)
```

For advanced usage, use [`Path`](../tenlib/fs.html#tenlib.fs.Path) instead:

```python
path = Path("/tmp/test.txt")

if path.exists():
    data = path.read_text()
else:
    data = compute()
    path.write(data)
```

## Files

Create a `Path` object, a wrapper for `pathlib.Path` with a few additional methods.

```python
p = Path("/tmp/test.txt")
```

### Read and write

To read data as a string or bytes:

```python
contents = p.read_text()
contents = p.read_bytes()
```

To write data as bytes or string, use the `Path.write()` method.

```python
p.write(b"contents")
```

```python
p.write("contents")
```

To append, use `Path.append()`:

```python
p.append("additional contents")
```

### Creating a file

Create a file using `Path.touch()`.

```python
p.touch()
```

To create the whole directory hierarchy, use `parents=True`, or simply `ptouch()`:

```python
p = Path("/tmp/long/path/to/file")

# equivalent
p.touch(parents=True)
p.ptouch()
```

The call returns the instance, so it can be chained with `write()`, for instance.

```python
p.ptouch().write("data")
```

## Directories

To go through a directory, use `glob()` or `rglob()`.

```python
dir = Path("./dir")

for file in dir.rglob("**/*.py"):
    msg_info(f"Found python file: {file}")
    process_file(file)
```

Create a directory using `mkdir()`:

```python
dir = Path("./dir")
dir.mkdir()
```

To create the parent directories as well, use `mkdir(parent=True)`.
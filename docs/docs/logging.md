# Logging

Logging can be stored in a file and displayed on the console.

A `log` object is available:

```python
>>> log.info("A log message")
>>> log.debug("Another log message")
```

Alternatively, you can obtain a log object using `logger()`:

```python
class Something:
    def __init__(self):
        self.log = logger(self.__class__.__name__)
```

## File logging

To write log data to a file, use `logging.set_file()` and `logging.set_level()`:

```python
>>> logging.set_file("ten.log")
>>> logging.set_level(DEBUG)
```

It can be disabled by calling any of these functions with `None`. For instance:

```python
>>> logging.set_file(None)
```

## CLI logging

To display log messages to the CLI, use `logging.set_cli_level()`:

```python
>>> logging.set_cli_level("INFO")
```

Disable it using:

```python
>>> logging.set_cli_level(None)
```
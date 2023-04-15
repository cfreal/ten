"""Classes relative to keeping track of time and displaying it efficiently.

`watch` and `stopwatch`'s `str` method will display the time in a readable
format, meaning you can instantiate them once and then print them whenever you
need.

    >>> s = stopwatch()
    >>> print(s)
    '00:00:00'
    >>> w = watch()
    >>> print(w)
    '12:56:31'
    >>> ...
    >>> print(s)
    '00:00:10'

The display format can be set while instantiating the object. The three
instantiations here are equivalent:

    >>> # Minute + Seconds display format
    >>> s = stopwatch('MS')
    >>> s = stopwatch(timeformat['MS'])
    >>> s = stopwatch('%M:%S')
    >>> print(s)
    '00:00'
    >>> 

Calling `format` on instances of this object allows you to choose the way you
want them formatted:

    >>> w = watch()
    >>> f'{w:HMS}'
    '12:56:32'
    >>> f'{w:%y-%m-%d %H:%M:%S}'
    '21-01-25 12:56:32'

"""
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


__all__ = ["timeformat", "watch", "stopwatch"]


class timeformat(Enum):
    """Different useful formats for `time.strftime`.
    See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    """

    MS = "%M:%S"
    MSu = "%M:%S.%f"
    HMS = "%H:%M:%S"
    HMSu = "%H:%M:%S.%f"
    DHMS = "%y-%m-%d %H:%M:%S"


class TimeHandler(ABC):
    def __init__(self, format: timeformat = timeformat["HMS"]):
        """Initializes the object.

        Args:
            format: the format that will be used to display the stopwatch when
                `str()` is called.
        """
        self.__timeformat = self._to_format_str(format)

    @staticmethod
    def _to_format_str(format) -> str:
        """Converts `format` into a time format string."""
        if isinstance(format, timeformat):
            return format.value

        try:
            return timeformat[format].value
        except KeyError:
            return format

    @abstractmethod
    def _to_datetime(self) -> datetime:
        """Returns a datetime representation of the object."""

    def __str__(self):
        return format(self, "")

    def __format__(self, format):
        if format:
            format = self._to_format_str(format)
        else:
            format = self.__timeformat
        return self._to_datetime().strftime(format)


class watch(TimeHandler):
    """Instances of this class keep track of the current time.

    >>> c = watch()
    >>> print(c)
    '12:34:07'
    >>> time.sleep(2)
    >>> print(c)
    '12:34:09'
    >>> c = watch('HMSu')
    >>> time.sleep(2)
    >>> print(c)
    '12:34:11.000004'
    >>> f'{c:%y-%m-%d %H:%M:%S}'
    '21-01-14 12:34:11'
    """

    def _to_datetime(self):
        return datetime.today()


class stopwatch(TimeHandler):
    """Instances of this class keep track of elapsed time after their
    initialization.

    >>> c = stopwatch()
    >>> print(c)
    '00:00:00'
    >>> time.sleep(2)
    >>> print(c)
    '00:00:02'
    >>> c = stopwatch('HMSu')
    >>> time.sleep(2)
    >>> print(c)
    '00:02:00.000004'
    >>> f'{c:%M:%S}'
    '00:02'
    """

    def __init__(self, format: timeformat = timeformat["HMS"]):
        super().__init__(format)
        self.start()

    def tick(self):
        return time.monotonic()

    def start(self):
        """Restarts the stopwatch."""
        self._start = self.tick()

    def elapsed(self) -> float:
        """Returns the elapsed time since the stopwatch was started."""
        return self.tick() - self._start

    def _to_datetime(self):
        return datetime.utcfromtimestamp(self.elapsed())

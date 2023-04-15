from __future__ import annotations

from collections.abc import MutableMapping
from collections import UserList


__all__ = [
    "TenDict",
    "TenList",
    "wrap_object",
]


def wrap_object(obj):
    """Converts an object into a proxy item. `dict`s are converted to a
    `TenDict`, `list`s to a `TenList`.
    """
    if type(obj) is list:
        return TenList(obj)
    if type(obj) is dict:
        return TenDict(obj)
    return obj


class GetItemProxy:
    """A proxy class that converts sequences and dicts to their proxified
    equivalent, to access items as properties recursively.
    """

    def __getitem__(self, key):
        return wrap_object(super().__getitem__(key))


# We would happily use collections.UserDict here, but since the internal object
# is referenced as `data`, we wouldn't be able to do wrapper.data = 'something'.
class UserDict(MutableMapping):
    __wo__: dict

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
            wo = args[0]
        else:
            wo = dict(*args, **kwargs)
        self.__wo__ = wo

    def __len__(self):
        return len(self.__wo__)

    def __getitem__(self, key):
        if key in self.__wo__:
            return self.__wo__[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)

    def __setitem__(self, key, item):
        self.__wo__[key] = item

    def __delitem__(self, key):
        del self.__wo__[key]

    def __iter__(self):
        return iter(self.__wo__)

    # Modify __contains__ to work correctly when __missing__ is present
    def __contains__(self, key):
        return key in self.__wo__

    # Now, add the methods in dicts but not in MutableMapping
    def __repr__(self):
        return repr(self.__wo__)

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["__wo__"] = self.__dict__["__wo__"].copy()
        return inst

    def copy(self):
        if self.__class__ is UserDict:
            return UserDict(self.__wo__.copy())
        import copy

        data = self.__wo__
        try:
            self.__wo__ = {}
            c = copy.copy(self)
        finally:
            self.__wo__ = data
        c.update(self)
        return c

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d


class TenDict(GetItemProxy, UserDict):
    """Proxy for `dict` that allows you to access items as properties
    recursively and provides other helpers.

    Examples:

        Items can be accessed as attributes:

        >>> some = TenDict({'a': 'b', 'c', 'd'})
        >>> some.a
        'b'
        >>> some.c = 'e'
        >>> some.c
        'e'

        This property is recursive:

        >>> deep = TenDict({
        ...     'some_list': [
        ...         {'some_dict': {
        ...             'a_value': 3
        ...         }}
        ...     ]
        ... })
        >>> deep.some_list[0].some_dict.a_value
        3

        Helpers are available:

        >>> some = TenDict({'key1': 'value1', 'key2': 'value2'})
        >>> some.setdefaults({'key2': 'value2_new', 'key3': 'value3'})
        TenDict({'key1': 'value1', 'key2': 'value2', 'key3': 'value3'})
        >>> some.keep('key1', 'key3')
        TenDict({'key1': 'value1', 'key3': 'value3'})

        The instance is a proxy, modifying the `TenDict` instance modifies the
        original `dict` as well.

        >>> some_dict = {'a': 'b', 'c': 'd'}
        >>> proxy = TenDict(some_dict)
        >>> proxy['e'] = 'f'
        >>> proxy
        TenDict({'a': 3, 'c': 'd', 'e': 'f'})
        >>> some_dict
        {'a': 3, 'c': 'd', 'e': 'f'}
    """

    __annotations_cache__ = {}

    def __getattr__(self, name):
        # This means that the expected attribute is annotated but not defined
        if name in self._defined_annotations():
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    @classmethod
    def _defined_annotations(cls):
        """Returns a set containing every annotation of the base class and its
        superclasses.
        """
        try:
            return cls.__annotations_cache__[cls]
        except KeyError:
            pass

        cache = cls.__annotations_cache__[cls] = set()

        for scls in cls.__mro__:
            try:
                cache |= set(scls.__annotations__.keys())
            except AttributeError:
                pass

        return cache

    def __setattr__(self, name, value):
        if name in self._defined_annotations() or name in dir(self):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name):
        if name in self._defined_annotations() or name in dir(self):
            return super().__delattr__(name)

        try:
            del self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __repr__(self):
        return f"{type(self).__name__}({self.__wo__!r})"

    def update(self, *args, **kwargs) -> TenDict:
        """Same as `dict.update()`, but returns the instance."""
        self.__wo__.update(*args, **kwargs)
        return self

    def setdefaults(self, other={}, **kwargs) -> TenDict:
        """Generalizes `dict.setdefault()` for several values, and returns the
        instance.

        >>> some = TenDict({'key1': 'value1', 'key2': 'value2'})
        >>> some.setdefaults({'key2': 'value2_new', 'key3': 'value3'})
        TenDict({'key1': 'value1', 'key2': 'value2', 'key3': 'value3'})
        """
        kwargs.update(other)
        for k, v in kwargs.items():
            self.setdefault(k, v)
        return self

    def keep(self, *to_keep) -> TenDict:
        """Returns a `TenDict` that contains only the given keys.

        >>> some = TenDict({'a': 1, 'b': 2, 'c': 3, 'd': 4})
        >>> some.keep('a', 'd')
        TenDict({'a': 1, 'd': 4})
        """
        new = TenDict()

        for k in to_keep:
            try:
                new[k] = self[k]
            except KeyError:
                pass

        return new


class TenList(GetItemProxy, UserList):
    def __init__(self, lst=None):
        if lst is None:
            self.data = []
        elif isinstance(lst, list):
            self.data = lst
        else:
            self.data = list(lst)

    def __repr__(self):
        return f"{type(self).__name__}({self.data!r})"

import yaml

from tenlib.struct import storable
from tenlib.transform import color as _color


class Map(storable.Storable):
    """Represents a map of (for instance) the database schema.
    A map can be though of as a number of top level nodes, each containing a few
    nodes, and so on.
    For instance, a database map would have database names as top level nodes,
    and each of those would have tables, which would all have columns.

    To make the implementation easier, leaves are nodes with no children.
    Also, node names are unique.
    """

    _color = (_color.red, _color.yellow, _color.blue, str)
    _DICT_CLS = dict

    def __init__(self, items=None):
        if items is None:
            self.items = self._DICT_CLS()
            return
        if isinstance(items, self._DICT_CLS):
            self.items = items
            return

        self.items = self._DICT_CLS()

        for row in items:
            current_item = self.items
            for cell in row:
                current_item = current_item.setdefault(cell, self._DICT_CLS())

    def __str__(self):
        return self._str(self.items, 0)

    def _str(self, items, depth):
        pad = "  " * depth
        output = ""

        for key, value in items.items():
            try:
                color = self._color[depth]
            except IndexError:
                color = self._color[-1]

            output += "{}{}\n{}".format(
                pad, color(str(key)), self._str(value, depth + 1)
            )
        return output

    def store_yaml(self, filename):
        with open(filename, "w") as file:
            yaml.dump(self.items, file, default_flow_style=False)

    def __add__(self, other):
        """Merges two maps."""
        new = type(self)()
        new += self
        new += other
        return new

    def __iadd__(self, other):
        """Merges two maps."""
        items = self._DICT_CLS()
        self._merge_dicts(items, self.items)
        self._merge_dicts(items, other.items)
        self.items = items
        return self

    def _merge_dicts(self, one, two):
        for key, value in two.items():
            self._merge_dicts(one.setdefault(key, self._DICT_CLS()), value)

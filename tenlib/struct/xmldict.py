from __future__ import annotations

import xml.etree.cElementTree as ElementTree

from tenlib.struct.proxy import TenDict, TenList

__all__ = ["XMLDict"]


class XMLDict(TenDict):
    """Converts XML data as a dictionary.
    If a sub item is only represented once (e.g. `<rank>` tags in the example),
    they will be represented as a single item. Otherwise (e.g. `<country>`),
    they are represented as a list. Tag attributes are available as the attrs
    property. To make sure you can manipulate any item as a list, a `list()`
    helper method is available. This is useful in a few cases. For instance, if
    you are expecting a list of `<users>` tags, but in this case only one user
    is there, `xml.user[0]` will fail. Use `xml.user.list()[0]` to make sure you
    have a list.

    Example:
        >>> data = '''<?xml version="1.0"?>
        ... <data>
        ...     <country name="Liechtenstein">
        ...         <rank>1</rank>
        ...         <year>2008</year>
        ...         <gdppc>141100</gdppc>
        ...         <neighbor name="Austria" direction="E"/>
        ...         <neighbor name="Switzerland" direction="W"/>
        ...     </country>
        ...     <country name="Singapore">
        ...         <rank>4</rank>
        ...         <year>2011</year>
        ...         <gdppc>59900</gdppc>
        ...         <neighbor name="Malaysia" direction="N"/>
        ...     </country>
        ...     <country name="Panama">
        ...         <rank>68</rank>
        ...         <year>2011</year>
        ...         <gdppc>13600</gdppc>
        ...         <neighbor name="Costa Rica" direction="W"/>
        ...         <neighbor name="Colombia" direction="E"/>
        ...     </country>
        ... </data>'''
        >>> xml = XMLDict.build(data)
        >>> xml.country[0].rank
        '1'
        >>> xml.country[2].neighbor[0]
        XMLDict(attrs={'direction': 'W', 'name': 'Costa Rica'}, {})
        >>> xml.country[1].year.list()[0]
        '2011'
        >>>
    """

    attrs: TenDict = None

    def list(self) -> list[XMLDict]:
        return [self]

    def __repr__(self):
        return (
            f"<{type(self).__name__} "
            f"attrs={self.attrs!r}, "
            f"children={list(self.keys())}"
            f">"
        )

    @classmethod
    def build(cls, string) -> XMLDict:
        return cls._build(ElementTree.XML(string))

    @classmethod
    def _build(cls, current: ElementTree.Element) -> XMLDict:
        attrs = TenDict(current.attrib)
        if len(current) == 0 and current.text is not None:
            element = XMLString(current.text)
            element.attrs = attrs
            return element

        element = XMLDict()
        element.attrs = attrs

        for child in current:
            element.setdefault(child.tag, XMLList()).append(cls._build(child))

        # Simplify single-element lists by only keeping said element
        for tag, children in element.items():
            if len(children) == 1:
                element[tag] = children[0]

        return element


class XMLList(TenList):
    def list(self) -> list:
        return self


class XMLString(str):
    def list(self) -> list[XMLString]:
        return [self]

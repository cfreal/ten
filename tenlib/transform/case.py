import re

from tenlib.transform.generic import multiform


@multiform
def camel(name: str) -> str:
    """Converts `under_score` names into `CamelCase`."""
    return re.sub("(_|^)([a-z])", lambda x: x.group(2).upper(), name)


@multiform
def underscore(name: str) -> str:
    """Converts `CamelCase` names into `under_score`.
    This assumes the first letter is uppercased.
    """
    return re.sub("([A-Z])", lambda x: "_" + x.group(1).lower(), name)[1:]

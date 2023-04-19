from tenlib.transform.generic import to_str, multiform
from tenlib import fs


@multiform
def split(
    data: str,
    separator: str = "\n",
    *separators: str,
    strip: bool = False,
    empty: bool = False,
) -> list:
    """Splits the `data` with the first `separator`.
    Then, splits every row of the `data` with the second `separator`, and so on.

    Args:
        data: data to split
        separator (str): first separator to split data with
        *separators (str): other separators
        strip (bool): Whether to strip the rows after the last separation
        empty (bool): Whether to keep the empty rows after the first separation

    Example:
        >>> data = '1:2:  3\\n4:5:6  \\n'
        >>> split(data, '\\n', ':')
        [['1', '2', '  3'], ['4', '5', '6  '], []]
        >>> split(data, '\\n', ':', strip=True)
        [['1', '2', '  3'], ['4', '5', '6'], []]
        >>> split(data, '\\n', ':', empty=False)
        [['1', '2', '  3'], ['4', '5', '6  ']]
    """
    separator = to_str(separator)
    data = data.split(separator)

    if not empty:
        data = [row for row in data if row]

    if not separators:
        if strip:
            return [row.strip() for row in data]
        return data

    # empty is not transmitted, on purpose
    return split(data, *separators, strip=strip)


def join(data, separator="\n", *separators) -> str:
    """Merges the deepest list with the last `separator`. Then, merges the
    obtained sublist with the second to last `separator`, and so on.

    Example:
        >>> data = [[1, 2, 3], [4, 5, 6]]
        >>> join(data, '\\n', ':')
        '1:2:3\\n4:5:6'
    """
    data = to_str(data)
    separator = to_str(separator)

    if not separators:
        return separator.join(data)
    return separator.join(join(row, *separators) for row in data)


def map(table, **functions) -> list:
    """For every column *n* in the table, if the keyword argument `_n` was
    given, apply it to every cell of said column.

    Args:
        table (list): A list of lists (a table)
        **functions: an `_n`: `func` mapping

    Examples:
        >>> transform.table.map(
        ...     [[1, 2, 3], [4, 5, 6]],
        ...     _0=lambda x: x+1,
        ...     _2=lambda x: x*2
        ... )
        [2, 2, 6], [5, 5, 12]
    """
    identity = lambda x: x
    processed_table = []
    for row in table:
        processed_row = []
        for i, cell in enumerate(row):
            function = functions.get(f"_{i}") or functions.get(i)
            if function:
                cell = function(cell)
            processed_row.append(cell)
        processed_table.append(processed_row)
    return processed_table


read = fs.wrapper_read(split)
write = fs.wrapper_write(join)

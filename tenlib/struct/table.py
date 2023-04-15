import csv
import io

from rich.table import Table as RichTable

from tenlib.struct import storable
from tenlib.transform import generic


class Table(storable.Storable):
    """Represents a table.

    Args:
        columns (list): Column names
        data (list[list]): Data as a list of rows

    Examples:

        Build a table and display it:

            >>> r = Table(
            ...     ['first', 'second', 'third'],
            ...     [['1', '2', '3'], ['4', '5', '6']]
            ... )
            >>> print(r)
            ┌───────┬────────┬───────┐
            │ first │ second │ third │
            ├───────┼────────┼───────┤
            │     1 │      2 │     3 │
            │     4 │      5 │     6 │
            └───────┴────────┴───────┘

    """

    def __init__(self, columns: list, data: list[list]):
        self.columns = columns
        self.data = data

    def _to_str(self, cell):
        """Converts data of various types into a string."""
        if isinstance(cell, str):
            return cell
        if cell is None:
            return "<None>"
        if isinstance(cell, bytes):
            try:
                return cell.decode()
            except UnicodeDecodeError:
                pass
        return str(cell)

    def _get_title(self):
        """Gets a title to prefix the table with."""
        return None

    def __str__(self):
        columns = [self._to_str(column) for column in self.columns]
        data = [[self._to_str(cell) for cell in row] for row in self.data]
        nb_rows = len(self.data)

        table = RichTable(
            *columns,
            title=self._get_title(),
            caption=f"{nb_rows} rows in set",
            caption_justify="right",
        )

        for row in data:
            table.add_row(*row)

        s = io.StringIO()

        from rich import print

        print(table, file=s)
        s.seek(0)

        return s.read()

    def store_as_csv(self, filename):
        with open(filename, "w") as file:
            columns = [str(c) for c in self.columns]
            data = generic.to_str(self.data)
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(data)

import io
from threading import Lock
import unittest
import sys
from tenlib import flow

from tenlib.flow.console import get_console
from tenlib.flow.messageformatter import NewschoolMessageFormatter

__all__ = ["TenTestCase"]


class TenTestCase(unittest.TestCase):
    def setUp(self) -> None:
        sys.argv = ["./main.py"]
        sys.argc = len(sys.argv)
        flow.set_message_formatter(NewschoolMessageFormatter())
        console = get_console()
        self.__old_console_file = console.file
        console.file = io.StringIO()
        console.record = True

    def tearDown(self) -> None:
        console = get_console()
        # Strip buffer
        console.export_text()
        console.record = False
        console.file = self.__old_console_file
        return super().tearDown()

    def _read_output(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except SystemExit:
            pass
        data = get_console().export_text()
        return data

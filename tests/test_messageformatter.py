import io
import tempfile
import unittest

from rich.text import Text

from tenlib.flow.console import get_console
from tenlib.flow.messageformatter import *

from tests.ten_testcases import *


class TestMessageFormatter(TenTestCase):
    def test_print_no_params(self):
        out = OldschoolMessageFormatter()
        out.print()
        self.assertEqual(get_console().export_text(), "\n")

    # The two next tests are redundant with TestFlowMessageFormatter, but it does not
    # hurt

    def test_text_object_does_not_get_rendered(self):
        out = OldschoolMessageFormatter()
        out.success(Text("[b]Markup"))
        self.assertEqual(get_console().export_text(), "[+] [b]Markup\n")

    def test_print_can_receive_several_positional_arguments(self):
        out = OldschoolMessageFormatter()
        out.success("first", "second", 3, "forth")
        self.assertEqual(get_console().export_text(), "[+] first second 3 forth\n")

    def test_clear(self):
        out = OldschoolMessageFormatter()

        out.clear()

        self.assertEqual(get_console().export_text(), "")

    def test_bin_print(self):
        out = OldschoolMessageFormatter()

        with tempfile.TemporaryFile("a+") as h:
            get_console().file = h
            out.bin_print(b"ABC")
            h.seek(0)
            data = h.read()

        self.assertEqual(get_console().export_text(), "")
        self.assertEqual(data, "ABC")

    def test_bin_print_not_bytes(self):
        out = OldschoolMessageFormatter()

        with tempfile.TemporaryFile("a+") as h:
            get_console().file = h
            with self.assertRaisesRegex(
                TypeError, r"MessageFormatter\.bin_print\(\) expects a byte-like object"
            ):
                out.bin_print("ABC")

    def _test_all_status_for_cls(self, cls: type[MessageFormatter]):
        out = cls()

        out.success("OUTput")
        out.info("OUTput")
        out.failure("OUTput")
        out.error("OUTput")
        out.warning("OUTput")
        out.debug("OUTput")
        out.print("OUTput")

        return get_console().export_text(styles=True)

    def test_slickoutput_status(self):
        data = self._test_all_status_for_cls(SlickMessageFormatter)
        self.assertEqual(
            data,
            "\x1b[1;32m|\x1b[0m OUTput\n\x1b[1;34m|\x1b[0m OUTput\n\x1b[1;31m|\x1b[0m OUTput\n\x1b[1;31m|\x1b[0m OUTput\n\x1b[1;33m|\x1b[0m OUTput\n\x1b[1;35m|\x1b[0m OUTput\nOUTput\n",
        )

    def test_newschooloutput_status(self):
        data = self._test_all_status_for_cls(NewschoolMessageFormatter)
        self.assertEqual(
            data,
            "\x1b[1;32m✔\x1b[0m OUTput\n\x1b[1;34m·\x1b[0m OUTput\n\x1b[1;31m✖\x1b[0m OUTput\n\x1b[1;31m✖\x1b[0m OUTput\n\x1b[1;33m▲\x1b[0m OUTput\n\x1b[1;35m⊙\x1b[0m OUTput\nOUTput\n",
        )

    def test_oldschooloutput_status(self):
        data = self._test_all_status_for_cls(OldschoolMessageFormatter)
        self.assertEqual(
            data,
            "[\x1b[32m+\x1b[0m] OUTput\n[\x1b[34m*\x1b[0m] OUTput\n[\x1b[31m-\x1b[0m] OUTput\n[\x1b[31mx\x1b[0m] OUTput\n[\x1b[33m!\x1b[0m] OUTput\n[\x1b[35mD\x1b[0m] OUTput\nOUTput\n",
        )

    def test_otheroldschooloutput_status(self):
        data = self._test_all_status_for_cls(OtherOldschoolMessageFormatter)
        self.assertEqual(
            data,
            "\x1b[1;32m[+]\x1b[0m OUTput\n\x1b[1;34m[*]\x1b[0m OUTput\n\x1b[1;31m[-]\x1b[0m OUTput\n\x1b[1;31m[x]\x1b[0m OUTput\n\x1b[1;33m[!]\x1b[0m OUTput\n\x1b[1;35m[D]\x1b[0m OUTput\nOUTput\n",
        )

    def test_iconoutput_status(self):
        data = self._test_all_status_for_cls(IconMessageFormatter)
        self.assertEqual(
            data,
            "\x1b[1;32;40m ✔ \x1b[0m OUTput\n\x1b[1;34;40m · \x1b[0m OUTput\n\x1b[1;31;40m ✖ \x1b[0m OUTput\n\x1b[1;31;40m ✖ \x1b[0m OUTput\n\x1b[1;33;40m ▲ \x1b[0m OUTput\n\x1b[1;35;40m ⊙ \x1b[0m OUTput\nOUTput\n",
        )


if __name__ == "__main__":
    unittest.main()

import argparse
import sys

from tests.ten_testcases import TenTestCase
import unittest
import tempfile
import time
from rich.text import Text
import io

from unittest import mock

from tenlib.flow.messageformatter import MessageFormatter, NewschoolMessageFormatter
from tenlib import flow, exception, fs, logging


class TestFlowPrototype(TenTestCase):
    def _get_args(self, func, *args):
        sys.argv = ["./main"] + list(args)
        return flow._prototype_to_args(func)

    @unittest.mock.patch("sys.stderr")
    def test_no_args(self, stderr):
        def f_no_args():
            pass

        with self.assertRaises(SystemExit):
            self._get_args(f_no_args, "1234", "456")

        with self.assertRaises(SystemExit):
            self._get_args(f_no_args, "-a")

    @unittest.mock.patch("sys.stderr")
    def test_no_optional(self, stderr):
        def f_no_optional(a, b, c):
            pass

        with self.assertRaises(SystemExit):
            self._get_args(f_no_optional, "a")

        try:
            args, kwargs = self._get_args(f_no_optional, "a", "b", "c")
        except SystemExit:
            self.fail("Should work")

        self.assertEqual(args, ["a", "b", "c"])
        self.assertEqual(kwargs, {})

    @unittest.mock.patch("sys.stderr")
    def test_typed_int(self, stderr):
        def f_typed_int(a=3):
            pass

        sys.argv = ["./main", "-a", "a"]

        with self.assertRaises(SystemExit):
            self._get_args(f_typed_int, "-a", "a")

        try:
            args, kwargs = self._get_args(f_typed_int, "-a", "1234")
        except SystemExit:
            self.fail("Should work")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": 1234})

    @unittest.mock.patch("sys.stderr")
    def test_typed_none(self, stderr):
        def f_typed_none(a=None):
            pass

        with self.assertRaises(SystemExit):
            self._get_args(f_typed_none, "-a", "a", "b")

        try:
            args, kwargs = self._get_args(f_typed_none, "-a", "1234")
        except SystemExit:
            self.fail("Should work")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": "1234"})

    @unittest.mock.patch("sys.stderr")
    def test_typed_bool_no_default(self, stderr):
        def f_bool_false(a: bool):
            pass

        try:
            args, kwargs = self._get_args(f_bool_false, "-a")
        except SystemExit:
            self.fail("Should work")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": True})

        try:
            args, kwargs = self._get_args(f_bool_false)
        except SystemExit:
            self.fail("Should work")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": False})

    @unittest.mock.patch("sys.stderr")
    def test_typed_bool_default_true(self, stderr):
        def f_bool_true(a: bool = True):
            pass

        try:
            args, kwargs = self._get_args(f_bool_true, "-a")
        except SystemExit:
            self.fail("Should work")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": False})

        try:
            args, kwargs = self._get_args(f_bool_true)
        except SystemExit:
            self.fail("Should work")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": True})

    @unittest.mock.patch("sys.stderr")
    def test_default_list(self, stderr):
        def f_typed_list(a=[]):
            pass

        try:
            args, kwargs = self._get_args(f_typed_list, "-a", "1234")
        except SystemExit:
            self.fail("One list argument")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": ["1234"]})

        try:
            args, kwargs = self._get_args(f_typed_list, "-a", "1234", "5678")
        except SystemExit:
            self.fail("Several list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": ["1234", "5678"]})

        try:
            args, kwargs = self._get_args(f_typed_list, "-a")
        except SystemExit:
            self.fail("No list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": []})

    @unittest.mock.patch("sys.stderr")
    def test_default_list_int(self, stderr):
        def f_typed_list_int(a=[123, 456]):
            pass

        try:
            args, kwargs = self._get_args(f_typed_list_int, "-a", "1234")
        except SystemExit:
            self.fail("One list argument")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": [1234]})

        try:
            args, kwargs = self._get_args(f_typed_list_int, "-a", "1234", "5678")
        except SystemExit:
            self.fail("Several list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": [1234, 5678]})

        try:
            args, kwargs = self._get_args(f_typed_list_int, "-a")
        except SystemExit:
            self.fail("No list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": []})

    @unittest.mock.patch("sys.stderr")
    def test_typed_bool_list(self, stderr):
        def f_typed_list_bool(a: list[bool]):
            pass

        try:
            args, kwargs = self._get_args(
                f_typed_list_bool, "-a", "1", "0", "tRUe", "fALse", "NO", "YES"
            )
        except SystemExit:
            self.fail("One list argument")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": [True, False, True, False, False, True]})

    @unittest.mock.patch("sys.stderr")
    def test_typed_bool_list_invalid_input(self, stderr):
        def f_typed_list_bool(a: list[bool]):
            pass

        with self.assertRaises(SystemExit) as cm:
            args, kwargs = self._get_args(f_typed_list_bool, "-a", "1", "0", "blu")

        self.assertEqual(
            str(cm.exception.__context__),
            "argument -a: invalid str_to_bool value: 'blu'",
        )

    @unittest.mock.patch("sys.stderr")
    def test_typed_int_list(self, stderr):
        def f_typed_list_int(a: list[int]):
            pass

        try:
            args, kwargs = self._get_args(f_typed_list_int, "-a", "1234")
        except SystemExit:
            self.fail("One list argument")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": [1234]})

        try:
            args, kwargs = self._get_args(f_typed_list_int, "-a", "1234", "5678")
        except SystemExit:
            self.fail("Several list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": [1234, 5678]})

        try:
            args, kwargs = self._get_args(f_typed_list_int, "-a")
        except SystemExit:
            self.fail("No list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": []})

    @unittest.mock.patch("sys.stderr")
    def test_untyped_list(self, stderr):
        def f_typed_list(a: list):
            pass

        try:
            args, kwargs = self._get_args(f_typed_list, "-a", "1234")
        except SystemExit:
            self.fail("One list argument")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": ["1234"]})

        try:
            args, kwargs = self._get_args(f_typed_list, "-a", "1234", "5678")
        except SystemExit:
            self.fail("Several list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": ["1234", "5678"]})

        try:
            args, kwargs = self._get_args(f_typed_list, "-a")
        except SystemExit:
            self.fail("No list arguments")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": []})

    @unittest.mock.patch("sys.stderr")
    def test_with_forced_keywords(self, stderr):
        def main(a, *, b, c):
            pass

        try:
            args, kwargs = self._get_args(main, "a", "-b", "B", "-c", "C")
        except SystemExit:
            self.fail("b and c should be optional args")

        self.assertEqual(args, ["a"])
        self.assertEqual(kwargs, {"b": "B", "c": "C"})

    @unittest.mock.patch("sys.stderr")
    def test_same_shortcut_letter(self, stderr):
        def main(*, param1, param2):
            pass

        try:
            args, kwargs = self._get_args(main, "-p", "1", "-P", "2")
        except SystemExit:
            self.fail("Same name shortcut")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"param1": "1", "param2": "2"})

    @unittest.mock.patch("sys.stderr")
    def test_shortcut_letter_taken_already(self, stderr):
        def main(*, param1, param2, param3):
            pass

        try:
            args, kwargs = self._get_args(main, "-p", "1", "-P", "2", "--param3", "3")
        except SystemExit:
            self.fail("Same name shortcut")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"param1": "1", "param2": "2", "param3": "3"})

    @unittest.mock.patch("sys.stderr")
    def test_shortcut_letter_taken_already_by_help(self, stderr):
        def main(*, host):
            pass

        try:
            args, kwargs = self._get_args(main, "-H", "hostname")
        except SystemExit:
            self.fail("Same name shortcut")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"host": "hostname"})

    @unittest.mock.patch("sys.stderr")
    def test_cannot_have_a_help_parameter(self, stderr):
        def main(*, help):
            pass

        with self.assertRaises(argparse.ArgumentError) as cm:
            args, kwargs = self._get_args(main)

        self.assertEqual(
            str(cm.exception), "Cannot use 'help' as an entry parameter name"
        )

    def test_prototype_star_args_free(self):
        def main(a, *args):
            pass

        args, kwargs = self._get_args(main, "a", "b", "c")

        self.assertEqual(args, ["a", "b", "c"])
        self.assertEqual(kwargs, {})

    def test_prototype_star_args_int(self):
        def main(a, *args: int):
            pass

        args, kwargs = self._get_args(main, "a", "1", "2")

        self.assertEqual(args, ["a", 1, 2])
        self.assertEqual(kwargs, {})

    def test_prototype_star_args_and_following_param_is_kw_only(self):
        def main(a, *args: int, b):
            pass

        args, kwargs = self._get_args(main, "a", "1", "2", "-b", "bvalue")

        self.assertEqual(args, ["a", 1, 2])
        self.assertEqual(kwargs, {"b": "bvalue"})

    def test_none_default_does_not_condition_type(self):
        def main(a=None):
            pass

        args, kwargs = self._get_args(main, "-a", "1")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": "1"})

    def test_none_default_does_not_condition_type_for_int_type(self):
        def main(a: int = None):
            pass

        args, kwargs = self._get_args(main, "-a", "1")

        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": 1})

    def test_default_type_is_not_raw(self):
        class X:
            pass

        def main(a: X):
            pass

        with self.assertRaises(TypeError) as cm:
            self._get_args(main, "a", "1")

        self.assertEqual(str(cm.exception), "Unsupported type X for parameter a")

    def test_path_is_valid_type(self):
        def main(a: fs.Path):
            self.assertIsInstance(a, fs.Path)
            self.assertEqual(str(a), "/etc/passwd")

        args, kwargs = self._get_args(main, "/etc/passwd")
        self.assertIsInstance(args[0], fs.Path)
        self.assertEqual(str(args[0]), "/etc/passwd")

    def test_string_annotation_is_properly_resolved(self):
        def main(a: "int"):
            ...

        args, kwargs = self._get_args(main, "1")
        self.assertEqual(args[0], 1)

    def test_string_annotation_list_is_properly_resolved(self):
        def main(a: "list[int]"):
            ...

        args, kwargs = self._get_args(main, "-a", "1", "2")
        self.assertEqual(kwargs["a"], [1, 2])

    def test_string_annotation_is_not_used_as_string(self):
        def main(a: "str", b: "int"):
            ...

        try:
            self._get_args(main, "abc", "123")
        except:
            self.fail("Got an exception with a 'str' type")

    def test_entry_with_class_takes_hints_from_init(self):
        class Exploit:
            abc: str

            def __init__(self, abc: int = 3):
                pass

            def run(self):
                pass

        args, kwargs = self._get_args(Exploit, "-a", "1")
        self.assertEqual(kwargs["abc"], 1)


class TestFlowArg(TenTestCase):
    def test_arg(self):
        @flow.arg("a", "documentation for a")
        def func(a: int):
            pass

        self.assertEqual(func.__ten_doc__["a"], "documentation for a")

    @unittest.mock.patch("sys.stdout")
    def test_arg_is_in_help(self, stdout):
        sys.stdout = x = io.StringIO()

        @flow.entry
        @flow.arg("a", "documentation for a")
        def main(a: int = False):
            pass

        sys.argv = ["./a", "--help"]
        try:
            main()
        except SystemExit:
            pass
        x.seek(0)
        self.assertIn("documentation for a", x.read())


class TestFlowDocToDesc(TenTestCase):
    def test_standard(self):
        def func():
            """Documentation with a strange indentation, due to this list:
                - some
                - random
                    * list

            No comment !
            """

        r = flow._doc_to_description(func)

        self.assertEqual(
            r,
            "Documentation with a strange indentation, due to this list:\n    - some\n    - random\n        * list\n\nNo comment !",
        )

    def test_oneliner_emptyend(self):
        def func():
            """Documentation with only one line"""

        r = flow._doc_to_description(func)

        self.assertEqual(r, "Documentation with only one line")

    def test_oneliner(self):
        def func():
            """Documentation with only one line"""

        r = flow._doc_to_description(func)

        self.assertEqual(r, "Documentation with only one line")

    def test_one_lf(self):
        def func():
            """Documentation with only one line"""

        r = flow._doc_to_description(func)

        self.assertEqual(r, "Documentation with only one line")


class TestFlowMain(TenTestCase):
    def test_entry_noargs(self):
        @flow.entry
        def main():
            pass

        self.assertEqual("", self._read_output(main))

    @unittest.mock.patch("sys.stderr")
    def test_entry_raise_std_exc(self, stderr):
        @flow.entry
        def main():
            raise ValueError("Some value is wrong")

        self.assertIn("ValueError: Some value is wrong\n", self._read_output(main))

    @unittest.mock.patch("sys.stderr")
    def test_entry_raise_ten_exc(self, stderr):
        @flow.entry
        def main():
            flow.error("Some value is wrong")

        self.assertIn("TenError: Some value is wrong\n", self._read_output(main))

    @unittest.mock.patch("sys.stderr")
    def test_entry_raise_ten_leave(self, stderr):
        @flow.entry
        def main():
            flow.leave("Exit message")

        self.assertIn("Exit message\n", self._read_output(main))

    @unittest.mock.patch("sys.stderr")
    def test_entry_raise_ten_leave_pb(self, stderr):
        @flow.entry
        def main():
            pb = flow.progress()
            tid = pb.add_task("test1", total=100)
            pb.start()
            pb.update(tid, advance=1)
            flow.leave("Exit message")

        self.assertIn("Exit message\n", self._read_output(main))

    @unittest.mock.patch("sys.stderr")
    def test_entry_raise_ten_failure(self, stderr):
        @flow.entry
        def main():
            flow.failure("Some value is wrong")

        self.assertIn("✖ Some value is wrong\n", self._read_output(main))

    @unittest.mock.patch("sys.stderr")
    def test_entry_raise_ten_failure_pb(self, stderr):
        @flow.entry
        def main():
            pb = flow.progress()
            tid = pb.add_task("test2", total=100)
            pb.start()
            pb.update(tid, advance=1)
            flow.failure("Some value is wrong")

        self.assertIn("✖ Some value is wrong\n", self._read_output(main))

    @unittest.mock.patch("sys.stderr")
    def test_entry_keyboardinterrupt(self, stderr):
        @flow.entry
        def main():
            raise KeyboardInterrupt

        self.assertEqual(self._read_output(main), "✖ Execution interrupted (Ctrl-C)\n")

    # @unittest.mock.patch("sys.stderr")
    def test_entry_keyboardinterrupt_pb(self):
        @flow.entry
        def main():
            pb = flow.progress()
            tid = pb.add_task("test3", total=100)
            pb.start()
            pb.update(tid, advance=1)
            pb.stop()

            raise KeyboardInterrupt

        self.assertIn("Execution interrupted", self._read_output(main))

    def test_completedtotalcolumn_works_with_none(self):
        self.assertEqual(flow._CompletedTotalColumn().get_string_for_nb(None), "0")

    def test_completedtotalcolumn_reflects_order(self):
        self.assertEqual(flow._CompletedTotalColumn().get_string_for_nb(123), "123")
        self.assertEqual(flow._CompletedTotalColumn().get_string_for_nb(1200), "1.2K")
        self.assertEqual(
            flow._CompletedTotalColumn().get_string_for_nb(1234 * 1000), "1.2M"
        )
        self.assertEqual(
            flow._CompletedTotalColumn().get_string_for_nb(3000 * 1000 * 1000), "3.0G"
        )

    def test_entry_class(self):
        @flow.entry
        class Entry:
            def run(self):
                flow.msg_print("OK")

        self.assertEqual(self._read_output(Entry), "OK\n")


class TestFlowInform(TenTestCase):
    def test_inform_go(self):
        @flow.inform(go="go")
        def test():
            return

        out = self._read_output(test)
        self.assertEqual(out, "")

    def test_inform_ok_false(self):
        @flow.inform(ok="ok")
        def test():
            return False

        out = self._read_output(test)
        self.assertEqual(out, "")

    def test_inform_ok_true(self):
        @flow.inform(ok="ok")
        def test():
            return True

        out = self._read_output(test)
        self.assertEqual(out, "✔ ok\n")

    def test_inform_ko_false(self):
        @flow.inform(ko="ko")
        def test():
            return False

        out = self._read_output(test)
        self.assertEqual(out, "✖ ko\n")

    def test_inform_ko_true(self):
        @flow.inform(ko="ko")
        def test():
            return True

        out = self._read_output(test)
        self.assertEqual(out, "")

    def test_inform_ko_exit(self):
        @flow.inform(ko="ko", ko_exit=True)
        def test():
            return False

        with self.assertRaises(exception.TenFailure):
            test()


class TestFlowAssume(TenTestCase):
    def test_assume(self):
        with self.assertRaises(exception.TenFailure):
            flow.assume(False, "Woops")

    def test_assume_true(self):
        flow.assume(True, "Woops")


class TestFlowOthers(TenTestCase):
    @mock.patch("builtins.input", return_value="yes")
    def test_pause(self, input):
        self.assertEqual(
            self._read_output(flow.pause), "⊙ Paused. Press ENTER to resume execution"
        )

    def test_sleep(self):
        start = time.time()
        flow.sleep(2)
        self.assertGreaterEqual(time.time(), start + 2)


class TestFlowMessages(TenTestCase):
    def test_set_formatter_with_string_no_formatter_suffix(self):
        flow.set_message_formatter("Oldschool")
        tests = [
            ("success", "[+]"),
            ("info", "[*]"),
            ("failure", "[-]"),
            ("error", "[x]"),
            ("warning", "[!]"),
            ("debug", "[D]"),
        ]
        for type, prefix in tests:
            func = getattr(flow, f"msg_{type}")
            self.assertEqual(self._read_output(func, type), f"{prefix} {type}\n")

    def test_bin_print(self):
        console = flow.get_console()
        old_file = console.file
        buffer = io.BytesIO()
        console.file = io.TextIOWrapper(buffer)
        try:
            flow.bin_print(b"ABC")
            self.assertEqual(buffer.getvalue(), b"ABC")
        finally:
            console.file = old_file

    def test_clear(self):
        self.assertEqual(self._read_output(flow.msg_clear), f"")


class TestFlowMessageFormatter(TenTestCase):
    def test_set_formatter_with_string_no_formatter_suffix(self):
        flow.set_message_formatter("Oldschool")
        self.assertEqual(
            self._read_output(flow.msg_success, "Success"), "[+] Success\n"
        )

    def test_set_formatter_with_string_with_formatter_suffix(self):
        flow.set_message_formatter("OldschoolMessageFormatter")
        self.assertEqual(
            self._read_output(flow.msg_success, "Success"), "[+] Success\n"
        )

    def test_set_formatter_with_string_with_formatter_suffix(self):
        flow.set_message_formatter("OtherOldschoolMessageFormatter")
        self.assertEqual(
            self._read_output(flow.msg_success, "Success"), "[+] Success\n"
        )

    def test_set_formatter_with_class(self):
        flow.set_message_formatter(flow.messageformatter.OldschoolMessageFormatter)
        self.assertEqual(
            self._read_output(flow.msg_success, "Success"), "[+] Success\n"
        )

    def test_set_formatter_with_class_instance(self):
        flow.set_message_formatter(flow.messageformatter.OldschoolMessageFormatter())
        self.assertEqual(
            self._read_output(flow.msg_success, "Success"), "[+] Success\n"
        )

    def test_set_formatter_with_invalid_object(self):
        with self.assertRaises(TypeError) as cm:
            flow.set_message_formatter(1.3)
        self.assertEqual(
            str(cm.exception),
            "The object needs to be a MessageFormatter name, class, or instance, not 1.3",
        )

    def test_set_random_formatter(self):
        old_mf = None

        flow.set_random_message_formatter()

        for i in range(10):
            flow.set_random_message_formatter()
            mf = flow.get_message_formatter()
            if mf != old_mf:
                break
            old_mf = mf
        else:
            self.fail("No new message formatter found")

    def test_trace(self):
        with tempfile.NamedTemporaryFile("a+") as f:
            logging.set_file(f)
            logging.set_level(logging.TRACE)

            @flow.trace
            def test123(a, b):
                return 123

            test123("smthishere", 2)

            f.seek(0)
            data = f.read()
        # Hard to get a better heuristic
        self.assertIn("TestFlowMessageFormatt", data)
        self.assertIn("smthishere", data)

    def test_get_message_formatter_sets_default(self):
        flow.__dict__["__message_formatter"] = None
        self.assertIsInstance(flow.get_message_formatter(), MessageFormatter)

    def test_text_object_does_not_get_rendered(self):
        flow.set_message_formatter("Oldschool")
        self.assertEqual(
            self._read_output(flow.msg_success, Text("[b]Markup")), "[+] [b]Markup\n"
        )

    def test_print_can_receive_several_positional_arguments(self):
        flow.set_message_formatter("Oldschool")
        self.assertEqual(
            self._read_output(flow.msg_success, "first", "second", 3, "forth"),
            "[+] first second 3 forth\n",
        )


class TestFlowPrompt(TenTestCase):
    def test_prompt(self):
        # Prompt uses input internally, so we can mock this
        with mock.patch("builtins.input", return_value="test"):
            self.assertEqual(flow.ask("ask for test"), "test")


if __name__ == "__main__":
    unittest.main()

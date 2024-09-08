from pathlib import Path
import tempfile
import unittest
import sys

from tenlib.config import config
from tests.ten_testcases import TenTestCase
from tenlib.cli import transform, ten


class TestCLI(TenTestCase):
    def setUp(self) -> None:
        super().setUp()
        self._output = b""

    def _test_program(self, program, *args, input: bytes = None) -> None:
        sys.argv = ["./main.py"] + list(args)
        sys.argc = len(sys.argv)

        def _read(*args, **kwargs) -> bytes:
            return input

        def _write(data: bytes) -> int:
            self._output += data
            return len(data)

        read = sys.stdin.buffer.read
        write = sys.stdout.buffer.write
        sys.stdin.buffer.read = _read
        sys.stdout.buffer.write = _write

        try:
            output = self._read_output(program)
        finally:
            sys.stdin.buffer.read = read
            sys.stdout.buffer.write = write

        return output, self._output

    def test_transform_qs_to_json(self) -> None:
        _, output = self._test_program(
            transform, "qs.parse", "json.encode", input=b"a=3&b=2"
        )
        self.assertEqual(output, b'{"a": "3", "b": "2"}\n')

    def test_transform_wrong_transform(self) -> None:
        output, _ = self._test_program(
            transform, "qs.doesnotexist", "json.encode", input=b"a=3&b=2"
        )
        self.assertIn("Unknown transform qs.doesnotexist\n", output)

    def test_transform_wrong_module(self) -> None:
        output, _ = self._test_program(
            transform, "doesnotexist.help", "json.encode", input=b"a=3&b=2"
        )
        self.assertIn("Unknown module doesnotexist\n", output)

    def test_transform_qs_removes_extra_line(self) -> None:
        _, output = self._test_program(transform, "base64.encode", input=b"test\n")
        self.assertEqual(output, b"dGVzdA==\n")

    def test_transform_safely_returns_bytes(self) -> None:
        _, output = self._test_program(transform, "base64.decode", input=b"AAAA")
        self.assertEqual(output, b"\x00\x00\x00")

    def test_transform_with_python(self) -> None:
        _, output = self._test_program(
            transform, "base64.decode", "--python", input=b"AAAA"
        )
        self.assertEqual(output, b"b'\\x00\\x00\\x00'\n")

    def test_transform_to_tendict_returns_dict(self) -> None:
        _, output = self._test_program(transform, "csv.decode", input=b"a,b,c\n1,2,3")
        self.assertEqual(output, b"[{'a': '1', 'b': '2', 'c': '3'}]\n")

    def test_ten_program(self) -> None:
        config.__dict__["create_script_command"] = ("touch",)

        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "test.py"

            output1, output2 = self._test_program(ten, str(file))
            self.assertEqual("", output1)
            self.assertEqual(b"", output2)
            self.assertTrue(file.exists())

    def test_ten_program_already_exists(self) -> None:
        create_file_command = config.create_script_command
        config.__dict__["create_script_command"] = ("touch",)

        try:
            with tempfile.TemporaryDirectory() as directory:
                file = Path(directory) / "test.py"
                file.write_text("test")

                output1, output2 = self._test_program(ten, str(file))
                self.assertIn("File exists\n", output1)
                self.assertEqual(b"", output2)
        finally:
            config.__dict__["create_script_command"] = create_file_command


if __name__ == "__main__":
    unittest.main()

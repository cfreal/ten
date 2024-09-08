import unittest
import time
import os
import tempfile
from tests.ten_testcases import *

from tenlib import shell


class TestShell(TenTestCase):
    def test_wait_process(self):
        start = time.time()
        p = shell.call(["sleep", "1"])
        self.assertGreaterEqual(time.time() - start, 1)

    def test_run_background(self):
        start = time.time()
        p = shell.process(["sleep", "1"])
        self.assertLess(time.time() - start, 1)
        p.wait()
        p.stdin.close()
        p.stdout.close()
        p.stderr.close()

    def test_command_expecting_stdin_does_not_hang(self):
        out, err = shell.output("cat")
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_get_output_as_str(self):
        out, err = shell.output("echo stdout; echo stderr 1>&2")
        self.assertEqual(out, "stdout\n")
        self.assertEqual(err, "stderr\n")

    def test_get_output_as_bytes(self):
        out, err = shell.output("echo stdout; echo stderr 1>&2", text=False)
        self.assertEqual(out, b"stdout\n")
        self.assertEqual(err, b"stderr\n")

    def test_run_to_file(self):
        with tempfile.NamedTemporaryFile() as file:
            TMP_FILE = file.name
        TMP_CONTENTS = "123"

        self.assertFalse(os.path.exists(TMP_FILE))

        p = shell.call(f"echo -n {TMP_CONTENTS} > {TMP_FILE}")

        self.assertTrue(os.path.exists(TMP_FILE))

        with open(TMP_FILE, "r") as h:
            self.assertEqual(h.read(), TMP_CONTENTS)

    def test_escape(self):
        self.assertEqual(shell.escape("abc"), "'abc'")
        self.assertEqual(shell.escape("abc'def"), "'abc'\\''def'")
        self.assertEqual(shell.escape("abc'def'ijk"), "'abc'\\''def'\\''ijk'")

    def test_kill_after_sleep(self):
        with self.assertRaises(shell.TimeoutExpired) as cm:
            shell.call(["sleep", "2"], timeout=1)


if __name__ == "__main__":
    unittest.main()

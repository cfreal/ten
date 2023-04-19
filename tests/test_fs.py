import unittest
import pathlib
import shutil
import os

from tenlib import fs


# Most of the code is from pathlib, so it's supposed to work fine.
class TestFS(unittest.TestCase):
    def setUp(self):
        self.path = pathlib.Path(__file__).parent.absolute() / "fixtures" / "fs"
        self.fspath = fs.Path(str(self.path))

        shutil.rmtree(self.path, ignore_errors=True)

        os.mkdir(self.path)
        os.mkdir(self.path / "dir1")
        os.mkdir(self.path / "dir1" / "sub_dir")

        (self.path / "dir1" / "sub_dir" / "file1.txt").write_bytes(b"file 1 contents")
        (self.path / "dir1" / "sub_dir" / "file2.php").write_bytes(b"file 2 contents")
        (self.path / "dir1" / "sub_dir" / "file3.txt").write_bytes(b"file 3 contents")

    def tearDown(self):
        shutil.rmtree(self.path, ignore_errors=True)

    def test_touch_parents(self):
        f = self.fspath / "new_directory" / "new_file.txt"

        with self.assertRaises(FileNotFoundError):
            f.touch()
        self.assertEqual(f.touch(parents=True), f)

    def test_ptouch(self):
        f = self.fspath / "new_directory" / "new_file.txt"

        with self.assertRaises(FileNotFoundError):
            f.touch()
        self.assertEqual(f.ptouch(), f)

    def test_file_not_present(self):
        with self.assertRaises(FileNotFoundError):
            fs.read_text("/tmp/boo.test_doesnotexist")

    def test_write_str(self):
        DATA = "string"
        f = self.fspath / "new_file.txt"
        pf = pathlib.Path(str(f))

        f.write(DATA)
        self.assertEqual(pf.read_text(), DATA)

    def test_write_append_text(self):
        DATA = "string"
        f = self.fspath / "new_file.txt"
        pf = pathlib.Path(str(f))
        f.write("buu")

        f.append(DATA)

        self.assertEqual(pf.read_text(), "buu" + DATA)
        pf.unlink()

    def test_write_append_bytes(self):
        DATA = b"string"
        f = self.fspath / "new_file.txt"
        pf = pathlib.Path(str(f))
        f.write(b"buu")

        f.append(DATA)

        self.assertEqual(pf.read_bytes(), b"buu" + DATA)
        pf.unlink()

    def test_write_bytes(self):
        DATA = b"string"
        f = self.fspath / "new_file.txt"
        pf = pathlib.Path(str(f))

        f.write(DATA)
        self.assertEqual(pf.read_bytes(), DATA)

        pf.unlink()

    def test_file_wrappers_read(self):
        FILE = str(self.path / "dir1" / "sub_dir" / "file1.txt")

        def add_abc(data):
            return data + b"abc"

        read = fs.wrapper_read(add_abc)

        self.assertEqual(read(FILE), b"file 1 contentsabc")

    def test_file_wrappers_write(self):
        FILE = str(self.path / "write_test.txt")

        def add_abc(data):
            return data + b"abc"

        write = fs.wrapper_write(add_abc)
        write(FILE, b"test")

        self.assertEqual(pathlib.Path(FILE).read_bytes(), b"testabc")

    def test_func_exists(self):
        self.assertEqual(fs.exists(self.fspath), True)

    def test_func_read_bytes(self):
        self.assertEqual(
            fs.read_bytes(self.fspath / "dir1" / "sub_dir" / "file1.txt"),
            b"file 1 contents",
        )

    def test_func_read(self):
        self.assertEqual(
            fs.read_text(self.fspath / "dir1" / "sub_dir" / "file1.txt"),
            "file 1 contents",
        )

    def test_func_mkdirs(self):
        d = self.fspath / "some_dir"
        pd = pathlib.Path(self.fspath / "some_dir")
        fs.mkdir(d)

        self.assertTrue(pd.exists())
        self.assertTrue(pd.is_dir())


if __name__ == "__main__":
    unittest.main()

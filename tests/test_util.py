import unittest
import time

from tenlib.util import misc, watch
from tests.ten_testcases import *


class TestWatch(unittest.TestCase):
    def setUp(self) -> None:
        self.sw = watch.stopwatch()

    def test_to_format_str_from_str(self):
        self.assertEqual(watch.TimeHandler._to_format_str("test"), "test")

    def test_to_format_str_from_timeformat(self):
        self.assertEqual(
            watch.TimeHandler._to_format_str(watch.timeformat["HMS"]),
            watch.timeformat["HMS"].value,
        )

    def test_to_format_str_from_str_that_is_a_timeformat(self):
        self.assertEqual(
            watch.TimeHandler._to_format_str("HMS"), watch.timeformat["HMS"].value
        )

    def test_str_call(self):
        self.assertEqual(str(self.sw), "00:00:00")
        time.sleep(1)
        self.assertEqual(str(self.sw), "00:00:01")

    def test_format_call_no_args(self):
        self.assertEqual(format(self.sw), "00:00:00")

    def test_format_call_with_args(self):
        self.assertRegex(f"{self.sw:HMSu}", r"^00:00:00\.\d{6}$")

    def test_watch(self):
        w = watch.watch()
        self.assertRegex(f"{w:HMSu}", r"^\d+:\d+:\d+\.\d{6}$")


class TestMisc(unittest.TestCase):
    def test_repr_attrs(self):
        class Obj:
            def __init__(self):
                self.toto = 3
                self.titi = "something"

        self.assertEqual(
            misc.repr_attrs(Obj(), ["toto", "titi"]), "Obj(toto=3, titi='something')"
        )

    def test_niter_n_negative(self):
        with self.assertRaisesRegex(
            ValueError, "niter\(\): n needs to be strictly positive: -3"
        ):
            next(misc.niter(range(10), -3))

    def test_niter_n_3(self):
        self.assertEqual(
            list(misc.niter(range(10), 3)), [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)]
        )

    def test_niter_n_1(self):
        self.assertEqual(
            list(misc.niter(range(10), 1)),
            [
                (0,),
                (1,),
                (2,),
                (3,),
                (4,),
                (5,),
                (6,),
                (7,),
                (8,),
                (9,),
            ],
        )

    def test_niter_bytes(self):
        self.assertEqual(list(misc.niter(b"abcdefg", 2)), [b"ab", b"cd", b"ef", b"g"])

    def test_niter_str(self):
        self.assertEqual(list(misc.niter("abcdefg", 2)), ["ab", "cd", "ef", "g"])


if __name__ == "__main__":
    unittest.main()

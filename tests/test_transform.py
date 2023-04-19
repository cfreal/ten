import unittest
import string
import tempfile
from tests.ten_testcases import *

from tenlib import struct, transform
from tenlib.transform.generic import multiform


class TestTransform(unittest.TestCase):
    def test_base64(self):
        self.assertEqual(transform.base64.encode("test"), "dGVzdA==")
        self.assertEqual(transform.base64.decode("dGVzdA=="), b"test")

    def test_case(self):
        self.assertEqual(transform.case.camel("random_test"), "RandomTest")
        self.assertEqual(transform.case.underscore("RandomTest"), "random_test")

    def test_csv_decode(self):
        data = """\
user,email,password
admin,admin@admin.net,password1
user0,user0@user.net,user0passwd
user1,user1@user.net,user1passwd
"""
        array = transform.csv.decode(data)
        self.assertIsInstance(array, struct.TenList)

        for row in array:
            self.assertIsInstance(row, struct.TenDict)

        row = array[0]
        self.assertEqual(row.user, "admin")
        self.assertEqual(row.email, "admin@admin.net")
        self.assertEqual(row.password, "password1")

        row = array[1]
        self.assertEqual(row.user, "user0")
        self.assertEqual(row.email, "user0@user.net")
        self.assertEqual(row.password, "user0passwd")

        row = array[2]
        self.assertEqual(row.user, "user1")
        self.assertEqual(row.email, "user1@user.net")
        self.assertEqual(row.password, "user1passwd")

    def test_csv_encode_list(self):
        fieldnames = ["user", "email", "password"]
        data = [
            ["admin", "admin@admin.net", "password1"],
            ["user0", "user0@user.net", "user0passwd"],
            ["user1", "user1@user.net", "user1passwd"],
        ]
        expected = """\
user,email,password
admin,admin@admin.net,password1
user0,user0@user.net,user0passwd
user1,user1@user.net,user1passwd
"""

        result = transform.csv.encode(data, fieldnames, lineterminator="\n")
        self.assertEqual(result, expected)

    def test_csv_encode_dict_noheaders(self):
        fieldnames = ["user", "email", "password"]
        data = [
            ["admin", "admin@admin.net", "password1"],
            ["user0", "user0@user.net", "user0passwd"],
            ["user1", "user1@user.net", "user1passwd"],
        ]
        expected = """\
user,email,password
admin,admin@admin.net,password1
user0,user0@user.net,user0passwd
user1,user1@user.net,user1passwd
"""

        data_dict = [{k: v for k, v in zip(fieldnames, row)} for row in data]

        result = transform.csv.encode(data_dict, lineterminator="\n")
        self.assertEqual(result, expected)

    def test_csv_encode_dict_headers(self):
        fieldnames = ["user", "email", "password"]
        data = [
            ["admin", "admin@admin.net", "password1"],
            ["user0", "user0@user.net", "user0passwd"],
            ["user1", "user1@user.net", "user1passwd"],
        ]
        expected = """\
user,password
admin,password1
user0,user0passwd
user1,user1passwd
"""

        data_dict = [{k: v for k, v in zip(fieldnames, row)} for row in data]

        result = transform.csv.encode(
            data_dict, ("user", "password"), lineterminator="\n", extrasaction="ignore"
        )
        self.assertEqual(result, expected)

    def test_csv_write(self):
        fieldnames = ["user", "email", "password"]
        data = [
            ["admin", "admin@admin.net", "password1"],
            ["user0", "user0@user.net", "user0passwd"],
            ["user1", "user1@user.net", "user1passwd"],
        ]
        expected = """\
user,email,password
admin,admin@admin.net,password1
user0,user0@user.net,user0passwd
user1,user1@user.net,user1passwd
"""
        with tempfile.NamedTemporaryFile(mode="w+") as file:
            transform.csv.write(file.name, data, fieldnames, lineterminator="\n")
            file.seek(0)
            self.assertEqual(file.read(), expected)

    def test_csv_read(self):
        expected = """\
user,email,password
admin,admin@admin.net,password1
user0,user0@user.net,user0passwd
user1,user1@user.net,user1passwd
"""
        with tempfile.NamedTemporaryFile(mode="w+") as file:
            file.write(expected)
            file.seek(0)

            array = transform.csv.read(file.name)

        self.assertIsInstance(array, struct.TenList)

        for row in array:
            self.assertIsInstance(row, struct.TenDict)

        row = array[0]
        self.assertEqual(row.user, "admin")
        self.assertEqual(row.email, "admin@admin.net")
        self.assertEqual(row.password, "password1")

        row = array[1]
        self.assertEqual(row.user, "user0")
        self.assertEqual(row.email, "user0@user.net")
        self.assertEqual(row.password, "user0passwd")

        row = array[2]
        self.assertEqual(row.user, "user1")
        self.assertEqual(row.email, "user1@user.net")
        self.assertEqual(row.password, "user1passwd")

    def test_wrap_join_format(self):
        wjf = transform.generic.wrap_join_format
        self.assertEqual(wjf(formatter="{:c}", jointure="")(b"ABC"), "ABC")
        self.assertEqual(
            wjf(formatter="CHR(0x{:02x})", wrapper="CONCAT({})")(b"ABC"),
            "CONCAT(CHR(0x41),CHR(0x42),CHR(0x43))",
        )
        self.assertEqual(wjf()(b"ABC"), "65,66,67")
        self.assertEqual(wjf(empty="empty_string")(""), "empty_string")

    def test_hash(self):
        self.assertEqual(
            transform.hashing.md5("ABC"), "902fbdd2b1df0c4f70b4a5d23525e932"
        )
        self.assertEqual(
            transform.hashing.sha1("ABC"), "3c01bdbb26f358bab27f267924aa2c9a03fcfdb8"
        )
        self.assertEqual(
            transform.hashing.sha256("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_hexa(self):
        self.assertEqual(transform.hexa.encode("ABC\n"), "4142430a")
        self.assertEqual(transform.hexa.decode("4142430a"), b"ABC\n")

    def test_html(self):
        self.assertEqual(
            transform.html.encode_all("ABC&DEF\n<>"),
            "&#x41;&#x42;&#x43;&#x26;&#x44;&#x45;&#x46;&#x0a;&#x3c;&#x3e;",
        )
        self.assertEqual(transform.html.encode_all_dec("ABC"), "&#65;&#66;&#67;")
        self.assertEqual(transform.html.encode("ABC&DEF\n<>"), "ABC&amp;DEF\n&lt;&gt;")
        self.assertEqual(
            transform.html.decode("&#x41;&#x42;&#x43;&#x26;&#x44;&#x45;&#x46;"),
            "ABC&DEF",
        )

    def test_js(self):
        self.assertEqual(
            transform.js.from_char_code("ABC&DEF\n"),
            "String.fromCharCode(65,66,67,38,68,69,70,10)",
        )

    def test_json(self):
        self.assertEqual(
            transform.json.encode({"something": [1, 2, 3]}), '{"something": [1, 2, 3]}'
        )
        self.assertEqual(
            transform.json.decode('{"something":[1,2,3]}'), {"something": [1, 2, 3]}
        )

    def test_php(self):
        self.assertEqual(
            transform.php.dot_chr("ABC&DEF\n"),
            "chr(65).chr(66).chr(67).chr(38).chr(68).chr(69).chr(70).chr(10)",
        )

    def test_multiform(self):
        @multiform
        def u(data: bytes):
            return data.upper()

        self.assertEqual(u("aBc"), b"ABC")
        self.assertEqual(u(b"abc"), b"ABC")
        self.assertEqual(u([b"abc", "def"]), [b"ABC", b"DEF"])
        self.assertEqual(u((b"abc", "def")), (b"ABC", b"DEF"))
        self.assertEqual(u({"x": 123, "y": b"z"}), {"x": b"123", "y": b"Z"})
        self.assertEqual(u({123, b"z"}), {b"123", b"Z"})
        self.assertEqual(
            u([1, 2, {"x": 123, "y": b"z"}]), [b"1", b"2", {"x": b"123", "y": b"Z"}]
        )
        self.assertEqual(
            u(struct.TenDict({"x": 123, "y": b"z"})),
            struct.TenDict({"x": b"123", "y": b"Z"}),
        )

        class UnknownType:
            pass

        with self.assertRaises(TypeError):
            u(UnknownType())

    def test_multiform_type_hinting_not_str_or_bytes_raises_typeerror(self):
        with self.assertRaises(TypeError) as cm:

            @multiform
            def u(data: int):
                return data

        self.assertEqual(
            str(cm.exception),
            "First argument of multiform-decored function should have a type of str or bytes, not int",
        )

    def test_multiform_type_hinting_not_set_raises_typeerror(self):
        with self.assertRaises(TypeError) as cm:

            @multiform
            def u(data):
                return data

        self.assertEqual(
            str(cm.exception),
            "First argument of multiform-decored function should have a type annotation",
        )

    def test_multiform_type_hinting_set_to_str_is_fine(self):
        @multiform
        def u(data: str) -> str:
            return data.upper()

        self.assertEqual(u("aBc"), "ABC")

    def test_sql(self):
        self.assertEqual(
            transform.sql.addslashes_double("AB\"C'D\nE\tF\r"), '"AB\\"C\'D\\nE\\tF\\r"'
        )
        self.assertEqual(
            transform.sql.addslashes_single("AB\"C'D\nE\tF\r"), "'AB\"C\\'D\\nE\\tF\\r'"
        )
        self.assertEqual(
            transform.sql.doublequote("AB\"C'D\nE\tF\r"), '"AB""C\'D\nE\tF\r"'
        )
        self.assertEqual(
            transform.sql.singlequote("AB\"C'D\nE\tF\r"), "'AB\"C''D\nE\tF\r'"
        )
        self.assertEqual(transform.sql.ord("ABC"), [65, 66, 67])
        self.assertEqual(transform.sql.sum_char("ABC"), "CHAR(65)+CHAR(66)+CHAR(67)")
        self.assertEqual(transform.sql.sum_chr("ABC"), "CHR(65)+CHR(66)+CHR(67)")
        self.assertEqual(transform.sql.hexadecimal("ABC"), "0x414243")
        self.assertEqual(
            transform.sql.concat_char("ABC"), "CONCAT(CHAR(65),CHAR(66),CHAR(67))"
        )
        self.assertEqual(
            transform.sql.concat_chr("ABC"), "CONCAT(CHR(65),CHR(66),CHR(67))"
        )
        self.assertEqual(transform.sql.pipes_chr("ABC"), "CHR(65)||CHR(66)||CHR(67)")
        self.assertEqual(transform.sql.xstring("ABC"), "X'414243'")

    def test_table(self):
        data = " a:b:c\nddd:eee :fff\niii:jjj:kkk "
        table = [
            [" a", "b", "c"],
            ["ddd", "eee ", "fff"],
            ["iii", "jjj", "kkk "],
        ]
        self.assertEqual(transform.table.split(data, "\n", ":"), table)
        self.assertEqual(transform.table.join(table, "\n", ":"), data)

    def test_table_strip(self):
        data = " a:b:c   \nddd:eee :fff\niii:jjj:kkk "
        table = [["a", "b", "c"], ["ddd", "eee", "fff"], ["iii", "jjj", "kkk"]]
        self.assertEqual(transform.table.split(data, "\n", ":", strip=True), table)

    def test_table_empty(self):
        data = "a:b:c   \nddd:eee:fff\niii:jjj:kkk\n"
        table = [["a", "b", "c"], ["ddd", "eee", "fff"], ["iii", "jjj", "kkk"], []]
        self.assertEqual(
            transform.table.split(data, "\n", ":", strip=True, empty=True), table
        )

    def test_table_map(self):
        self.assertEqual(
            transform.table.map(
                [[1, 2, 3], [4, 5, 6]], _0=lambda x: x + 1, _2=lambda x: x * 2
            ),
            [[2, 2, 6], [5, 5, 12]],
        )

    def test_qs(self):
        self.assertEqual(
            transform.qs.encode("abcdef\x00\x2f.\x1fsomeTHING+"),
            "abcdef%00%2F.%1FsomeTHING%2B",
        )
        self.assertEqual(transform.qs.encode_all("ABC"), "%41%42%43")
        self.assertEqual(
            transform.qs.decode("abcdef%00%2F.%1FsomeTHING+"),
            "abcdef\x00\x2f.\x1fsomeTHING ",
        )
        self.assertEqual(transform.qs.iis_encode_all("ABC"), "%u0041%u0042%u0043")
        self.assertEqual(
            transform.qs.iis_encode("abcdef\x00\x2f.\x1fsomeTHING+"),
            "abcdef%u0000/.%u001FsomeTHING%u002B",
        )
        self.assertEqual(
            transform.qs.unparse({"k1": "v1", "k2": "", "k3[k4]": "v3 //"}),
            "k1=v1&k2=&k3[k4]=v3+%2F%2F",
        )
        self.assertEqual(
            transform.qs.unparse({"a": ["b", {"d": "e"}]}), "a[0]=b&a[1][d]=e"
        )
        with self.assertRaises(ValueError):
            transform.qs.parse("a[[b]=3", flat=False)
        self.assertEqual(
            transform.qs.parse("a[0]=b&a[1][d]=e", flat=False),
            struct.TenDict({"a": {"0": "b", "1": {"d": "e"}}}),
        )

    def test_qs_parse_standard(self):
        self.assertEqual(
            transform.qs.parse("k1=v1&k2=&k3%5Bk4%5D=v3+%2F%2F"),
            {"k1": "v1", "k2": "", "k3[k4]": "v3 //"},
        )

    def test_qs_parse_proper_array_index_computation(self):
        self.assertEqual(
            transform.qs.parse("k[0]=0&k[3]=3&k[]=1", flat=False),
            {"k": {"0": "0", "3": "3", "1": "1"}},
        )

    def test_qs_parse_proper_array_index_computation_with_repeat_0(self):
        # [] followed by [0] should be in the same key
        self.assertEqual(
            transform.qs.parse("k[][b]=b&k[0][a]=a&k[0][c]=c", flat=False),
            {"k": {"0": {"a": "a", "b": "b", "c": "c"}}},
        )

    def test_qs_parse_ignore_empty(self):
        # Empty keys should be discarded
        self.assertEqual(transform.qs.parse("&&&&&k=3&&&", flat=False), {"k": "3"})
        self.assertEqual(transform.qs.parse("&&&&&k=3&&&"), {"k": "3"})

    def test_qs_parse_array_keys_not_flat(self):
        # Parsing errors for array keys with flat=False
        with self.assertRaises(ValueError):
            transform.qs.parse("&[]=x&&&&[3]=3&&&", flat=False)

    def test_qs_parse_unsupported_array_property_not_flat(self):
        # This format actually exists, but we can't parse it atm
        with self.assertRaises(ValueError):
            transform.qs.parse("&k[a].v=x", flat=False)

    def test_random(self):
        # It's random, we can only test that the charset's fine
        # assertFalse() acts as assertEmpty()
        R = transform.random

        s = R.string(size=100, charset=string.ascii_letters + string.digits)
        self.assertEqual(len(s), 100)
        self.assertFalse(set(s) - set(string.ascii_letters + string.digits))

        s = R.alpha(size=101)
        self.assertEqual(len(s), 101)
        self.assertFalse(set(s) - set(string.ascii_letters))

        s = R.lower(size=102)
        self.assertEqual(len(s), 102)
        self.assertFalse(set(s) - set(string.ascii_lowercase))

        s = R.hexa(size=103)
        self.assertEqual(len(s), 103)
        self.assertFalse(set(s) - set("0123456789abcdef"))

        s = R.digits(size=103)
        self.assertEqual(len(s), 103)
        self.assertFalse(set(s) - set("0123456789"))

        s = R.number(10, 100)
        self.assertIn(s, range(10, 101))

    def test_generic_to_bytes(self):
        self.assertEqual(transform.to_bytes("some_string"), b"some_string")
        self.assertEqual(
            transform.to_bytes(bytearray((1, 2, 3, 4))), b"\x01\x02\x03\x04"
        )
        self.assertEqual(transform.to_bytes(None), None)

    def test_generic_strip(self):
        self.assertEqual(transform.strip("some_string test "), b"some_string test")

    def test_generic_xor(self):
        self.assertEqual(transform.xor("A", "B"), b"\x03")
        self.assertEqual(transform.xor("ABCD", "AB"), b"\x00\x00\x02\x06")
        self.assertEqual(transform.xor("AB", "ABCD"), b"\x00\x00")

    def test_not_empty(self):
        self.assertEqual(
            transform.not_empty(["abc", "", "test", 123, 0]), ["abc", "test", 123]
        )


if __name__ == "__main__":
    unittest.main()

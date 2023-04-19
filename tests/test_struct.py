import os
from tenlib.struct.proxy import wrap_object
import unittest
import tempfile
import glob

from tenlib import struct
from tenlib.config import config
from tenlib.struct import TenDict, TenList


class TestStruct(unittest.TestCase):
    def test_xmldict(self):
        data = """\
<root>
    <user id="1">
        <nickname>admin</nickname>
        <email>admin@admin.org</email>
        <email created='2020-10-10'>recovery@admin.org</email>
    </user>
    <user id="2">
        <nickname>user0</nickname>
        <email>user0@user.net</email>
    </user>
</root>
"""
        d = struct.XMLDict.build(data)
        self.assertEqual(len(d.user), 2)

        # Read attributes
        self.assertEqual(d.user[0].attrs.id, "1")
        self.assertEqual(d.user[1].attrs.id, "2")

        # Read multiple/single children
        self.assertEqual(d.user[0].email[0], "admin@admin.org")
        self.assertEqual(d.user[0].email[1], "recovery@admin.org")
        self.assertEqual(d.user[0].email[1].attrs.created, "2020-10-10")
        self.assertEqual(d.user[1].email, "user0@user.net")

        # Use list() to ensure the returned data is a list
        self.assertEqual(d.list(), [d])
        self.assertEqual(d.user[0].email.list(), d.user[0].email)
        self.assertEqual(d.user[1].email.list(), [d.user[1].email])
        self.assertEqual(repr(d), """<XMLDict attrs=TenDict({}), children=['user']>""")

    def test_table(self):
        r = struct.Table(
            ["first", "second", "third"], [["1", "2", "3"], ["4", "5", "6"]]
        )
        self.assertEqual(
            str(r).encode(),
            b"\xe2\x94\x8f\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\xb3\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\xb3\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x93\n\xe2\x94\x83 first \xe2\x94\x83 second \xe2\x94\x83 third \xe2\x94\x83\n\xe2\x94\xa1\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x95\x87\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x95\x87\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\xa9\n\xe2\x94\x82 1     \xe2\x94\x82 2      \xe2\x94\x82 3     \xe2\x94\x82\n\xe2\x94\x82 4     \xe2\x94\x82 5      \xe2\x94\x82 6     \xe2\x94\x82\n\xe2\x94\x94\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\xb4\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\xb4\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x98\n             2 rows in set\n",
        )

        r = struct.Table(["first", "second", "third"], [[1, 2, 3], [b"4\xc2", 5, None]])
        self.assertEqual(
            str(r).encode(),
            b"\xe2\x94\x8f\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\xb3\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\xb3\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x93\n\xe2\x94\x83 first    \xe2\x94\x83 second \xe2\x94\x83 third  \xe2\x94\x83\n\xe2\x94\xa1\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x95\x87\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x95\x87\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\x81\xe2\x94\xa9\n\xe2\x94\x82 1        \xe2\x94\x82 2      \xe2\x94\x82 3      \xe2\x94\x82\n\xe2\x94\x82 b'4\\xc2' \xe2\x94\x82 5      \xe2\x94\x82 <None> \xe2\x94\x82\n\xe2\x94\x94\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\xb4\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\xb4\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x98\n                 2 rows in set\n",
        )

    def test_table_save(self):
        r = struct.Table(
            ["first", "second", "third"], [["1", "2", "3"], ["4", "5", "6"]]
        )
        with tempfile.NamedTemporaryFile() as f:
            r.store_as_csv(f.name)
            f.seek(0)
            data = f.read()
            self.assertEqual(data, b"first,second,third\r\n1,2,3\r\n4,5,6\r\n")

    def test_map_add(self):
        map1 = struct.Map({"db1": {"table1": {"column1": {}, "column2": {}}}})
        map2 = struct.Map(
            {
                "db1": {"table1": {"column3": {}, "column2": {"something": {}}}},
                "db2": {"table1": {}},
            }
        )
        map3 = map1 + map2
        self.assertEqual(map3.items["db1"]["table1"]["column2"]["something"], {})
        self.assertEqual(map3.items["db2"]["table1"], {})

    def test_map_color(self):
        map1 = struct.Map(
            {"db1": {"table1": {"column1": {}, "column2": {"type": {"varchar": {}}}}}}
        )

        def fake_colorer(prefix):
            def fake_color(item):
                return f"{prefix}_{item}"

            return fake_color

        map1._color = [fake_colorer("A"), fake_colorer("B"), fake_colorer("C")]
        self.assertEqual(
            str(map1),
            "A_db1\n  B_table1\n    C_column1\n    C_column2\n      C_type\n        C_varchar\n",
        )

    def test_map_save(self):
        map1 = struct.Map(
            {"db1": {"table1": {"column1": {}, "column2": {"type": {"varchar": {}}}}}}
        )
        with tempfile.NamedTemporaryFile() as f:
            map1.store_yaml(f.name)
            f.seek(0)
            data = f.read()
            self.assertEqual(
                data,
                b"db1:\n  table1:\n    column1: {}\n    column2:\n      type:\n        varchar: {}\n",
            )

    def test_storable_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            s = StorableObject()
            path = directory + "/prefix123"
            s.store(path)
            filenames = self._storableobject_ok_contents(directory)
            self.assertTrue(all(f.startswith(path + ".") for f in filenames))

    def _storableobject_ok_contents(self, directory):
        filenames = glob.glob(f"{directory}/*")
        self.assertEqual(len(filenames), 2)
        filenames.sort()
        filename = filenames[0]

        self.assertTrue(filename.endswith(".other"))

        with open(filename, "r") as h:
            self.assertEqual(h.read(), f"test_other_{filename}")

        filename = filenames[1]

        self.assertTrue(filename.endswith(".txt"))

        with open(filename, "r") as h:
            self.assertEqual(h.read(), f"test_txt")

        return filenames


class StorableObject(struct.Storable):
    def __str__(self):
        return f"test_txt"

    def store_as_other(self, filename):
        with open(filename, "w") as h:
            h.write(f"test_other_{filename}")


class TestTenDict(unittest.TestCase):
    def test_creation(self):
        z = TenDict()
        self.assertEqual(z, {})

        z = TenDict({1: 2})
        self.assertEqual(z, {1: 2})

        z = TenDict([(1, 2)])
        self.assertEqual(z, {1: 2})

    def test_changes_are_reflected(self):
        d = {}
        z = TenDict(d)
        z[1] = 2
        self.assertEqual(d, {1: 2})

    def test_attr_read_annotated(self):
        class AnnotatedWrapper(TenDict):
            attr: int

        z = AnnotatedWrapper({"attr": "wrapped"})

        with self.assertRaises(AttributeError):
            z.attr

    def test_attr_read_masked(self):
        class Wrapper(TenDict):
            attr = "wrapper"

        z = Wrapper({"attr": "wrapped"})

        self.assertEqual(z.attr, "wrapper")

    def test_attr_read(self):
        z = TenDict({"a": 1, "b": 2})
        self.assertEqual(z.a, 1)
        self.assertEqual(z.b, 2)

    def test_subclass_attr_read(self):
        class SubTenDict(TenDict):
            a: str
            b = 4

        z = SubTenDict({"a": 1, "b": 2})
        with self.assertRaisesRegex(AttributeError, "a"):
            z.a

        self.assertEqual(z.b, 4)

    def test_attr_write(self):
        z = TenDict({"a": 1, "b": 2})
        z.a = 2

        self.assertEqual(z.a, 2)
        self.assertEqual(z["a"], 2)

    def test_attr_write_property(self):
        z = TenDict({"a": 1, "b": 2})
        z.copy = 1
        self.assertNotIn("copy", z.__wo__)

    def test_subclass_attr_write(self):
        class SubTenDict(TenDict):
            a: str
            b = 4

        z = SubTenDict({"a": 1, "b": 2})
        z.a = 2

        self.assertEqual(z.a, 2)
        self.assertEqual(z["a"], 1)

    def test_tendict_access(self):
        a = struct.TenDict({"key0": "something0", "key1": "something1", 1: 1})
        with self.assertRaises(AttributeError):
            a.nope
        with self.assertRaises(KeyError):
            a["nope"]
        self.assertEqual(a.key0, "something0")
        self.assertEqual(a["key0"], "something0")
        self.assertEqual(a[1], 1)

    def test_tendict_setdefaults(self):
        a = struct.TenDict({"key0": "something0", "key1": "something1", 1: 1})
        result = a.setdefaults({"key0": "not_changed", "key2": "changed"})
        self.assertEqual(a.key0, "something0")
        self.assertEqual(a.key2, "changed")
        self.assertEqual(result, a)

    def test_tendict_update(self):
        a = struct.TenDict({"key0": "something0", "key1": "something1", 1: 1})
        result = a.update(
            {
                "key0": "changed1",
                "key2": "changed2",
            }
        )
        self.assertEqual(a.key0, "changed1")
        self.assertEqual(a.key2, "changed2")
        self.assertEqual(result, a)

    def test_tendict_repr(self):
        base = {"key0": "something0", "key1": "something1", 1: 1}
        a = struct.TenDict(base)
        self.assertEqual(repr(a), f"TenDict({base})")

    def test_tendict_del(self):
        a = struct.TenDict({"key0": "something0", "key1": "something1", 1: 1})

        del a.key0
        del a[1]

        with self.assertRaises(AttributeError):
            del a.key0

        with self.assertRaises(KeyError):
            a[1]

        with self.assertRaises(AttributeError):
            del a.update

    def test_default_tendict_access(self):
        class DefaultDict(TenDict):
            def __missing__(self, name):
                return None

        a = DefaultDict()
        a.update({"key0": "something0", "key1": "something1", 1: 1})
        self.assertIsNone(a.nope)
        self.assertEqual(a.key0, "something0")
        self.assertEqual(a["key0"], "something0")
        self.assertEqual(a[1], 1)

    def test_keep(self):
        a = struct.TenDict({"key0": "something0", "key1": "something1", 1: 1})
        kept = a.keep("key0", 1, "key_that_does_not_exist")
        self.assertIsInstance(kept, TenDict)
        self.assertEqual(kept, {"key0": "something0", 1: 1})

    def test_fromkeys(self):
        x = ("key1", "key2", "key3")
        y = 0

        z = TenDict.fromkeys(x, y)
        self.assertIsInstance(z, TenDict)
        self.assertEqual(z, {"key1": 0, "key2": 0, "key3": 0})

    def test_copy(self):
        z = struct.TenDict({"key0": "something0", "key1": "something1", 1: 1})
        d = z.copy()

        self.assertIsInstance(z, TenDict)
        self.assertEqual(d, {"key0": "something0", "key1": "something1", 1: 1})

        d["key0"] = "something_else"

        self.assertEqual(z, {"key0": "something0", "key1": "something1", 1: 1})
        self.assertEqual(d, {"key0": "something_else", "key1": "something1", 1: 1})

    def test_copyuserdict(self):
        z = struct.proxy.UserDict({"key0": "something0", "key1": "something1", 1: 1})
        d = z.copy()

        self.assertIsInstance(z, struct.proxy.UserDict)
        self.assertEqual(d, {"key0": "something0", "key1": "something1", 1: 1})

        d["key0"] = "something_else"

        self.assertEqual(z, {"key0": "something0", "key1": "something1", 1: 1})
        self.assertEqual(d, {"key0": "something_else", "key1": "something1", 1: 1})


class TestTenList(unittest.TestCase):
    def test_attr_insert_reflected(self):
        lst = [1, 2, 3]
        z = TenList(lst)
        z.insert(0, -1)
        self.assertEqual(z, [-1, 1, 2, 3])

    def test_init_generator(self):
        z = TenList(i for i in range(10))
        self.assertEqual(z, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_repr(self):
        z = TenList(i for i in range(10))
        self.assertEqual(repr(z), "TenList([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])")


class TestWrapobject(unittest.TestCase):
    def test_wrapobject_int(self):
        self.assertIs(wrap_object(1), 1)

    def test_wrapobject_dict(self):
        b = {}
        z = wrap_object(b)
        self.assertIsInstance(z, TenDict)
        self.assertIs(z.__wo__, b)

    def test_wrapobject_list(self):
        b = []
        z = wrap_object(b)
        self.assertIsInstance(z, TenList)
        self.assertIs(z.data, b)

    def test_wrapobject_subclass_of_dict(self):
        class B(dict):
            pass

        b = B()
        z = wrap_object(b)
        self.assertIsInstance(z, B)


if __name__ == "__main__":
    unittest.main()

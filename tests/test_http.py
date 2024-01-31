import asyncio
import re
import time
import unittest
import xml.etree

import requests
from requests import models as rm
from tenlib import http, struct
from tenlib.http import FormNotFoundError, Multi
from tenlib.config import config

from tests.ten_testcases import *


class TimeoutProtocol(asyncio.Protocol):
    def __init__(self, future: asyncio.Future):
        self.future = future

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        time.sleep(1)
        self.transport.write(b"HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\nA")
        self.transport.close()

    def connection_lost(self, exc):
        self.future.set_result(True)


class ReturnsRequestTimeoutSession(http.Session):
    def send(self, req, **kwargs):
        return kwargs["timeout"]


class TestHTTPSession(TenTestCase):
    def setUp(self):
        self.base = "https://target.com"
        self.ns = http.Session()
        self.ss = http.ScopedSession(self.base)
        super().setUp()

    def test_verify_set_to_false_by_default(self):
        self.assertFalse(self.ns.verify)
        self.assertFalse(self.ss.verify)

    def test_remove_trailing_slash(self):
        url = self.base + "/"
        self.assertEqual(http.ScopedSession(url).base_url, self.base)

    def test_get_absolute_url(self):
        url = self.ss.get_absolute_url("toto")
        self.assertEqual(url, self.ss.base_url + "toto")

        DOMAIN = "https://domain.fr/page"
        self.assertEqual(self.ss.get_absolute_url(DOMAIN), DOMAIN)

        PAGE = "/some/page"
        self.assertEqual(self.ss.get_absolute_url(PAGE), self.base + PAGE)

    def test_set_burp(self):
        ns = http.Session()

        ORIG_PROXY = {"http": "fake_proxy"}
        ns.proxies = ORIG_PROXY
        ns.verify = True

        # Use burp mode

        ns.burp()

        self.assertEqual(ns.proxies, {"all": config.burp_proxy})
        self.assertFalse(ns.verify)
        self.assertEqual(
            ns._burp_saved_state, {"proxies": {"http": "fake_proxy"}, "verify": True}
        )

        # Change it again, should not do anything
        ns.burp()

        self.assertEqual(ns.proxies, {"all": config.burp_proxy})
        self.assertFalse(ns.verify)
        self.assertEqual(
            ns._burp_saved_state, {"proxies": {"http": "fake_proxy"}, "verify": True}
        )

        # Remove it

        ns.unburp()

        self.assertEqual(ns.proxies, ORIG_PROXY)
        self.assertTrue(ns.verify)
        self.assertFalse(ns._burp_saved_state)

        # Remove it again, should not change anything

        ns.unburp()

        self.assertEqual(ns.proxies, ORIG_PROXY)
        self.assertTrue(ns.verify)
        self.assertFalse(ns._burp_saved_state)

    def test_proxies(self):
        ns = http.Session()
        PROXY = "http://some-proxy:8080/"

        # unset
        ns.proxies = None
        self.assertEqual(ns.proxies, None)

        # str to dict wrapper
        ns.proxies = PROXY
        self.assertEqual(ns.proxies, {"all": PROXY})

        # standard way (dict)
        ns.proxies = {"https": PROXY + "s", "http2": PROXY + "1"}
        self.assertEqual(ns.proxies, {"https": PROXY + "s", "http2": PROXY + "1"})

        # wrong type
        with self.assertRaisesRegex(TypeError, "Invalid proxy type: int"):
            ns.proxies = 3

    def test_session_timeout_is_applied_to_request(self):
        fs = ReturnsRequestTimeoutSession()
        fs.timeout = 0.4
        timeout = fs.get("http://target.com")
        self.assertEqual(timeout, 0.4)

    def test_session_timeout_from_request_has_priority(self):
        fs = ReturnsRequestTimeoutSession()
        fs.timeout = 0.4
        timeout = fs.get("http://target.com", timeout=0.3)
        self.assertEqual(timeout, 0.3)

    def test_session_timeout_none_in_request_has_priority(self):
        fs = ReturnsRequestTimeoutSession()
        fs.timeout = 0.4
        timeout = fs.get("http://target.com", timeout=None)
        self.assertEqual(timeout, None)

    def test_raw(self):
        url = self.base + "/test<invalid%00characters>"
        r = self.ns.prepare_request(rm.Request("GET", url))
        self.assertEqual(r.url, url)

    def test_not_raw(self):
        url = self.base + "/test<invalid%00characters>"
        url_encoded = self.base + "/test%3Cinvalid%00characters%3E"
        self.ns.raw_url = False
        r = self.ns.prepare_request(rm.Request("GET", url))
        self.ns.raw_url = True
        self.assertEqual(r.url, url_encoded)

    def test_raw_with_params_in_url_and_as_kwargs(self):
        url = self.base + "/test<invalid%00characters>?a=b<>"
        r = self.ns.prepare_request(rm.Request("GET", url, params={"a": "c<>"}))
        self.assertEqual(r.url, url + "&a=c%3C%3E")

    def test_raw_with_params_as_kwargs(self):
        url = self.base + "/test<invalid%00characters>"
        r = self.ns.prepare_request(rm.Request("GET", url, params={"a": "c<>"}))
        self.assertEqual(r.url, url + "?a=c%3C%3E")

    def test_scope_append(self):
        url = self.base + "/../test!"
        r = self.ss.prepare_request(rm.Request("GET", url))
        self.assertEqual(r.url, url)

    def test_scope_out_domain(self):
        url = "http://other-target.com"
        with self.assertRaises(http.HTTPOutOfScopeError):
            self.ss.prepare_request(rm.Request("GET", url))

    def test_scope_out_port(self):
        url = "https://target.com:8090"
        with self.assertRaises(http.HTTPOutOfScopeError):
            self.ss.prepare_request(rm.Request("GET", url))

    def test_scope_out_scheme(self):
        url = "http://target.com:443"
        with self.assertRaises(http.HTTPOutOfScopeError):
            self.ss.prepare_request(rm.Request("GET", url))

    def test_get(self):
        session = FakeSession()
        method, url, kwargs = session.get("http://test.com/")
        self.assertEqual(method, "GET")

    def test_post(self):
        session = FakeSession()
        method, url, kwargs = session.post("http://test.com/")
        self.assertEqual(method, "POST")

    def test_options(self):
        session = FakeSession()
        method, url, kwargs = session.options("http://test.com/")
        self.assertEqual(method, "OPTIONS")

    def test_put(self):
        session = FakeSession()
        method, url, kwargs = session.put("http://test.com/")
        self.assertEqual(method, "PUT")

    def test_head(self):
        session = FakeSession()
        method, url, kwargs = session.head("http://test.com/")
        self.assertEqual(method, "HEAD")

    def test_patch(self):
        session = FakeSession()
        method, url, kwargs = session.patch("http://test.com/")
        self.assertEqual(method, "PATCH")

    def test_delete(self):
        session = FakeSession()
        method, url, kwargs = session.delete("http://test.com/")
        self.assertEqual(method, "DELETE")


class TestHttpResponse(TenTestCase):
    def response_index_of(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.status_code = 200
        r._content = b"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>Index of /</title>
<style type="text/css">
a, a:active {text-decoration: none; color: blue;}
a:visited {color: #48468F;}
a:hover, a:focus {text-decoration: underline; color: red;}
body {background-color: #F5F5F5;}
h2 {margin-bottom: 12px;}
table {margin-left: 12px;}
th, td { font: 90% monospace; text-align: left;}
th { font-weight: bold; padding-right: 14px; padding-bottom: 3px;}
td {padding-right: 14px;}
td.s, th.s {text-align: right;}
div.list { background-color: white; border-top: 1px solid #646464; border-bottom: 1px solid #646464; padding-top: 10px; padding-bottom: 14px;}
div.foot { font: 90% monospace; color: #787878; padding-top: 4px;}
</style>
</head>
<body>
<h2>Index of /</h2>
<div class="list">
<table summary="Directory Listing" cellpadding="0" cellspacing="0">
<thead><tr><th class="n">Name</th><th class="m">Last Modified</th><th class="s">Size</th><th class="t">Type</th></tr></thead>
<tbody>
<tr><td class="n"><a href="../">Parent Directory</a>/</td><td class="m">&nbsp;</td><td class="s">- &nbsp;</td><td class="t">Directory</td></tr>
<tr><td class="n"><a href="0linux/">0linux</a>/</td><td class="m">2010-Jun-17 11:18:51</td><td class="s">- &nbsp;</td><td class="t">Directory</td></tr>
<tr><td class="n"><a href="0x109/">0x109</a>/</td><td class="m">2013-Sep-19 17:10:28</td><td class="s">- &nbsp;</td><td class="t">Directory</td></tr>
<tr><td class="n"><a href="2mandvd/">2mandvd</a>/</td><td class="m">2013-Jul-30 16:28:18</td><td class="s">- &nbsp;</td><td class="t">Directory</td></tr>
<tr><td class="n"><a href="3lrvsteam/">3lrvsteam</a>/</td><td class="m">2009-Aug-17 15:53:58</td><td class="s">- &nbsp;</td><td class="t">Directory</td></tr>
</tbody>
</table>
</div>
</body>
</html>"""
        return r

    def test_re_findall(self):
        r = self.response_index_of()
        self.assertIsInstance(r.re, http.ResponseRegex)
        REGEX = '<a href="(.*?)">'
        self.assertEqual(r.re.findall(REGEX), re.findall(REGEX, r.text))

    def test_re_search(self):
        r = self.response_index_of()
        self.assertIsInstance(r.re, http.ResponseRegex)
        REGEX = '<a href="(.*?)">'
        self.assertEqual(
            r.re.search(REGEX, flags=re.S).groups(),
            re.search(REGEX, r.text, flags=re.S).groups(),
        )

    def test_re_match(self):
        r = self.response_index_of()
        self.assertIsInstance(r.re, http.ResponseRegex)
        REGEX = '.*<a href="(.*?)">.*'
        self.assertEqual(
            r.re.match(REGEX, flags=re.S).groups(),
            re.match(REGEX, r.text, flags=re.S).groups(),
        )

    def test_re_sub(self):
        r = self.response_index_of()
        REGEX = '<a href="(.*?)">'
        REPLACE = lambda match: f'<o href="{match.group(1)}">'
        self.assertEqual(r.re.sub(REGEX, REPLACE), re.sub(REGEX, REPLACE, r.text))

    def test_re_target(self):
        r = self.response_index_of()
        self.assertEqual(r.re._target(""), r.text)
        self.assertEqual(r.re._target(b""), r.content)

    def test_re_not_method(self):
        r = self.response_index_of()
        with self.assertRaisesRegex(
            AttributeError,
            "'ResponseRegex' object has no attribute 'some_unknown_method'",
        ):
            r.re.some_unknown_method()
        with self.assertRaisesRegex(
            AttributeError, "'ResponseRegex' object has no attribute '__version__'"
        ):
            r.re.__version__

    def test_contains(self):
        r = self.response_index_of()
        self.assertTrue(r.contains("<body>"))
        self.assertFalse(r.contains("<nobody>"))
        self.assertTrue(r.contains(b"<body>"))
        self.assertFalse(r.contains(b"<nobody>"))

    def test_expect_wrong(self):
        r = self.response_index_of()

        with self.assertRaises(http.UnexpectedHTTPStatusCodeError):
            r.expect(300, 301)

    def test_expect_right(self):
        r = self.response_index_of()
        r.expect(300, 200, 100)

    def test_code_wrong(self):
        r = self.response_index_of()
        self.assertFalse(r.code(300, 302))

    def test_code_right(self):
        r = self.response_index_of()
        self.assertTrue(r.code(300, 200, 302))

    def test_xml_not_xml(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.status_code = 200
        r._content = b"""this is not xml"""
        with self.assertRaises(xml.etree.ElementTree.ParseError):
            r.xml()

    def test_select(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.status_code = 200
        r._content = b"""<x><a></a><a></a><a></a></x>"""
        tags = r.select("a")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags, r.soup.select("a"))

    def test_select_one(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.status_code = 200
        r._content = b"""<x><a></a><a></a><a></a></x>"""
        tag = r.select_one("a")
        self.assertEqual(tag, r.soup.select_one("a"))

    def test_xml_ok(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.status_code = 200
        r._content = b"""<x></x>"""
        self.assertEqual(r.xml(), struct.XMLDict.build(r.text))

    def test_store(self):
        ns = http.Session()

        request = requests.Request()
        request.body = b""

        response = http.Response(ns)
        response.request = request
        response.connection = None
        response._content = b"some content"
        response.headers = {"a": "b", "c": "d"}
        response.status_code = 200

        class Raw:
            pass

        class Headers(dict):
            def getlist(self, name):
                return self[name]

        response.raw = Raw()
        response.raw.version = 1.1
        response.raw.headers = Headers(response.headers)
        response.raw.status = "OK"

        save = "/tmp/test_ten_dump"
        response.store(save)

        # We're really only looking for the call to requests_toolbelt to be made
        # We don't care much for the output
        with open(f"{save}.txt", "rb") as h:
            self.assertEqual(
                h.read(),
                b"  HTTP/1.1\r\nHost: \r\n\r\n\r\nHTTP/? OK \r\na: b\r\nc: d\r\n\r\nsome content",
            )

    def test_from_response(self):
        r = requests.Response()
        ns = FakeSession()
        r._content = b"test"
        r2 = http.Response._from_response(ns, r)
        self.assertIsInstance(r2, http.Response)
        self.assertGreaterEqual(r2.__dict__.items(), r.__dict__.items())

    def test_response_hook(self):
        ns = http.Session()
        r = requests.Response()
        r._content = b"test"
        r.encoding = None
        r2 = ns._response_hook(r)
        self.assertIsInstance(r2, http.Response)
        self.assertEqual(r2.encoding, "utf-8")
        # Make the test ignore "utf-8"
        r.encoding = "utf-8"
        self.assertGreaterEqual(r2.__dict__.items(), r.__dict__.items())


class TestForm(TenTestCase):
    def test_form(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST"></form>
        """
        with self.assertRaises(FormNotFoundError):
            r.form(id="toto")
        with self.assertRaises(FormNotFoundError):
            r.form(action="/login", method="GET")

        self.assertIsNotNone(r.form(action="/login"))
        self.assertIsNotNone(r.form(method="POST"))

    def test_form_with_empty_textarea_gives_empty_values(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST"><textarea name="test1"></textarea><textarea name="test2"/></form>
        """
        form = r.form(action="/login")
        self.assertEqual(form.data, {"test1": "", "test2": ""})

    def test_form_update_with_kwargs(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST"></form>
        """

        form = r.form(action="/login")
        form.update(a="3", b="4")
        self.assertEqual(form.data, {"a": "3", "b": "4"})

    def test_first(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST"></form>
        <form action="/login2" method="POST"></form>
        """
        form = r.form(method="POST")
        self.assertIsNotNone(form)
        self.assertEqual(form.action, "http://site.com/login")

    def test_form_input(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST">
            <input type="text" name="login" value="email@mail.net" />
            <input type="password" name="passwd" />
            <textarea name="message">contents
            something</textarea>
        </form>
        """
        form = r.form(method="POST")
        self.assertIsNotNone(form)
        self.assertEqual(
            form.data,
            {
                "login": "email@mail.net",
                "passwd": "",
                "message": "contents\n            something",
            },
        )

    def test_form_referer(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST"></form>
        <form action="/login2" method="POST"></form>
        """
        form = r.form(method="POST")
        self.assertEqual(form.referrer, r.url)
        self.assertEqual(form.referer, r.url)

    def test_form_repr(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST">
            <input type="text" name="login" value="email@mail.net" />
            <input type="password" name="passwd" />
            <textarea name="message">contents
            something</textarea>
        </form>
        """
        form = r.form(method="POST")
        self.assertEqual(
            repr(form),
            "Form(action='http://site.com/login', method='POST', data={'login': 'email@mail.net', 'passwd': '', 'message': 'contents\\n            something'})",
        )

    def test_form_update(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST">
            <input type="text" name="login" value="email@mail.net" />
            <input type="password" name="passwd" />
        </form>
        """
        form = r.form(method="POST")
        result = form.update({"login": "login123", "passwd": "passwd123"})
        self.assertIs(result, form)
        self.assertEqual(form.data, {"login": "login123", "passwd": "passwd123"})

    def test_form_set_get_key(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/"
        r._content = b"""
        <form action="/login" method="POST">
            <input type="text" name="login" value="email@mail.net" />
            <input type="password" name="passwd" />
        </form>
        """
        form = r.form(method="POST")
        form["login"] = "login123"
        self.assertEqual(form.data, {"login": "login123", "passwd": ""})

    def test_form_action(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login" method="POST">
        </form>
        """
        form = r.form(method="POST")
        self.assertEqual(form.action, "http://site.com/login")

        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="login" method="POST">
        </form>
        """
        form = r.form(method="POST")
        self.assertEqual(form.action, "http://site.com/sub/login")

    def test_form_with_input_with_no_name_works(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="login" method="POST">
        <input value="test"/>
        </form>
        """
        form = r.form(method="POST")
        self.assertEqual(form.data, {"": "test"})

    def test_form_with_textarea_with_no_name_works(self):
        ns = http.Session()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="login" method="POST">
        <textarea>test</textarea>
        </form>
        """
        form = r.form(method="POST")
        self.assertEqual(form.data, {"": "test"})

    def test_form_submit(self):
        ns = FakeSession()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login" method="POST">
        </form>
        """
        form = r.form(method="POST")
        method, url, kwargs = form.submit()
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://site.com/login")
        self.assertEqual(kwargs["data"], {})
        self.assertEqual(kwargs["headers"], {"Referer": r.url})

    def test_form_does_not_replace_referer_if_given_by_kwargs(self):
        ns = FakeSession()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login" method="POST">
        </form>
        """
        form = r.form(method="POST")
        method, url, kwargs = form.submit(headers={"Referer": "other_referer"})
        self.assertEqual(kwargs["headers"], {"Referer": "other_referer"})

    def test_form_referrer_setter_and_getter_work(self):
        ns = FakeSession()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login" method="POST">
        </form>
        """
        form = r.form(method="POST")
        form.referrer = "a"
        self.assertEqual(form.referrer, "a")
        self.assertEqual(form.referer, "a")

    def test_form_setitem(self):
        ns = FakeSession()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login" method="POST">
        </form>
        """
        form = r.form(method="POST")
        form["user"] = "abc"
        self.assertEqual(form.data, {"user": "abc"})

    def test_form_setitem(self):
        ns = FakeSession()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login" method="POST">
        </form>
        """
        form = r.form(method="POST")
        form.data["user"] = "abc"
        self.assertEqual(form["user"], "abc")

    def test_submit_nomethod(self):
        ns = FakeSession()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login">
            <input type="text" name="test" value="hello" />
        </form>
        """
        form = r.form(action="/login")
        method, url, kwargs = form.submit()
        self.assertEqual(method, "GET")
        self.assertEqual(url, "http://site.com/login")
        self.assertEqual(kwargs["params"], {"test": "hello"})

    def test_submit_post(self):
        ns = FakeSession()
        r = http.Response(session=ns)
        r.url = "http://site.com/sub/dir"
        r._content = b"""
        <form action="/login" method="POST">
            <input type="text" name="test" value="hello" />
        </form>
        """
        form = r.form(method="POST")
        method, url, kwargs = form.submit()
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://site.com/login")
        self.assertEqual(kwargs["data"], {"test": "hello"})


class FakeResponse:
    """A fake response object that stores a few stuff."""

    def __init__(self, data):
        self.history = []
        self.data = data

    def __repr__(self):
        return repr(self.data)

    def __eq__(self, other):
        return self.data == other

    def __iter__(self):
        return iter(self.data)


class FakeSession(http.Session):
    def request(self, method, url, **kwargs):
        return FakeResponse((method, url, kwargs))


class FakePoolSession(http.Session):
    """Fake session to test pools. Returns a fake response containing the value
    of the "id" GET parameter.
    """

    def request(self, method, url, params={}, **kwargs):
        id = params["id"]
        if id == 50:
            raise ValueError("Some HTTP error occured")
        return FakeResponse(id)


class FakeMultiSession(http.Session):
    """Fake session to test multi requests. Returns a fake response containing
    the URL, the params, and the data.
    """

    def request(self, method, url, params: dict = {}, **kwargs):
        id = params.get("id")
        if id == 50:
            raise ValueError("Some HTTP error occured")
        return FakeResponse((url, params, kwargs.get("data")))


class TestPool(TenTestCase):
    def test_pool_of_10_reqs(self):
        session = FakePoolSession()

        with session.pool(on_error="raise") as pool:
            for i in range(10):
                pool.get("/", params={"id": i}, tag=i)

            i = 0
            for response in pool.as_completed():
                self.assertEqual(response.tag, response)
                i += 1
            self.assertEqual(i, 10)
            self.assertIsNone(pool._progress)

        self.assertIsNone(pool._progress)

    def test_pool_of_10_reqs_with_progress(self):
        session = FakePoolSession()

        with session.pool(on_error="raise", description="running") as pool:
            for i in range(10):
                pool.get("/", params={"id": i}, tag=i)

            i = 0
            for response in pool.as_completed():
                self.assertEqual(response.tag, response)
                i += 1
            self.assertEqual(i, 10)

            self.assertEqual(pool._progress._tasks[0].description, "running")
            self.assertEqual(pool._progress._tasks[0].total, 10)
            self.assertEqual(pool._progress._tasks[0].completed, 10)

        self.assertIsNone(pool._progress)

    def test_exception_is_raised_if_on_error_is_raise(self):
        session = FakePoolSession(1)

        with session.pool(on_error="raise") as pool:
            for i in range(40, 60):
                pool.get("/", params={"id": i}, tag=i)

            with self.assertRaises(ValueError) as cm:
                for response in pool.as_completed():
                    self.assertEqual(response.tag, response)

        self.assertEqual(response.tag, 50 - 1)
        self.assertEqual(str(cm.exception), "Some HTTP error occured")

    def test_response_is_skipped_if_on_error_is_skip(self):
        session = FakePoolSession()

        with session.pool(on_error="skip") as pool:
            for i in range(40, 60):
                pool.get("/", params={"id": i}, tag=i)

            for response in pool.as_completed():
                self.assertEqual(response.tag, response)
                self.assertNotEqual(response.tag, 50)

    def test_exception_is_yielded_if_on_error_is_return(self):
        session = FakePoolSession()

        with session.pool(on_error="return") as pool:
            for i in range(40, 60):
                pool.get("/", params={"id": i}, tag=i)

            for response in pool.as_completed():
                if response.tag == 50:
                    self.assertIsInstance(response, ValueError)
                    self.assertEqual(str(response), "Some HTTP error occured")
                else:
                    self.assertEqual(response.tag, response)

    def test_futures_are_cancelled_if_context_is_closed(self):
        class SlowPoolSession(http.Session):
            def request(self, method, url, params={}, **kwargs):
                if params["id"] >= 10:
                    time.sleep(1)
                return id

        session = SlowPoolSession(1)

        with session.pool(on_error="raise") as pool:
            futures = [pool.get("/", params={"id": i}, tag=i) for i in range(20)]
            time.sleep(0.1)

        for i in range(10):
            self.assertTrue(futures[i].done())
        # The pool operates on 1 thread, so the first two "slow" requests are
        # probably running
        for i in range(10 + 1, 20):
            self.assertTrue(futures[i].cancelled())

    def test_cannot_add_request_after_shutdown(self):
        session = FakePoolSession(1)
        with session.pool() as pool:
            pass

        with self.assertRaises(RuntimeError) as cm:
            pool.get("/", tag=1)

        self.assertEqual(
            str(cm.exception), "cannot schedule new futures after shutdown"
        )

    def test_post_issues_post_request(self):
        class FakePoolSessionWithMethod(http.Session):
            def request(self, method, url, params={}, **kwargs):
                return FakeResponse((method, url))

        session = FakePoolSessionWithMethod(1)

        with session.pool() as pool:
            pool.post("http://site.com/", tag=1)

            for response in pool.as_completed():
                self.assertEqual(response.tag, 1)
                self.assertEqual(response.data[0], "POST")
                self.assertEqual(response.data[1], "http://site.com/")

    def test_responses_contains_every_response(self):
        session = FakePoolSession()
        with session.pool() as pool:
            for i in range(0, 20):
                pool.get("/", params={"id": i}, tag=i)

            self.assertEqual(pool.in_order(), list(range(20)))

    def test_add_requests_while_pool_is_running(self):
        session = FakePoolSession()
        with session.pool() as pool:
            for i in range(0, 20):
                pool.get("/", params={"id": i}, tag=i)

            for r in pool.as_completed():
                if r.tag == 10:
                    for i in range(10):
                        pool.get("/", params={"id": 60 + i}, tag=60 + i)

            self.assertEqual(pool.in_order(), list(range(20)) + list(range(60, 70)))

    def test_add_requests_while_pool_is_running_and_with_progress(self):
        session = FakePoolSession(1)
        with session.pool(description="running") as pool:
            for i in range(0, 20):
                pool.get("/", params={"id": i}, tag=i)

            self.assertEqual(pool._progress._tasks[0].total, 20)

            for r in pool.as_completed():
                if r.tag == 10:
                    for i in range(10):
                        pool.get("/", params={"id": 60 + i}, tag=60 + i)
                    self.assertEqual(pool._progress._tasks[0].total, 30)

            self.assertEqual(pool.in_order(), list(range(20)) + list(range(60, 70)))

    def test_slow_request_gets_preceeded_by_fast_request(self):
        # We queue a fast request, then a slow request. On the first response,
        # we queue a fast request. We expect the slow request to be preceeded by
        # the two fast requests.

        class SlowPoolSession(http.Session):
            def request(self, method, url, params={}, **kwargs):
                id = params["id"]
                if id == 10:
                    time.sleep(1)
                return FakeResponse(id)

        session = SlowPoolSession(2)

        with session.pool() as pool:
            pool.get("/", params={"id": 1}, tag=1)
            pool.get("/", params={"id": 10}, tag=10)

            done_tags = []
            for r in pool.as_completed():
                if r.tag == 1:
                    pool.get("/", params={"id": 2}, tag=2)
                if r.tag == 10:
                    self.assertEqual(done_tags, [1, 2])
                done_tags.append(r.tag)

            self.assertEqual(pool.in_order(), [1, 10, 2])


class TestMulti(TenTestCase):
    def test_get_10_reqs(self):
        session = FakeMultiSession()
        responses = session.multi().get(Multi([f"/{i}" for i in range(10)]))
        self.assertEqual(responses, [(f"/{i}", {}, None) for i in range(10)])
        self.assertEqual(
            [r.tag for r in responses], [{("url",): f"/{i}"} for i in range(10)]
        )

    def test_get_two_multis(self):
        session = FakeMultiSession()
        responses = session.multi().post(
            "/", params={"m1": Multi(range(5))}, data={"m2": Multi(range(3))}
        )
        self.assertEqual(
            responses,
            [("/", {"m1": m1}, {"m2": m2}) for m2 in range(3) for m1 in range(5)],
        )
        self.assertEqual(
            [r.tag for r in responses],
            [
                {("params", "m1"): m1, ("data", "m2"): m2}
                for m2 in range(3)
                for m1 in range(5)
            ],
        )

    def test_multi_with_multi_in_list(self):
        session = FakeMultiSession()
        responses = session.multi().post("/", data=(("k", Multi(range(10))),))
        self.assertEqual(responses, [(f"/", {}, [["k", i]]) for i in range(10)])
        self.assertEqual(
            [r.tag for r in responses], [{("data", 0, 1): i} for i in range(10)]
        )


class TestFirst(TenTestCase):
    def path_is_4(self, response) -> bool:
        return response.data[0] == "/4"

    def test_get_10_reqs(self):
        session = FakeMultiSession()
        response = session.first(self.path_is_4).get(
            Multi([f"/{i}" for i in range(10)])
        )
        self.assertEqual(response, ("/4", {}, None))

    def test_get_10_reqs_no_match_returns_None(self):
        session = FakeMultiSession()
        response = session.first(self.path_is_4).get(
            Multi([f"/{i}" for i in range(10, 20)])
        )
        self.assertEqual(response, None)

    def contains_m1_m2_with_proper_value(self, response) -> bool:
        return response.data[1].get("m1") == 4 and response.data[2].get("m2") == 1

    def test_get_two_multis(self):
        session = FakeMultiSession()
        response = session.first(self.contains_m1_m2_with_proper_value).post(
            "/", params={"m1": Multi(range(5))}, data={"m2": Multi(range(3))}
        )
        self.assertEqual(response, ("/", {"m1": 4}, {"m2": 1}))
        self.assertEqual(response.tag, {("params", "m1"): 4, ("data", "m2"): 1})


if __name__ == "__main__":
    unittest.main()

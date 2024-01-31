"""Everything related to HTTP.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed, TimeoutError
import re
from typing import Callable, Generator, Any, Literal
import urllib.parse
from dataclasses import dataclass
from rich.progress import Progress
from bs4 import BeautifulSoup

import requests
import requests.adapters
import requests.models
from functools import cached_property
import requests_toolbelt.utils.dump
import urllib3

from tenlib import fs, struct
from tenlib.config import config
from tenlib.exception import TenError
from tenlib.flow import progress

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__all__ = [
    "Session",
    "ScopedSession",
    "Response",
    "ResponseRegex",
    "Form",
    "Multi",
    "RequestPool",
    "MultiRequest",
    "HTTPOutOfScopeError",
    "UnexpectedHTTPStatusCodeError",
    "FormNotFoundError",
]

DEFAULT_ENCODING = "utf-8"

# Types

BytesOrStr = str | bytes
ErrorHandling = Literal["skip", "raise", "return"]

# Classes


class HTTPOutOfScopeError(TenError):
    """URL is out of scope."""

    def __init__(self, url, base):
        super().__init__(f"{url} is not within {base}")


class UnexpectedHTTPStatusCodeError(TenError):
    """HTTP status code unexpected."""

    def __init__(self, response, status_codes):
        super().__init__(
            f"Status code {response.status_code} is not one of {status_codes}"
        )


class FormNotFoundError(TenError):
    """No form could be found using the given selector."""

    def __init__(self, selector):
        super().__init__(f"Could not find form using selector: {selector!r}")


class Session(requests.Session):
    """Pentest-compatible HTTP Session.

    As an extension of requests' `Session`, this class provides the default API
    and a few extra features:

    - No SSL verification by default. SSL warnings are disabled.
        Controlled by `Session.verify`.
    - HTTP redirects are not followed by default.
        Controlled by `Session.allow_redirects`.
    - URL parameters are not reparsed by default ("as-is").
        Controlled by `Session.raw_url`.
    - Proxies can be set using a string or the usual dictionary.
    - `Session.burp` can be called in order to setup burp as a proxy, and
        removed using `Session.unburp`

    In addition, it is able to send requests concurrently using `Session.multi`
    or `Session.pool`.

    Examples:

        >>> s = Session()
        >>> s.get('https://target.com/index/../admin/dashboard<test>').url
        'https://target.com/index/../admin/dashboard<test>'
        >>> s.proxies = 'socks5://localhost:12345'

    """

    raw_url: bool = True
    """Whether to reparse and url-encode characters in the URL.
    """
    timeout: int | tuple[int, int] = None
    """A global timeout for request and responses. Defaults to no timeout.
    """
    verify: bool
    """Verify the SSL certificate of the server. Defaults to False."""
    allow_redirects: bool = False
    """Automatically follow HTTP redirects. Defaults to False."""
    max_connections: int
    """Maximum number of concurrent connections. Defaults to 10."""

    def __init__(self, max_connections: int = 10):
        """
        Args:
            max_connections (int): Maximum number of concurrent HTTP connections.
                Defaults to 10.
        """
        super().__init__()

        self._burp_saved_state = {}

        # Regular requote_uri function: allows to hook/restore it depending on
        # raw_url's value
        self._regular_requote_uri = requests.models.requote_uri
        self._raw_requote_uri = lambda url: url
        self.hooks = {"response": self._response_hook}
        self.max_connections = max_connections
        self.verify = False
        self._build_adapters()

    def _build_adapters(self):
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=self.max_connections)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    # The three HTTP method calls set a default value for allow_redirects
    # Override this behaviour

    def get(self, url: str, **kwargs) -> Response:
        """Sends a GET request. Returns a `Response` object."""
        kwargs.setdefault("allow_redirects", self.allow_redirects)
        return super().get(url, **kwargs)

    def post(self, url: str, data=None, json=None, **kwargs) -> Response:
        """Sends a POST request. Returns a `Response` object.

        Args:
            url: URL for the new `Request` object.
            data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the `Request`.
            json: (optional) json to send in the body of the `Request`.
            **kwargs: Optional arguments that `request` takes.

        Returns:
            Response
        """
        return super().post(url, data, json, **kwargs)

    def options(self, url: str, **kwargs) -> Response:
        """Sends an OPTIONS request. Returns a `Response` object."""
        kwargs.setdefault("allow_redirects", self.allow_redirects)
        return super().options(url, **kwargs)

    def head(self, url: str, **kwargs) -> Response:
        """Sends a HEAD request. Returns a `Response` object."""
        kwargs.setdefault("allow_redirects", self.allow_redirects)
        return super().head(url, **kwargs)

    def put(self, url: str, data=None, **kwargs) -> Response:
        """Sends a PUT request. Returns a `Response` object.

        Args:
            url: URL for the new `Request` object.
            data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the `Request`.
            **kwargs: Optional arguments that `request` takes.

        Returns:
            Response
        """
        return super().put(url, data, **kwargs)

    def patch(self, url: str, data=None, **kwargs) -> Response:
        """Sends a PATCH request. Returns a `Response` object.

        Args:
            url: URL for the new `Request` object.
            data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the `Request`.
            **kwargs: Optional arguments that `request` takes.

        Returns:
            Response
        """
        return super().patch(url, data, **kwargs)

    def delete(self, url, **kwargs) -> Response:
        """Sends an OPTIONS request. Returns a `Response` object."""
        return super().delete(url, **kwargs)

    def pool(
        self,
        workers: int = None,
        on_error: ErrorHandling = "raise",
        description: str = None,
    ) -> RequestPool:
        """Creates a request pool.

        Example:

            with session.pool() as pool:
                for i in range(10):
                    pool.get(f'https://target.com/?news_id={i}', tag=i)

                for response in pool.as_completed():
                    if response.contains("<title>Suspicious</title>"):
                        break

            msg_success("Found suspicious news with id={response.tag}")

        Args:
            workers (int): Number of workers in the pool. Defaults to
                `self.max_connections`.
            on_error (ErrorHandling): How to handle errors: `raise`, `return`,
                or `skip`. Defaults to `raise`.

        Returns:
            RequestPool: request pool.
        """
        if workers is None:
            workers = self.max_connections
        return RequestPool(self, workers, on_error, description)

    def multi(
        self,
        workers: int = None,
        on_error: ErrorHandling = "raise",
        description: str = None,
    ) -> MultiRequest:
        """Sets up a multi-request object, allowing to run multiple requests
        concurrently.

        >>> s = Session()
        >>> responses = s.multi().get("https://target.com/news.php", params={"id": Multi(range(10))})

        Args:
            workers (int): Number of workers in the pool. Defaults to
                `self.max_connections`.
            on_error (ErrorHandling): How to handle errors: `raise`, `return`,
                or `skip`. Defaults to `raise`.

        Returns:
            MultiRequest: An object that allows to send multiple requests
                concurrently.
        """
        if workers is None:
            workers = self.max_connections
        return MultiRequest(self, workers, on_error, description)

    def first(
        self,
        filter: Callable,
        workers: int = None,
        on_error: ErrorHandling = "raise",
        description: str = None,
    ) -> MultiRequestFirst:
        """Returns the first response that matches the filter.
        Responses are run concurrently.

        Args:
            filter (Callable): Filter function.

        Returns:
            Response: first response that matches the filter.
        """
        if workers is None:
            workers = self.max_connections
        return MultiRequestFirst(self, workers, on_error, description, filter)

    def prepare_request(self, request):
        """If raw_url is True, the `url` is sent as-is. Additional params are
        urlencoded.
        """
        prepared = super().prepare_request(request)

        if not self.raw_url:
            return prepared

        prepared.url = request.url

        if request.params:
            enc_params = prepared._encode_params(request.params)
            separator = "?" if "?" not in request.url else "&"
            prepared.url += separator + enc_params

        return prepared

    def __upgrade_kwargs(self, kwargs: dict):
        kwargs.setdefault("allow_redirects", self.allow_redirects)
        if self.timeout is not None:
            kwargs.setdefault("timeout", self.timeout)

    def request(self, method: str, url: str, **kwargs) -> Response:
        """Constructs a `Request`, prepares it and sends it. Returns a
        `Response` object.
        """
        self.__upgrade_kwargs(kwargs)
        return super().request(method, url, **kwargs)

    def _response_hook(self, response: Response, **kwargs) -> Response:
        """Change response encoding and replace the object by a `Response`."""
        if not response.encoding:
            response.encoding = DEFAULT_ENCODING
        return Response._from_response(self, response)

    # Burp

    def burp(self) -> None:
        """Sets Burp as the proxy for every request, and sets `verify` to
        `False`. To reset, use `Session.unburp`.
        """
        if self._burp_saved_state:
            return
        self._burp_saved_state = {"proxies": self.proxies, "verify": self.verify}
        self.proxies = config.burp_proxy
        self.verify = False

    def unburp(self) -> None:
        """Resets the original proxies and the `verify` value."""
        if not self._burp_saved_state:
            return
        self.proxies = self._burp_saved_state["proxies"]
        self.verify = self._burp_saved_state["verify"]
        self._burp_saved_state = {}

    # Proxies

    @property
    def proxies(self) -> dict:
        """Set proxies. If set to a `str`, the proxy is used for every protocol.
        If set to `None`, no proxy is used.

        Args:

            proxy (str, dict, None): Proxy to use

        Examples:

            >>> session.proxies = 'localhost:8080'
            {'all': 'localhost:8080'}
            >>> session.proxies = {'https': 'socks://proxy.net:12345'}
            {'https': 'socks://proxy.net:12345'}
        """
        return self._proxies

    @proxies.setter
    def proxies(self, proxy) -> None:
        if proxy is None:
            self._proxies = None
        elif isinstance(proxy, dict):
            self._proxies = proxy
        elif isinstance(proxy, str):
            self._proxies = {"all": proxy}
        else:
            raise TypeError(f"Invalid proxy type: {type(proxy).__name__}")


class ScopedSession(Session):
    """HTTP Session scoped to a target URL.

    When issuing HTTP requests, the base URL is prepended to the given path.

    Examples:

        >>> s = ScopedSession('https://target.com/admin')
        >>> await s.get('/user/login').url
        'https://www.target.com/admin/user/login'
        >>> await s.get('/login/../dashboard').url
        'https://www.target.com/admin/login/../dashboard'
        >>> await s.get('https://target.com/admin/something').url
        'https://target.com/admin/something'
        >>> await s.get('https://target.com/user')
            HTTPOutOfScopeError: https://target.com/user is not within
            https://target.com/admin
        >>> await s.get('/../user').url
        'https://target.com/admin/../user'
    """

    def __init__(self, base_url: str, max_connections: int = 10):
        """
        Args:
            base_url (str): Base URL of the target
            max_connections (int): Maximum number of concurrent HTTP connections.
                Defaults to 10.
        """
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self._parsed_base_url = urllib.parse.urlparse(self.base_url)

        super().__init__(max_connections)

    def prepare_request(self, request):
        """Scopes given URL to the target if needed, and makes sure it is within
        scope. Then, prepares the request before removing the hook on the URL
        encoding function.
        """
        request.url = self.get_absolute_url(request.url)
        if not self.is_in_scope(request.url):
            raise HTTPOutOfScopeError(request.url, self.base_url)
        return super().prepare_request(request)

    # Processing

    def is_in_scope(self, url: str) -> bool:
        """Verifies that given URL is within the target's scope."""
        bu = self._parsed_base_url
        tu = urllib.parse.urlparse(url)
        return (
            bu.hostname == tu.hostname
            and bu.port == tu.port
            and bu.scheme == tu.scheme
            and tu.path.startswith(bu.path)
        )

    def get_absolute_url(self, url: str, base: str = None) -> str:
        """Merges base URL with the given one.
        If the given URL starts with `http://` or `https://`, it is considered a
        full URL. Otherwise, it is appended to the base

        Using `urllib.parse.urljoin` does not do the job properly, as for
        instance you want specially crafted paths such as
        `/admin/login.php/../dashboard`.

        Args:
            url (str): URL to scope with base URL
            base (str): Base URL

        Returns:
            str: Scoped URL
        """
        if base is None:
            base = self.base_url

        if url.startswith("https://") or url.startswith("http://"):
            return url

        return base + url


class ResponseRegex:
    """Helper class allowing to perform regex function calls onto the response.
    If the pattern is a `str`, it will be matched against `Response.text`. If
    it is `bytes`, it will be matched against `Response.content`.

    For instance

        response.re.search('test[0-9]+')

    is equivalent to

        re.search('test[0-9]+', response.text)

    and

        response.re.sub(b'someth[iI]ng', b'else')

    is equivalent to

        re.sub(b'someth[iI]ng', b'else', response.content)
    """

    A = re.A
    I = re.I
    S = re.S
    L = re.L
    M = re.M
    X = re.X

    def __init__(self, response: Response):
        self.response = response

    def search(self, pattern: BytesOrStr, flags: int = 0):
        """Calls `re.search` onto the HTTP response."""
        return re.search(pattern, self._target(pattern), flags)

    def match(self, pattern: BytesOrStr, flags: int = 0):
        """Calls `re.match` onto the HTTP response."""
        return re.match(pattern, self._target(pattern), flags)

    def findall(self, pattern: BytesOrStr, flags: int = 0):
        """Calls `re.findall` onto the HTTP response."""
        return re.findall(pattern, self._target(pattern), flags)

    def sub(
        self, pattern: BytesOrStr, replacement: BytesOrStr, *args, **kwargs
    ) -> BytesOrStr:
        """Calls `re.sub` onto the HTTP response."""
        return re.sub(pattern, replacement, self._target(pattern), *args, **kwargs)

    def _target(self, pattern: BytesOrStr) -> BytesOrStr:
        """Returns either the byte representation or the text representation
        of the response depending on the type of `pattern`.
        """
        if isinstance(pattern, bytes):
            return self.response.content
        return self.response.text


class Response(requests.Response, struct.Storable):
    """Enhanced HTTP response.

    The response object can be filtered more easily using `Response.code` and
    `Response.contains`. It also contains a few helpers:

    * `Response.form`: Parse, fill and submit forms
    * `Response.re`: Perform regex operations on the response
    * `Response.soup`: Returns a `BeautifulSoup` object
    * `Response.xml`: Returns a dict representation of the response's XML

    Additionally, the response object is storable (see
    `tenlib.struct.storable.Storable`)

    Examples:

        Finding a pattern in a response:

            >>> response.re.search('<data csrf-token="(.*?)"').group(1)
            'MyCsrfToken'

        Finding every `<p>` tag:

            >>> response.soup.find('p')
            [<Element 'p' >, <Element 'p' class=('errorButton',)>]
    """

    session: Session
    """The session that was used to make the request."""
    tag: Any
    """A tag that can be used to identify the response."""

    def __init__(self, session: Session):
        self.session = session
        super().__init__()

    @classmethod
    def _from_response(cls, session: Session, response: requests.Response):
        new_response = cls(session)
        new_response.__dict__.update(response.__dict__)
        return new_response

    def code(self, *codes: int) -> bool:
        """Returns `True` if the `status_code` is in `codes`.

        Args:
            *code (int): Possible status codes.

        Examples:
            >>> response.status_code
            500
            >>> response.code(200, 500, 403)
            True
            >>> response.code(200, 302)
            False
        """
        return self.status_code in codes

    def contains(self, needle: BytesOrStr) -> bool:
        """Returns `True` if the response contents contains `needle`."""
        if isinstance(needle, str):
            return needle in self.text
        return needle in self.content

    def follow_redirect(self) -> Response:
        """Follows the redirection. Raises `ValueError` if no Location header is
        found.
        """

        for redirection in self.session.resolve_redirects(self, self.request):
            return redirection

    @cached_property
    def re(self) -> ResponseRegex:
        """A `ResponseRegex` object built from this response."""
        return ResponseRegex(self)

    @cached_property
    def soup(self) -> BeautifulSoup:
        """A `BeautifulSoup` object built from this response."""
        return BeautifulSoup(self.content, "lxml")

    def form(self, selector: str = None, **attributes) -> Form:
        """Finds a `<form>` tag with given CSS selector and extracts its action,
        method and input/textarea fields to build a `Form` object.

        Args:
            selector: CSS selector of the `<form>` tag you want to extract.
            **attributes: Attributes of the `<form>` tag you want to extract.

        Raises:
            FormNotFoundError: The form was not found in the page.

        Examples:
            >>> response.form('#login-form')
            ...
            >>> response.form(action='/login')
            ...
        """
        selector = selector or ""
        selector = "form" + selector
        selector += "".join(f'[{k}="{v}"]' for k, v in attributes.items())
        form = self.soup.select_one(selector)
        if not form:
            raise FormNotFoundError(selector)

        action = form.attrs.get("action", "")
        action = urllib.parse.urljoin(self.url, action)
        method = form.attrs.get("method", "GET")
        data = {}

        inputs = form.select("input")
        data.update(
            {
                input.attrs.get("name", ""): input.attrs.get("value", "")
                for input in inputs
            }
        )
        inputs = form.select("textarea")
        data.update(
            {
                input.attrs.get("name", ""): input.contents[0] if input.contents else ""
                for input in inputs
            }
        )

        return Form(self.session, action, method, data, self.url)

    def expect(self, *codes: int) -> None:
        """If the HTTP status code of the response is not within `codes`, raises
        an `UnexpectedHTTPStatusCodeError`.

        Args:
            *codes (int): Possible status codes.

        Raises:
            UnexpectedHTTPStatusCodeError: if the response's status code is not
                in `codes`.

        Examples:
            >>> response.status_code
            500
            >>> response.expect(200, 500, 403)
            >>> response.expect(200, 302)
            UnexpectedHTTPStatusCodeError: Status code 500 is not one of (200, 302)
        """
        if not self.code(*codes):
            raise UnexpectedHTTPStatusCodeError(self, codes)

    def select(self, selector: str) -> list[BeautifulSoup]:
        """Returns a list of all elements matching the CSS selector."""
        return self.soup.select(selector)

    def select_one(self, selector: str) -> BeautifulSoup:
        """Returns the first element matching the CSS selector."""
        return self.soup.select_one(selector)

    def xml(self) -> struct.XMLDict:
        """Builds a dict representation of the XML response."""
        return struct.XMLDict.build(self.text)

    def store_as_txt(self, path):
        """Saves both the HTTP request and the HTTP response in a file."""
        dump = requests_toolbelt.utils.dump
        data = dump.dump_all(self, request_prefix="", response_prefix="")
        fs.write(path, data)


class Form:
    """Represents an HTTP form, with its action (target URL), method, and data.

    Attributes:
        session (Session): HTTP session
        action (str): Form's action URL
        method (str): Form's HTTP method

    Examples:
        Grab `<form id="form_login" action="/user/login" method="POST">`, check
        the CSRF token, change credentials and submit it:

            >>> f = response.form(id="form_login")
            >>> f
            Form(
                action='https://www.target.com/user/login',
                method='POST',
                data={
                    'login': '',
                    'password': '',
                    '_csrf_token': '3e8c31f3880701247c910479e9ac99f8ba2c6819'
                }
            )
            >>> f["_csrf_token"]
            '3e8c31f3880701247c910479e9ac99f8ba2c6819'
            >>> f["login"] = 'test@test.fr'
            >>> f["password"] = 'haricot'
            >>> response = f.submit()

        Grab `<form name="edition">`, change the username and submit it to
        `/user/edit`:

            >>> new_response = await response.form(name="edition").update(
            ...     username='my_new_username'
            ... ).submit('/user/edit')
    """

    session: Session = None
    """HTTP Session"""
    action: str = None
    """Form action (URL to send it to)"""
    method: str = None
    """HTTP method to sent the form with."""
    data: dict
    """Form data."""

    def __init__(
        self,
        session: Session,
        action: str,
        method: str,
        data: dict,
        referer: str = None,
    ):
        self.session = session
        self.action = action
        self.method = method
        self.data = data
        self.referer = referer

    @property
    def referrer(self):
        # Referer is actually a misspelling of Referrer
        return self.referer

    @referrer.setter
    def referrer(self, value):
        # Referer is actually a misspelling of Referrer
        self.referer = value

    def submit(self, action: str = None, method: str = None, **kwargs) -> Response:
        """Submits the form.

        Args:
            action (str): URL to send the form data to.
                If not set, the form's action will be used
            method (str): HTTP method to use.
                If not set, the form's method will be used
            kwargs: Arguments to send to the `Session.request` call.

        Returns:
            Response: HTTP response
        """
        if action is None:
            action = self.action
        if method is None:
            method = self.method

        args_key = "params" if method == "GET" else "data"
        kwargs[args_key] = self.data
        if self.referer:
            kwargs.setdefault("headers", {}).setdefault("Referer", self.referer)

        return self.session.request(method, action, **kwargs)

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"action={self.action!r}, "
            f"method={self.method!r}, "
            f"data={self.data})"
        )

    def update(self, data: dict = {}, **kwargs) -> Form:
        """Updates the form's data."""
        self.data.update(data, **kwargs)
        return self

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value


class RequestPool:
    """A request pool is a pool of requests that can be executed in parallel.

    The pool is thread-safe, and can (should) be used as a context manager.

    After requests have been submitted, the pool can provide the responses back
    in order of submission or of completion.
    Exiting the context manager will cause the pool to cancel all pending
    requests.

    Examples:

        Submit 10 GET requests to `/user/{i}`, run them concurrently, and get
        responses in order of submission:

            with session.pool() as pool:
                for i in range(10):
                    pool.get(f"/user/{i}")
                responses = pool.in_order()

            for i, response in enumerate(responses):
                msg_info(f"User #{i} has {response.json()['posts']} posts")

        *Note: for this usage, `Session.multi` is more convenient.*

        Try out 10 different URLs, and get the first response that returns a
        200 status code:

            with session.pool() as pool:
                for id in news_ids:
                    pool.get(f"/news.php?id={id}", tag=id)

                for response in pool.as_completed():
                    if response.code(200):
                        break
                else:
                    failure("No response returned a 200 status code")

            msg_success(f"Got response for news with ID={response.tag}")
            msg_info(response.text)
    """

    def __init__(
        self,
        session: Session,
        workers: int,
        on_error: ErrorHandling,
        description: str = None,
    ):
        self._session: Session = session
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=workers)
        self._queue: list[Future[Response]] = []
        self._on_error = on_error
        self._description = description
        self._progress: Progress = None

    def __enter__(self) -> RequestPool:
        self._executor.__enter__()
        if self._description is not None:
            self._progress = progress(transient=True)
            self._progress.add_task(
                description=self._description, total=len(self._queue)
            )
            self._progress.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Shut downs the pool. Cancels all pending requests."""
        if self._progress:
            self._progress.stop()
            self._progress = None
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _submit_request(self, method, *args, tag, **kwargs) -> Future[Response]:
        future = self._executor.submit(getattr(self._session, method), *args, **kwargs)
        future.tag = tag
        self._queue.append(future)
        if self._progress:
            self._progress.update(0, total=len(self._queue))
            future.add_done_callback(
                lambda _: self._progress and self._progress.advance(0)
            )
        return future

    def get(self, url: str, *args, tag=None, **kwargs) -> Future[Response]:
        """Queues a GET request."""
        return self._submit_request("get", url, *args, tag=tag, **kwargs)

    def post(
        self, url: str, data=None, json=None, *args, tag=None, **kwargs
    ) -> Future[Response]:
        """Queues a POST request."""
        return self._submit_request("post", url, data, json, *args, tag=tag, **kwargs)

    def _tag_results(
        self, generator: Generator[Future[Response]]
    ) -> Generator[Response | BaseException, None, None]:
        """Returns the results of a generator of futures, with the tag.
        If an exception was raised, it will be re-raised, or returned, in
        function of the `on_error` parameter.
        """
        on_error = self._on_error
        for future in generator:
            exception = future.exception()
            if not exception:
                response = future.result()
                response.tag = future.tag
                yield response
            else:
                if on_error == "raise":
                    raise exception
                if on_error == "skip":
                    continue
                exception.tag = future.tag
                yield exception

    def _as_completed_futures(self) -> Generator[Future[Response], None, None]:
        """Yields futures as they complete, even if they were added to the pool
        after the call.
        """
        done = set()
        current_len = len(self._queue)
        while True:
            old_len = current_len
            todo = set(self._queue) - done
            try:
                for item in as_completed(todo, 0.3):
                    done.add(item)
                    yield item
                    current_len = len(self._queue)
                    if current_len > old_len:
                        break
                current_len = len(self._queue)
            except TimeoutError:
                continue
            if current_len == old_len:
                break

    def in_order(self) -> list[Response | BaseException]:
        """Returns the HTTP responses, in order of submission."""
        return list(self._tag_results(self._queue))

    def as_completed(self) -> Generator[Response | BaseException]:
        """Yields HTTP responses as they arrive.

        for response in pool.as_completed():
            msg_info(f"Received {response.tag}: {response.status_code}")
        """
        for response in self._tag_results(self._as_completed_futures()):
            yield response


@dataclass
class Multi:
    """Indicates an element that holds several values.
    This must be used with `MultiRequest`.
    """

    items: list


class MultiRequest:
    """Runs several requests concurrently and return the responses as
    a list.

    Examples:

        Runs `/get?p1=1`, `/get?p1=2`, `/get?p1=3`, and returns the responses:

            >>> s = Session()
            >>> responses = s.multi().get("https://httpbin.org/get", params={"p1": Multi([1, 2, 3])})

        Bruteforces a login form and returns the responses:


            >>> s = Session()
            >>> usernames = ["admin", "tomcat"]
            >>> passwords = ["admin", "tomcat", "admin123456", "tomcat123456"]
            >>> responses = s.multi().post(
            ...    "http://target.com/manager/html",
            ...    data={"username": Multi(usernames), "password": Multi(passwords)}
            ... )

    The tags of the responses are a dict containing, for each multi, the "path"
    to it and its value. For example:

        >>> responses[3].tag
        {("data", "username"): "admin", ("data", "password"): "admin123456"}
    """

    def __init__(
        self, session: Session, workers: int, on_error: ErrorHandling, description: str
    ) -> None:
        self._session: Session = session
        self._workers = workers
        self._on_error = on_error
        self._description = description

    def get(self, url: str, **kwargs) -> list[Response]:
        """Sends GET requests. Returns a list of `Response`s."""
        return self._run_requests("get", url=url, **kwargs)

    def post(self, url: str, data=None, json=None, **kwargs) -> list[Response]:
        """Sends POST requests. Returns a list of `Response`s.

        Args:
            url: URL for the new `Request` object.
            data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the `Request`.
            json: (optional) json to send in the body of the `Request`.
            **kwargs: Optional arguments that `request` takes.

        Returns:
            list[Response]: List of responses
        """
        return self._run_requests("post", url=url, data=data, json=json, **kwargs)

    def _run_requests(self, method: str, **kwargs) -> list[Response]:
        pool = self._session.pool(self._workers, self._on_error, self._description)
        paths_items: dict[Any, Multi] = {}

        # Find Multi instances in both args and kwargs
        self._find_multis_in_value(paths_items, (), kwargs)

        # Small optimisation: if there are more than one Multi, we can convert
        # the last ones to a list in order not to iterate over them multiple
        # times.
        paths_items = {
            path: list(multi.items)
            if i >= 1 and not hasattr(multi, "__len__")
            else multi.items
            for i, (path, multi) in enumerate(paths_items.items())
        }

        # Repeat the request for each item in the Multis

        arguments = self.__arguments_copy(kwargs)
        method = getattr(pool, method)

        with pool:
            self._iter_set_path(method, arguments, list(paths_items.items()), {})
            return self._get_results(pool)

    def _get_results(self, pool: RequestPool):
        return pool.in_order()

    def _find_multis_in_value(self, paths: dict, path: tuple, value: Any) -> None:
        if isinstance(value, Multi):
            paths[path] = value
        elif isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                self._find_multis_in_value(paths, path + (i,), item)
        elif isinstance(value, dict):
            for key, item in value.items():
                self._find_multis_in_value(paths, path + (key,), item)

    def __arguments_copy(self, arguments) -> Any:
        if isinstance(arguments, dict):
            return {k: self.__arguments_copy(v) for k, v in arguments.items()}
        if isinstance(arguments, (list, tuple)):
            return [self.__arguments_copy(v) for v in arguments]
        if isinstance(arguments, Multi):
            return "X"
        return arguments

    def _replace_at_path(self, arguments, path, value) -> None:
        deep = arguments
        *path, last = path
        for stop in path:
            deep = deep[stop]
        deep[last] = value

    def _iter_set_path(
        self,
        method: Callable,
        arguments: dict,
        paths_items: list[tuple[tuple, Multi]],
        set_items: tuple,
    ) -> None:
        """Fills the arguments with the items from the Multi instances.

        Args:
            method (Callable): Session method to call
            arguments (dict): Base arguments
            paths_items (list[tuple[tuple, Multi]]): For each multi, a path to
                find it in the arguments and the items of the multi
            set_items (dict): Items from multi instances that have already
                been set
        """
        try:
            (path, items), *paths_items = paths_items
        except ValueError:
            # No more path: arguments have been filled, run the method
            pass
        else:
            for item in items:
                self._replace_at_path(arguments, path, item)
                self._iter_set_path(
                    method, arguments, paths_items, set_items | {path: item}
                )
            return

        arguments = self.__arguments_copy(arguments)
        method(**arguments, tag=set_items)


class MultiRequestFirst(MultiRequest):
    """Runs several requests concurrently and return the first successful
    response.
    """

    def __init__(
        self,
        session: Session,
        workers: int,
        on_error: ErrorHandling,
        description: str,
        filter: Callable,
    ) -> None:
        super().__init__(session, workers, on_error, description)
        self._filter = filter

    def _get_results(self, pool: RequestPool):
        for response in pool.as_completed():
            if self._filter(response):
                return response
        return None

    def get(self, url: str, **kwargs) -> Response | BaseException | None:
        return super().get(url, **kwargs)

    def post(
        self, url: str, data=None, json=None, **kwargs
    ) -> Response | BaseException | None:
        return super().post(url, data, json, **kwargs)

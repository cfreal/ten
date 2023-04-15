# HTTP: requests on steroids

The HTTP module is implemented on top of
[requests](https://requests.readthedocs.io/en/master/), but provides additional
features. Refer to [`tenlib.http`'s documentation](../tenlib/http.html) for details.

- [HTTP: requests on steroids](#http-requests-on-steroids)
    - [Example comparison requests/ten](#example-comparison-requeststen)
    - [Session](#session)
        - [Creating a standard session and issuing HTTP requests](#creating-a-standard-session-and-issuing-http-requests)
        - [Creating a scoped session](#creating-a-scoped-session)
        - [Setting a proxy](#setting-a-proxy)
        - [Proxying through Burp](#proxying-through-burp)
        - [Raw URLs](#raw-urls)
    - [HTTP Responses](#http-responses)
        - [Status code](#status-code)
        - [Text matching](#text-matching)
        - [Regular expressions](#regular-expressions)
        - [BeautifulSoup: checking the DOM](#beautifulsoup-checking-the-dom)
    - [Forms](#forms)
        - [Getting a form](#getting-a-form)
        - [Setting form values](#setting-form-values)
        - [Sending the form](#sending-the-form)
    - [Multi, First, Pool: Send concurrent requests](#multi-first-pool-send-concurrent-requests)
        - [Multi: run all concurrent requests](#multi-run-all-concurrent-requests)
        - [First: stop as soon as one request succeeds](#first-stop-as-soon-as-one-request-succeeds)
        - [Pool: advanced concurrency](#pool-advanced-concurrency)

## Example comparison requests/ten

Let's say you want to log in as an administrator on a Drupal website. You want
to proxy the traffic through Burp to check if everything works correctly.
With `requests`, you'd have the following script:

```python
import requests
import re

URL = 'http://site.com'

def main():
    session = Session()
    session.verify = False

    session.proxies = {'http': 'localhost:8080', 'https': 'localhost:8080'}

    # GET request to get CSRF token, form ID, etc.

    response = session.get(URL + '/user/login')

    form_build_id = re.search('name="form_build_id" value="(.*?)"', response.text).group(1)
    form_token = re.search('name="form_token" value="(.*?)"', response.text).group(1)
    form_id = re.search('name="form_id" value="(.*?)"', response.text).group(1)

    # Log in

    response = session.post(
        URL + '/user/login',
        data={
            'user': 'someone',
            'pass': 'password1!'
            'form_build_id': form_build_id,
            'form_token': form_token,
            'form_id': form_id,
        }
    }

    if response.status_code != 200:
        print('Unable to log in')
        exit()

    if 'Welcome, admin' not in response.text:
        print('User is not an administrator')
        exit()

    print('Login successful !')

main()
```

With `ten`, you'd have:

```python
from ten import *

URL = 'http://site.com'

@entry
def main():
    session = ScopedSession(URL)
    session.burp()

    response = session.get('/user/login')

    form = response.form(id='user-login')
    form.update({
        'user': 'someone',
        'pass': 'password1!'
    })
    response = form.submit()

    if not response.code(200):
        failure('Unable to log in')

    if not response.contains('Welcome, admin'):
        failure('User is not an administrator')

    msg_success('Login successful !')


main()
```

Faster, and more readable. But that's not all the http module can do.

## Session

### Creating a standard session and issuing HTTP requests

Create a session like so:

```python
session = Session()
```

The API is the same as `requests.Session`'s API.

```python
# Some GET request
response = session.get('https://site.com/', headers={...}, ...)
# Some POST request
response = session.post('https://site.com/user/login', data={...}, ...)
```

### Creating a scoped session

When you're bound to send several requests to the same website, you often end
up having to concat the base URL with the path. Instead, you can use a
`ScopedSession`:

```python
session = ScopedSession('http://target.com/admin')
```

You'd call methods like this:

```python
# GET http://target.com/admin/login
response = await session.get('/login')
```

If you request something that is out of scope, it'll raise an exception:

```python
# raises HTTPOutOfScopeError
response = await session.get('http://target.com/user')
```

### Setting a proxy

The standard `requests` API requires you to set proxies as a dictionary. Now,
a string suffices:

```python
session.proxies = "socks5://localhost:8888"
```

### Proxying through Burp

If you need to debug some requests, you can call `Session.burp()` to set the
proxy to `localhost:8080`.

```python
session.burp()
```

When you're done, unset it like so:

```python
session.unburp()
```

### Raw URLs

By default, URL's path is not re-evaluated by **ten**, allowing the use of non-canonical URLs, or un-encoded URLs:

```python
# GET /portal/../admin?param=<xss> HTTP/1.1
response = session.get("https://target.com/portal/../admin?param=<xss>")
```

To go back to the `requests` behaviour, were the URL is canonicalized and GET parameters are re-encoded, set `raw_url` to `False`.

```python
session.raw_url = False
# GET /admin?param=%3Cxss%3E HTTP/1.1
response = session.get("https://target.com/portal/../admin?param=<xss>")
```

## HTTP Responses

Upon receiving an HTTP response, one will generally make sure they are OK, using the HTTP status code or looking for keywords in the contents, and then parse their contents to extract data.

### Status code

Comparing the HTTP status code with several:

```python
if response.code(200, 302):
    ...
```

Exiting when an unexpected code happens:

```python
response.expect(200)
```

### Text matching

Use `Response.contains()` to quickly check for keywords, as string or bytes:

```python
if response.contains('login successful'):
    ...
```

```python
if response.contains(b'login successful'):
    ...
```

### Regular expressions

Every response object contains a `re` property that has the same API as the `re`
module. It handles both `str` and `bytes`.

```python
match = response.re.search(r'token:([0-9]+)')
```

```python
changed = response.re.sub(
    br'\x00\x00\x7f.{5}', b''
)
```

### BeautifulSoup: checking the DOM

A [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) object is available as `response.soup`:

```python
p_tags = response.soup.find('p')
```

In addition, `select()` and `select_one()` are access elements using CSS selectors:

```python
token = response.select_one('input[name="token"]').attrs["value"]
```

## Forms

### Getting a form

Use the `Response.form` method to extract a form from a response:

```python
login_form = response.form(id="user-login")
```

Any combination of HTML attributes can be used to select the form:

```python
login_form = response.form(action="/user/login", method="POST")
```

The `form` method returns a `Form` object, which contains the form's data, and
can be used to submit the form.

```python
Form(
    action='https://www.drupal.org/user/login',
    method='post',
    data={
        'name': '',
        'pass': '',
        'form_build_id': 'form-b2WxheXaaeswzS13Ypq5YhAWMJLRk8-fs_xT9VMceXw',
        'form_token': '9l0gj6ZY1OJBZ9I9ZKWvaNetevSRw2e5dHycs7SBzPs',
        'form_id': 'user_login',
        'op': 'Log in'
    }
)
```

### Setting form values

Form values can be read/written as a dict:

```python
csrf_token = form["token"]
form["user"] = "test@yopmail.com"
form["password"] = "Password123!"
```

or using the `update()` method:

```python
form.update({"user": "test@yopmail.com", "password": "Password123!"})
```

The underlying dictionary is stored in `form.data`.

### Sending the form

You can then submit the form:

```python
response = form.submit()
```

## Multi, First, Pool: Send concurrent requests

### Multi: run all concurrent requests

Oftentimes, you'll need to send multiple requests at the same time. For example, when you're fuzzing a parameter, you'll want to send a request for each payload.
**ten** provides helpers to do so, easily, and in a readable way.

Say you want to retrieve the first 10 news from a website. You could do it like so:

```python
session = ScopedSession("https://target.com/")
responses = [session.get(f"/news/{id}") for id in range(10)]
```

However, requests are done one after the other, which is inefficient. Using `Multi`, you can retrieve them concurrently:

```python
session = ScopedSession("https://target.com/")
responses = session.multi().get(Multi(f"/news/{id}" for id in range(10)))
```

The Multi keyword can be anywhere in the call. If you want to issue POST requests to `/api/news`, with `news_id` being 0 to 9, you can do:

```python
session = ScopedSession("https://target.com/")
responses = session.multi().post("/api/news", data={"news_id": Multi(range(10))})
```

Even better, you can use several Multi keywords:

```python
# Get news for each month and day of the year 2023
session = ScopedSession("https://target.com/")
responses = session.multi().post(
    "/api/news",
    data={
        "year": 2023,
        "month": Multi(range(1, 13)),
        "day": Multi(range(1, 32))
    }
)
```

This code would produce *12 \* 31* requests, all done concurrently.

### First: stop as soon as one request succeeds

`Session.multi()` will run every request to completion. In some cases, you might want to stop as soon as one request succeeds. For example, when you're fuzzing a parameter, you might want to stop as soon as you find a working payload. You can do so by using `Session.first()`.

```python
def news_exists(r: Response):
    return r.code(200) and r.contains("<title>News id")

first_news = session.first(news_exists).get(Multi(f"/news/{id}" for id in range(10)))
```

This code runs requests concurrently until one matches the `news_exists` predicate. It then returns the first response that matches, and cancel the other requests.

### Pool: advanced concurrency

For more advanced usage, you can use `Session.pool()`, which produces a `Pool` object. Pool objects run requests concurrently, and allow you to add requests to the pool, and retrieve responses as they come.

```python
with session.pool() as pool:
    # Queue 10 requests
    for id in range(10):
        pool.get(f"/news/{id}")
    # Retrieve responses, in order
    responses = pool.in_order()
```

In addition, you can get responses as they arrive using `pool.as_completed()`:

```python
with session.pool() as pool:
    # Queue 10 requests
    for id in range(10):
        pool.get(f"/news/{id}", tag=id)
    
    # Get responses, as they arrive
    for response in pool.as_completed():
        msg_info(f"Received {response.tag}: {response.status_code}")
```

The `tag` argument is optional, and can be used to identify responses.

As soon as you leave the `with` block, all pending requests are cancelled.
Use this to keep only some of the responses, and cancel the requests you don't
need:

```python
with session.pool() as pool:
    for id in range(100):
        pool.get(f"/news/{id}", tag=id)
    
    for response in pool.as_completed():
        msg_info(f"Received {response.tag}: {response.status_code}")
        if response.code(200) and response.contains("News id"):
            break

# At this point, all pending requests have been cancelled
msg_success(f"Found a news with ID {response.tag}")
```

Pool support adding new items while being iterated upon. If you're building some kind of crawler, you might need to add new requests whenever you find directories. Here the sample code for a very simple crawler:

```python
    s = ScopedSession(url)
    s.raw_url = False
    
    with s.pool() as pool:
        pool.get("/")
        done = set()
        for response in pool.as_completed():
            done.add(response.url)
            msg_info(response.url)

            # Directory: extract links and add them to the pool
            if response.contains("Index of "):
                urls = [a.attrs["href"] for a in response.select("a")]
                urls = {urljoin(response.url, u) for u in urls}
                urls = urls - done
                for url in urls:
                    if s.is_in_scope(url) and url.endswith('/'):
                        pool.get(url)
            # File
            else:
                # Save to disk ?
                ...
```
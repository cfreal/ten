# Tutorials and examples

## Wordpress user enumeration

- Concerns: flow, http

Although enumerating wordpress users isn't the most interesting part of a pentest, and it can be done by hundred of scripts, it's an interesting way to learn how to to build a simple script with ten, and then gradually improve it to make it more efficient, cleaner, and well-documented.

The goal is to list wordpress users (name and slug) using the well-known technique consisting in iterating over the `author` parameter: `/?author=1`, `/?author=2`, etc.

First, we'll do the most simple implementation possible.

### First script

First, create a template using:

```shell
$ ten wordpress-enum.py
```

This opens a template script on your favourite editor. Our script necessarily requires a URL, so let's add the url as an input parameter:

```python
@entry
def main(url):
    session = ScopedSession(url)
```

The arguments to the entry function are automatically mapped to CLI input. We can now run:

```shell
$ ./wordpress-enum.py http://target.com
```

If the author with ID 2 exists, fetching `/?author=2` results in a redirect to `/author/<slug-of-author>/`.
We'll start simple: let's just make a for loop that gets the HTTP response and extracts the slug.
*ten* uses the same API as `requests`! We can use `session.get` to get the response. It does not, by default, follow redirects, however.

```python
@entry
def main(url):
    session = ScopedSession(url)
    for id in range(1, 101):
        response = session.get("/", params={"author": id})
        if response.is_redirect:
            redirect = response.headers["location"]
            if "/author/" in redirect:
                slug = redirect.split("/")[-2]
                msg_info(f"Found author #{id} with slug {slug}")
```

Let's try out the script:

```shell
$ ./wordpress-enum.py http://target.com
[*] Found author #1 with slug user_smt
[*] Found author #3 with slug blogsmt-com
[*] Found author #9 with slug y-toma-fr
[*] Found author #10 with slug p-tim-fr
[*] Found author #11 with slug x-levieux-fr
[*] Found author #12 with slug hr-fr
```

It works fine, but we can improve the implementation in many, many ways:

- Let the user pick the maximum user IDs to try out
- Get username from the redirect page
- Run requests concurrently
- Let the user pick number of concurrent connections
- Let the user pick a proxy
- Add information about progress
- Document the script

Let's tackle these one by one.

### Adding parameters

Let's let the user pick the number of user IDs to bruteforce, defaulting to 100.

```python
def main(url, max_users=100):
    session = ScopedSession(url)
    for id in range(1, max_users + 1):
        ...
```

It's as simple as this: since the default value is an integer, ten assumes the value needs to be numeric.

```shell
$ ./wordpress-enum.py http://target.com --max-users=10
[*] Found author #1 with slug user_smt
[*] Found author #3 with slug blogsmt-com
[*] Found author #9 with slug y-toma-fr
[*] Found author #10 with slug p-tim-fr
```

Or, with a shortcut:

```shell
$ ./wordpress-enum.py http://target.com -m 10
```

If we removed the default value, we'd have to tell *ten* that we expect an `int` using python's typing:

```python
def main(url, max_users: int):
```

### Get username from the redirect page


Generally, after the redirect, we land on the page describing the Wordpress author, and the HTML looks like:

```html
<html>
...
<title>[name-of-user], author on Wordpress site<title>
...
</html>
```

As a result, we can follow the redirect;

```python
response = response.follow_redirect()
```

and then use a CSS selector to extract the title's contents:

```python
title = response.select_one("title").text
```

As a result, we obtain the username

```python
@entry
def main(url, max_users=100):
    session = ScopedSession(url)
    for id in range(max_users):
        response = session.get("/", params={"author": id})
        if response.is_redirect:
            redirect = response.headers["location"]
            if "/author/" in redirect:
                slug = redirect.split("/")[-2]
                response = response.follow_redirect()
                title = response.select_one("title").text
                username = title.split(",", 1)[0]
                msg_info(f"Found author #{id} with slug {slug}: {username}")
```

Let's refactor the code a little bit to remove indent:

```python
@entry
def main(url, max_users=100):
    session = ScopedSession(url)
    for id in range(max_users):
        response = session.get("/", params={"author": id})
        if not response.is_redirect:
            continue
        redirect = response.headers["location"]
        if not "/author/" in redirect:
            continue
        slug = redirect.split("/")[-2]
        response = response.follow_redirect()
        username = response.select_one("title").text.split(",", 1)[0]
        msg_info(f"Found author #{id} with slug {slug}: {username}")
```

### Running requests concurrently

At the moment, we run each HTTP request one by one. We can improve the process by running them concurrently. There are several ways to do this, but since we want to keep each response, we can just use `multi()`:

```python
responses = session.multi().get("/", params={"author": Multi(range(1, max_users+1))})
```

`Session.multi()` returns a list of responses, where each request is submitted once per value in the `Multi()` instance. Here, we thus get a request to `/?author=1`, `/?author=2`, etc.
The requests are run concurrently. The requests are then returned in the same order as they were submitted.

We then need to iterate over the responses as we did before:

```python
for id, response in enumerate(responses, start=1):
    ...
```

We are here in a simple case were it is easy to find the `id` from the index of the response in the list: the n<sup>th</sup> response corresponds to id *n*. However, sometimes the multis might not be numerical; you can also get this value from the `tag` element of the response:

```python
for response in responses:
    id = response.tag["params", "author"]
    ...
```

### Let user pick number of connections

By default, a session maintains, at most, 10 concurrent connections. We might want to let the user pick this themselves:

```python
@entry
def main(url, max_users=100, max_connections=10):
    session = ScopedSession(url, max_connections=max_connections)
```

### Allow for a proxy

While attacking stuff on the internet, you often need to use proxies. Setting `Session.proxies` to a string automatically uses it for all requests:

```python
@entry
def main(url, max_users=100, max_connections=10, proxy=None):
    session = ScopedSession(url, max_connections=max_connections)
    session.proxies = proxy
```

We now have a pretty clean script with a few customizable options. Let's make the script **ready for release** with a cleaner GUI, documentation, etc.

### Add a progress bar

Multi can display a progress bar indicating its progress. Simply add a `description` argument describing what is happening:

```python
@entry
def main(url, max_users=100, max_connections=10):
    session = ScopedSession(url, max_connections=max_connections)
    responses = session.multi(
        description="Bruteforcing author IDs"
    ).get("/", params={"author": Multi(range(max_users))})
```

Now, you get a beautiful progress bar while the process is running.

The second step of the exploitation, which resolves the redirects, should be faster, so it does not need a progress bar. Let's just add a spinner to point out that it is running:

```python
with msg_status("Resolving usernames..."):
    for response in responses:
        ...
```

### Documentation

Our program is now fast and it looks good. We need to handle the most dreaded step of development: documentation. If we run `--help` right now, we get the strict minimum:

```shell
./wordpress-enum.py --help                                                 
Usage: wordpress-enum.py [-h] [-m MAX_USERS] [-M MAX_CONNECTIONS] [-p PROXY] url

Positional Arguments:
  url

Options:
  -h, --help            show this help message and exit
  -m, --max-users MAX_USERS
  -M, --max-connections MAX_CONNECTIONS
  -p, --proxy PROXY
```

We'll document the script and its parameters in a blink. Let's start by adding a documentation to the main entrypoint.

```python
@entry
def main(url, max_users=100, max_connections=10, proxy=None):
    """Obtains Wordpress user slugs and usernames by bruteforcing author IDs.
    """
```

The help message gets a little bit better. However, we should also document arguments. This can be done by using `arg("name", "description")`:

```python
@entry
@arg("url", "URL of the WP website")
@arg("max_users", "Maximum amount of user IDs to bruteforce")
@arg("max_connections", "Maximum number of concurrent connections")
@arg("proxy", "Optional proxy to use")
def main(url, max_users=100, max_connections=10, proxy=None):
    """Obtains Wordpress user slugs and usernames by bruteforcing author IDs.
    """
```

That's it ! Our program is documented, and ready for release.

```shell
./wordpress-enum.py --help
Usage: wordpress-enum.py [-h] [-m MAX_USERS] [-M MAX_CONNECTIONS] [-p PROXY] url

Obtains Wordpress user slugs and usernames by bruteforcing author IDs.

Positional Arguments:
  url                   URL of the WP website

Options:
  -h, --help            show this help message and exit
  -m, --max-users MAX_USERS
                        Maximum amount of user IDs to bruteforce
  -M, --max-connections MAX_CONNECTIONS
                        Maximum number of concurrent connections
  -p, --proxy PROXY     Optional proxy to use
```

We are ready to go !

Here's the final script:

```python
#!/usr/bin/env python3

from ten import *


@entry
@arg("url", "URL of the WP website")
@arg("max_users", "Maximum amount of user IDs to bruteforce")
@arg("max_connections", "Maximum number of concurrent connections")
@arg("proxy", "Optional proxy to use")
def main(url, max_users=100, max_connections=10, proxy=None):
    """Obtains Wordpress user slugs and usernames by bruteforcing author IDs.
    """
    session = ScopedSession(url, max_connections=max_connections)
    session.proxies = proxy
    responses = session.multi(
        description="Bruteforcing author IDs"
    ).get("/", params={"author": Multi(range(max_users))})

    with msg_status("Resolving usernames..."):
        for response in responses:
            id = response.tag["params", "author"]
            if not response.is_redirect:
                continue
            redirect = response.headers["location"]
            if not "/author/" in redirect:
                continue
            slug = redirect.split("/")[-2]
            response = response.follow_redirect()
            username = response.select_one("title").text.split(",", 1)[0]
            msg_info(f"Found author #{id} with slug {slug}: {username}")

main()
```
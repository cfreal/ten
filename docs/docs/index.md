# ten

**ten** is a Python library for web exploit development. It provides a set of tools to make your life easier when writing code to test the security of web applications. The GitHub repository is available [here](https://github.com/cfreal/ten).

## Installation

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

## Quick start

Create a template and make the script executable:

```shell
$ ten script.py
```

This opens a template script with your favorite editor:

```python
from ten import *


@entry
def main():
    ...


main()
```

## Documentation

Refer to [the python documentation](../tenlib/index.html) for precise description of all the available classes and methods. Check the menu on the left for quick descriptions of the most used modules, and tutorials. 

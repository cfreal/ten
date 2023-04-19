from tenlib import fs


class Storable:
    """A Storable is an object that can be saved to disk under various
    representations.

    When `store(path)` is called, for every or some of the `store_as_<ext>()`
    method, a file named `<path>.<ext>` will be created.

    For instance, if a subclass has a `store_as_txt()` and a `store_as_json()`
    method, calling `obj.store('/tmp/file')` will save two files,
    `/tmp/file.txt` and `/tmp/file.json`, both containing the appropriate
    content. If `object.store_as_json('/tmp/file.json')` is called, only the
    json file will be created, under the filename `/tmp/file.json`.
    """

    def store(self, path: str | fs.Path, types: tuple = None):
        """Calls every `store_as_<ext>` method and saves the output into a file
        with an appropriate extension.

        Args:
            path (str): The prefix of the files that will be generated.
            types (tuple): If given, list of types of files to save.
                Otherwise, every file type will be stored

        Returns:
            str: The prefix path of the stored files
        """
        STORE_PREFIX = "store_as_"

        if not isinstance(path, fs.Path):
            path = fs.Path(path)

        methods = [method for method in dir(self) if method.startswith(STORE_PREFIX)]
        methods = {
            method[len(STORE_PREFIX) :]: getattr(self, method) for method in methods
        }
        methods = {
            name: method
            for name, method in methods.items()
            if types is None or name in types
        }

        for extension, method in methods.items():
            method(f"{path}.{extension}")

        return str(path)

    def store_as_txt(self, path):
        """Stores the object as a string."""
        return fs.write(path, str(self))

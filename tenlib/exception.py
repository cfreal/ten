"""Framework exceptions.
"""


class TenError(Exception):
    """Base class for errors produced by the framework."""


class TenExit(Exception):
    """Instances of that class, if raised, will be caught by the
    `tenlib.flow.entry` function and the function will exit.
    """

    def __init__(self, message):
        super().__init__()
        self.message = message


class TenFailure(TenExit):
    pass

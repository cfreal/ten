"""Holds the general configuration.
"""
# TODO Get config values from ~/ten.conf
# TODO Disallow editing properly

import os.path

__all__ = [
    "config",
    "Configuration",
]


class Configuration:
    burp_proxy: str = "http://localhost:8080"
    message_formatter: str = "OtherOldschoolMessageFormatter"
    create_script_command: tuple[str, ...] = ("code", "--")

    def __setattribute__(self):
        raise AttributeError(
            "Configuration attributes cannot be changed programmatically"
        )


config = Configuration()

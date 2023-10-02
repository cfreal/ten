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
    log_file: str = os.path.expanduser("~/ten.log")

    def __setattribute__(self):
        raise AttributeError(
            "Configuration attributes cannot be changed programmatically"
        )


config = Configuration()

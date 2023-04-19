"""Web exploit library

Imports frequently used symbols from tenlib.
"""


from tenlib import fs, logging, shell, struct
from tenlib.transform import base64, json, qs, table, hashing, to_bytes, to_str, xor
from tenlib import transform as tf
from tenlib.exception import TenError
from tenlib.flow import *
from tenlib.http import *
from tenlib.fs import *
from tenlib.struct import Table
from tenlib.util.misc import niter
from tenlib.util.watch import stopwatch, watch
from tenlib.logging import logger

# Standard libs imports

import asyncio
import os
import re
from pprint import pprint

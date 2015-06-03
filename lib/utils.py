"""
String and data utils, where implementation differs between Python 2 & 3
"""
import sys
from copy import deepcopy

PY_MAJOR, PY_MINOR = sys.version_info[:2]

if PY_MAJOR >= 3:
    from . import utils3 as utils_mod
else:
    from . import utils2 as utils_mod

STR2BYTES = utils_mod.STR2BYTES
BYTES2STR = utils_mod.BYTES2STR
NULLCHAR = utils_mod.NULLCHAR
NULLCHAR_2 = utils_mod.NULLCHAR_2
strjoin = utils_mod.strjoin
is_string = utils_mod.is_string
is_string_or_bytes = utils_mod.is_string_or_bytes
ascii_string = utils_mod.ascii_string

memcopy = deepcopy
if PY_MAJOR == 2 and PY_MINOR == 5:
    def memcopy(a):
        return a

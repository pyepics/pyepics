#!/usr/bin/env python
"""
String Utils for Python 2
"""
import sys
if sys.version_info[0] != 2:
    raise ImportError(" Python version 2 required")

NULLCHAR_2 = '\x00'
NULLCHAR =  '\x00'
STR2BYTES =  str
BYTES2STR = str

def strjoin(sep, seq):
    "join string sequence with a separator"
    return sep.join(seq)

def is_string(s):
    return isinstance(s, basestring)

is_string_or_bytes = is_string

ascii_string = str
# def ascii_string(s):
#     if isinstance(s, unicode):
#         return str(s)
#     else:
#         return s

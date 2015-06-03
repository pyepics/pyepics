#!/usr/bin/env python
"""
String Utils for Python 3
"""
import sys
if sys.version_info[0] != 3:
    raise ImportError(" Python version 3 required")

EPICS_STR_ENCODING = 'ASCII'
EPICS_STR_ENCODING = 'latin_1'
NULLCHAR_2 = '\x00'
NULLCHAR   = b'\x00'

def s2b(st1):
    'string to byte conversion'
    if isinstance(st1, bytes):
        return st1
    return bytes(st1, EPICS_STR_ENCODING)

def b2s(st1):
    'byte to string conversion'
    if isinstance(st1, str):
        return st1
    elif isinstance(st1, bytes):
        return str(st1, EPICS_STR_ENCODING)
    else:
        return str(st1)
 
STR2BYTES, BYTES2STR = s2b, b2s

def strjoin(sep, seq):
    "join string sequence with a separator"
    if isinstance(sep, bytes):
        sep = BYTES2STR(sep)
    if len(seq) == 0:
        seq = ''
    elif isinstance(seq[0], bytes):
        tmp =[]
        for i in seq:
            if i == NULLCHAR:
                break
            tmp.append(BYTES2STR(i))
        seq = tmp
    return sep.join(seq)

def is_string(s):
    return isinstance(s, str)

def is_string_or_bytes(s):
    return isinstance(s, str) or isinstance(s, bytes) 

def ascii_string(s):
    return bytes(s, EPICS_STR_ENCODING)

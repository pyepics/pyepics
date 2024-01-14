#!/usr/bin/env python
"""
A python module that uses pyepics to save/restore sets of pvs from files.

Copyright 2011 Angus Gratton <angus.gratton@anu.edu.au>
Australian National University
EPICS Open License

The module is intended to be compatible with the 'autosave' module format used in synApps.

Files -

xxx.req - A request file with a list of pvs to save. Format is the same as autosave request format,
          including being able to have "file yyy.req VAR=A,OTHER=B" style macro expansions.

xxx.sav - A saved file with the current PV values, to save/restore. Standalone file, this is a
          compatible format to the .sav files which are used by autosave.

This module requires/uses pyparsing parser framework. Debian/Ubuntu package is "python-pyparsing"
Web site is http://pyparsing.wikispaces.com/

"""

from pyparsing import (Literal, Optional, Word, Combine, Regex, Group,
                       ZeroOrMore, OneOrMore, LineEnd, LineStart, StringEnd,
                       alphanums, alphas, nums, printables)

import sys
import os
import datetime
import json
from epics.pv import get_pv
from epics.utils import IOENCODING


def restore_pvs(filepath, debug=False):
    """
    Restore pvs from a save file via Channel Access

    debug - Set to True if you want a line printed for each value set

    Returns True if all pvs were restored successfully.
    """
    pv_vals = []
    failures = []
    # preload PV names and values, hoping PV connections happen in background
    with open(filepath, 'r', encoding=IOENCODING) as fh:
        for line in fh.readlines():
            if len(line) < 2 or  line.startswith('<END') or line.startswith('#'):
                continue
            pvname, value = [w.strip() for w in line[:-1].split(' ', 1)]
            if value.startswith('@array@'):
                value = value.replace('@array@', '').strip()
                if value.startswith('{') and value.endswith('}'):
                    value = value[1:-1]
                value = json.loads(value)
            thispv = get_pv(pvname, connect=False)
            pv_vals.append((thispv, value))

    for thispv, value in pv_vals:
        thispv.connect()
        pvname = thispv.pvname
        if not thispv.connected:
            print("Cannot connect to %s" % (pvname))
        elif not thispv.write_access:
            print("No write access to %s" % (pvname))
        else:
            if debug:
                print("Setting %s to %s" % (pvname, value))
            try:
                thispv.put(value, wait=False)
            except:
                exctype, excvalue, exctrace = sys.exc_info()
                print("Error restoring %s to %s : %s" % (pvname, value,
                                                         exctype, excvalue))
                failues.append(pvname)
    return len(failures) == 0

def save_pvs(request_file, save_file, debug=False):
    """
    Save pvs from a request file to a save file, via Channel Access

    Set debug=True to print a line for each PV saved.

    Will print a warning if a PV cannot connect.
    """
    saver = AutoSaver(request_file)
    saver.save(save_file, verbose=debug)

class AutoSaver(object):
    """Autosave class"""
    def __init__(self, request_file=None):
        self.request_file = request_file
        self.pvs = []
        if request_file is not None:
            self.read_request_file(request_file)

    def read_request_file(self, request_file=None):
        if request_file is not None:
            self.request_file = request_file
        self.pvs = []
        for pvname in _parse_request_file(request_file):
            self.pvs.append(get_pv(pvname, connect=False))

    def save(self, save_file=None, verbose=False):
        """save PVs to save_file"""
        now = datetime.datetime.now()
        if save_file is None:
            sfile = self.request_file
            if sfile.endswith('.req'):
                sfile = sfile[:-4]
            tstamp = now.strftime("%Y%b%d_%H%M%S")
            save_file = "%s_%s.sav" % (sfile, tstamp)

        buff = ["# File saved by pyepics AutoSaver.save() on %s" % now,
                "# Edit with extreme care."]

        for thispv in self.pvs:
            pvname = thispv.pvname
            thispv.wait_for_connection()
            if thispv.connected:
                if thispv.count == 1:
                    value = str(thispv.get())
                elif thispv.count > 1 and 'char' in thispv.type:
                    value = thispv.get(as_string=True)
                elif thispv.count > 1 and 'char' not in thispv.type:
                    value = '@array@ %s' % json.dumps(thispv.get().tolist())
                buff.append("%s %s" % (pvname, value))
                if verbose:
                    print( "PV %s = %s" % (pvname, value))
            elif verbose:
                print("PV %s not connected" % (pvname))


        buff.append("<END>\n")
        with open(save_file, 'w', encoding=IOENCODING) as fh:
            fh.write("\n".join(buff))
        print("wrote %s"% save_file)

def _parse_request_file(request_file, macro_values={}):
    """
    Internal function to parse a request file.

    Parse happens in two stages, first build an AST then walk it and do
    file expansions (which recurse through here.)

    Returns a list of PV names.

    """
    ast = [ x for x in req_file.parseFile(request_file).asList() if len(x) > 0 ]

    result = []
    for n in ast:
        if len(n) == 1: # simple PV name
            pvname = n[0]
            for m,v in macro_values.items(): # please forgive me this awful macro expansion method
                pvname = pvname.replace("$(%s)" % m, v)
            result.append(pvname)
        elif n[0] == 'file': # include file
            subfile = n[1]
            subfile = os.path.normpath(os.path.join(os.path.dirname(request_file), subfile))
            sub_macro_vals = macro_values.copy()
            sub_macro_vals.update(dict(n[2:]))
            result += _parse_request_file(subfile, sub_macro_vals)
        else:
            raise Exception("Unexpected entry parsed from request file: %s" % n)
    return result

# request & save file grammar (combined because lots of it is pretty similar)
point = Literal('.')
minus = Literal('-')
ignored_quote = Literal('"').suppress()
ignored_comma = Literal(',').suppress()

file_name = Word(alphanums+":._-+/\\")

number = Word(nums)
integer = Combine( Optional(minus) + number )
float_number = Combine( integer +
                        Optional( point + Optional(number) )
                        ).setParseAction(lambda t:float(t[0]))

# PV names according to app developer guide and tech-talk email thread at:
# https://epics.anl.gov/tech-talk/2019/msg01429.php
pv_name = Combine(Word(alphanums+'_-+:[]<>;{}')
                  + Optional(Combine('.') + Word(printables)))
pv_value = (float_number | Word(printables))

pv_assignment = pv_name + pv_value

comment = Literal("#") + Regex(r".*")

macro = Group( Word(alphas) + Literal("=").suppress() + pv_name )
macros = Optional(macro + ZeroOrMore(Word(";,").suppress() + macro) )

#file_include = Literal("file") + pv_name + macros
file_include = Literal("file") + \
               (file_name | ignored_quote + file_name + ignored_quote) \
               + Optional(ignored_comma) + macros

def line(contents):
    return LineStart() + ZeroOrMore(Group(contents)) + LineEnd().suppress()

req_line = line( file_include | comment.suppress() | pv_name )
req_file = OneOrMore(req_line) + StringEnd().suppress()

sav_line = line( comment.suppress() | Literal("<END>").suppress() | pv_assignment)
sav_file = OneOrMore(sav_line) + StringEnd().suppress()

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

from pyparsing import Literal, Optional, Word, Combine, Regex, Group, \
    ZeroOrMore, OneOrMore, LineEnd, LineStart, StringEnd, \
    alphanums, alphas, nums

from epics.pv import PV
import os, datetime

def restore_pvs(filepath, debug=False):
    """ 
    Restore pvs from a save file via Channel Access 
    
    debug - Set to True if you want a line printed for each value set

    Returns True if all pvs were restored successfully.

    """
    success = True
    values = [ x for x in sav_file.parseFile(filepath).asList() if len(x) > 0 ]
    print( "Restoring %d values..." % ( len(values) ))
    for v in values:
        if debug:
            print( "Setting %s to %s..." % (v[0], v[1]))
        try:
            pv = PV(v[0])
            pv.put(v[1]) # hopefully this is good enough as conversions go           
        except Exception(e):
            print( "Error restoring %s to %s : %s" % (v[0], v[1], e))
            success = False
    return success
    
def save_pvs(request_file, save_pvs, debug=False):
    """
    Save pvs from a request file to a save file, via Channel Access

    Set debug=True to print a line for each PV saved.

    With throw an exception if any PV cannot be found.

    """
    pvnames = _parse_request_file(request_file)
    pv_vals = [ (pvname, PV(pvname).get()) for pvname in pvnames ]
    if debug:
        for (pv,val) in pv_vals:
            print( "PV %s = %s" % (pv, val))
    f = open(save_pvs, "w")
    f.write("# File saved automatically by save_restore.py on %s\n" % 
            datetime.datetime.now().isoformat())
    f.write("# Edit with extreme care.\n")
    f.writelines([ "%s %s\n" % v for v in pv_vals ])
    f.write("<END>\n")
    f.close()

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

# (originally I had pyparsing pulling out the $(Macro) references from inside names
# as well, but the framework doesn't work especially well without whitespace delimiters between
# tokens so we just do simple find/replace in a second pass
pv_name = Word(alphanums+":._$()")

pv_value = (float_number | Word(alphanums))
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
sav_line = line( comment.suppress() | Literal("<END>").suppress() | pv_assignment)

req_file = OneOrMore(req_line) + StringEnd().suppress()
sav_file = OneOrMore(sav_line) + StringEnd().suppress()

#!/usr/bin/env python
"""

Simple script that demonstrates how to use the epics.autosave module to
save & restore PV values using request files and savefiles, like with synApps
autosave (only via CA.)

Run ./save_restore.py -h for a full usage summary.

"""

from optparse import *
from epics.autosave import *

def main():
    (options, args) = get_validate_args()
    methods = { "restore" : do_restore, "save" : do_save }
    methods[options.mode](options.debug, args)

def do_restore(debug, args):
    print "Restoring PVs from save file %s..." % (args[0])
    if not restore_pvs(args[0], debug):
        sys.exit(1)

def do_save(debug, args):
    print "Saving PVs in %s to save file %s..." % (args[0], args[1])
    try:
        save_pvs(args[0], args[1], debug)
    except Exception,e:
        sys.exit("Failed to save pvs: %s" % e)

def get_validate_args():
    """
    Parse and validate command-line arguments

    """
    usage = "usage: %prog [options] [restore-file] save-file"
    parser = OptionParser(usage=usage, description="Save & restore EPICS pvs via Channel Access. Options --save & --restore are not required, if they are ommitted then the mode will be inferred from the number of arguments.")

    group = OptionGroup(parser, "Mode")
    group.add_option("-r", "--restore", action="store_const", const="restore", dest="mode",
                      help="Restore PV values saved in <save-file>")
    group.add_option("-s", "--save", action="store_const", const="save", dest="mode",
                      help="Save PV values in named in <restore-file> to <save-file>")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Debug Options")
    group.add_option("-d", "--debug", dest="debug", action="store_true",                   
                      help="Print each PV as it is saved/restored")
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    if options.mode is None and len(args) == 2:
        options.mode = "save"
    else:
        options.mode = "restore"

    if options.mode == "save":
        if len(args) != 2:
            parser.error("Saving pvs requires two arguments - restore-file save-file")
    elif options.mode == "restore":
        if len(args) != 1:
            parser.error("Restoring pvs requires one argument - save-file")
    else:
        parser.error("Unexpected command line arguments")
    return (options, args)

if __name__ == "__main__":
    main()


#!/usr/bin/env python

import epics
import time
import sys
import getopt

def show_usage():
    s = """Usage caget.py [options] <PV name> ...
    -h:    show this message


    """
    print s
    sys.exit()
    
opts, args = getopt.getopt(sys.argv[1:], "htansd:#:e:f:g:w:",
                           ["help", "terse","wide","number","data=",])

wait_time = 1.0

arr_num = None
format = None
terse  = False
use_ts = False
dbr_type = None
enum_as_num = False

for (k,v) in opts:
    if k in ("-h", "--help"):   show_usage()
    elif k == '-t':     terse = True
    elif k == '-a':    use_ts = True
    elif k == '-n':    enum_as_num = True
    elif k == '-d':    dbr_type = int(v)
    elif k == '-#':    arr_num  = int(v)
    elif k == '-w':    wait_time= float(v)
    elif k == '-e':     format = '%%.%ie' % int(v)
    elif k == '-f':      format = '%%.%if' % int(v)
    elif k == '-g':     format = '%%.%ig' % int(v)
    elif k == '-s':     format = 'STRING'

for pvname in args:
    form='native'
    if use_ts: form = 'time'
    pv = epics.PV(pvname,form=form)

    # pv connection
    t0 = time.time()
    pv.connect()
    while time.time()-t0 < wait_time:
        if pv.connected: break
        epics.poll()
    if not pv.connected:
        print "%s:: not connected" % pvname
    ox = pv.get_ctrlvars()
    epics.poll()


    value = pv.get(as_string=format=='STRING')

    if pv.type == 'enum' and  not enum_as_num:
        enum_strs = pv.enum_strs
        value = enum_strs[pv.get()]

    outstring = ''
    if not terse: outstring = pvname

    if use_ts:
        ts = epics.dbr.EPICS2UNIX_EPOCH +  pv._args['timestamp']
        outstring = "%s   %s" %(outstring,time.ctime(ts))
        print ts
    print outstring, value
    

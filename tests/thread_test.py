"""This script is to test various implementations of the Python to EPICS interface.
It checks wether these are multi-thread safe. That means that a caput and caget
to the same process valiable succeeds both from the forground and from a background
thread.

EpicsCA: Matt Newille, U Chicago
epics: Matt Newille, U Chicago
CA: Friedrich Schotte, NIH

Friedrich Schotte, APS, 14 Apr 2010
"""

pvname = "14IDB:serial13.TINP"
pvname = "13IDA:serial8.TINP"
pvname = "13IDA:DMM1Ch2_raw.VAL"

import lib as epics
# import epics


import time
from threading import Thread

def run_test(runtime=1, pvnames=None,  run_name='thread c'):
    print 'run thread %s  for %.3f sec ' % ( run_name, runtime)
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        print 'thread  %s / %s = %s ' % ( run_name , pvname, char_value)
        
    epics.ca.context_create(1)
    t0 = time.time()
    pvs = []
    for pvn in pvnames :
        p = epics.PV(pvn)
        p.add_callback(onChanges)
        pvs.append(p)
    while time.time()-t0 < runtime:
        time.sleep(0.01)

    p.clear_callbacks()
    print 'Done with Thread ', run_name
    
print "Run test in Foreground:"
run_test(2.0,  ('13IDA:DMM1Ch2_raw.VAL',),  'initial')


print "Run 2 Background Threads:"
th1 = Thread(target=run_test,args=(4, ('13IDA:DMM1Ch2_raw.VAL',), 'A'))
th1.start()
th2 = Thread(target=run_test,args=(10, ('13IDA:DMM1Ch2_raw.VAL',
                                       '13IDA:DMM1Ch3_raw.VAL',
                                       'S:SRcurrentAI.VAL'), 'B'))

th2.start()

th1.join()
th2.join()

print 'Done'

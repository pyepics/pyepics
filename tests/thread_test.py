"""This script tests using EPICS CA and Python threads together

Based on code from  Friedrich Schotte, NIH, modified by Matt Newville
19-Apr-2010
"""

import time
from threading import Thread
import epics

from  pvnames import updating_pvlist

def run_test(runtime=1, pvnames=None,  run_name='thread c'):
    print ' -> thread  "%s"  will run for %.3f sec ' % ( run_name, runtime)
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        print '      %s = %s (%s)' % (pvname, char_value, run_name)
        
    epics.ca.context_create()
    t0 = time.time()
    pvs = []
    for pvn in pvnames:
        p = epics.PV(pvn)
        p.get()
        p.add_callback(onChanges)
        
        pvs.append(p)
    while time.time()-t0 < runtime:
        time.sleep(0.01)

    for p in pvs: p.clear_callbacks()
    print 'Done with Thread ', run_name
    
print "First, run test in Foreground:"
run_test(2.0,  updating_pvlist, 'initial')

print "Run 2 Background Threads simultaneously:"
th1 = Thread(target=run_test,args=(5, updating_pvlist,  'A'))

th2 = Thread(target=run_test,args=(10, updating_pvlist, 'B'))
th1.start()
th2.start()

th1.join()
th2.join()

print 'Done'

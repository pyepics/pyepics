"""This script tests using EPICS CA and Python threads together

Based on code from  Friedrich Schotte, NIH, modified by Matt Newville
19-Apr-2010
"""

import time
from threading import Thread
import epics
import sys

from  pvnames import updating_pvlist
write = sys.stdout.write
def run_test(runtime=1, pvnames=None,  run_name='thread c'):
    write(' -> thread  "%s"  will run for %.3f sec\n ' % ( run_name, runtime))
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        write('      %s = %s (%s)\n' % (pvname, char_value, run_name))
        
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
    write( 'Done with Thread  %s' % run_name)
    
write( "First, run test in Foreground:\n")
run_test(2.0,  updating_pvlist, 'initial')

write("Run 2 Background Threads simultaneously:\n")
th1 = Thread(target=run_test,args=(5, updating_pvlist,  'A'))

th2 = Thread(target=run_test,args=(10, updating_pvlist, 'B'))
th1.start()
th2.start()

th1.join()
th2.join()

write( 'Done\n')

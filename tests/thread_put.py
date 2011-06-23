"""This script tests using EPICS CA and Python threads together

Based on code from  Friedrich Schotte, NIH, modified by Matt Newville
20-Apr-2010
"""

import time
from threading import Thread
import epics
import sys
import pvnames

epics.caput(pvnames.motor1,   0.3)
epics.caput(pvnames.motor2,  -20.0)
time.sleep(1.0)
epics.caput(pvnames.motor2, -20.0, wait=True)
sys.stdout.write('done with initial moves.\n')

def run_test(pvname,  target, run_name='thread c'):
    sys.stdout.write( ' -> thread  "%s"\n' % run_name)
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        sys.stdout.write('      %s = %s (%s)\n' % (pvname, char_value, run_name))
    epics.ca.context_create()
    p = epics.PV(pvname)
    sys.stdout.write('Put %s to %.3f   (%s)\n' % (pvname, target,run_name))
    p.put(target, wait=True)
    sys.stdout.write( 'Done with Thread %s\n' % run_name)
    epics.ca.context_destroy()
    
epics.ca.show_cache()

sys.stdout.write( "Run 2 Background Threads doing simultaneous put-with-waits:\n")
th1 = Thread(target=run_test,args=(  pvnames.motor1,  0.5,  'A'))
th2 = Thread(target=run_test,args=(  pvnames.motor2, 20.0,  'B'))
th1.start()
th2.start()

epics.ca.show_cache()
th2.join()
th1.join()

sys.stdout.write( 'Done.\n')
time.sleep(0.01)
epics.ca.show_cache()

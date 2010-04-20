"""This script tests using EPICS CA and Python threads together

Based on code from  Friedrich Schotte, NIH, modified by Matt Newville
20-Apr-2010
"""

import time
from threading import Thread
import epics
import sys

epics.caput('13IDC:m13.VAL', -2.0)
epics.caput('13IDC:m83.VAL', 35000.0)
time.sleep(3.0)
epics.caput('13IDC:m83.VAL', 35000.0, wait=True)

def run_test(pvname,  target, run_name='thread c'):
    sys.stdout.write( ' -> thread  "%s \n"   ' % run_name)
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        sys.stdout.write('      %s = %s (%s)\n' % (pvname, char_value, run_name))
    # epics.ca.context_create()
    # print epics.ca.attach_context(epics.ca.current_context())
    p = epics.PV(pvname)
    sys.stdout.write('Put %s to %.3f   (%s)\n' % (pvname, target,run_name))
    p.put(target, wait=True)
    sys.stdout.write( 'Done with Thread %s\n' % run_name)
    
sys.stdout.write( "Run 2 Background Threads doing simultaneous put/waits :")
th1 = Thread(target=run_test,args=(  '13IDC:m13.VAL',  3.0,  'A'))
th2 = Thread(target=run_test,args=(  '13IDC:m83.VAL',  33000.0,  'B'))
th1.start()
th2.start()

th1.join()
th2.join()

sys.stdout.write( 'Done.\n')

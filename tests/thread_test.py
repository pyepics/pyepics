"""This script tests using EPICS CA and Python threads together
Based on code from  Friedrich Schotte, NIH, modified by Matt Newville
19-Apr-2010
"""
import time
from  sys import stdout
from threading import Thread
import epics

from  pvnames import updating_pvlist
pvlist_a = updating_pvlist[:-1]
pvlist_b = updating_pvlist[1:]

def run_test(runtime=1, pvnames=None,  run_name='thread c'):
    msg = '-> thread "%s" will run for %.3f sec, monitoring %s\n'
    stdout.write(msg % (run_name, runtime, pvnames))
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        stdout.write('   %s = %s (%s)\n' % (pvname, char_value, run_name))
        stdout.flush()

    # epics.ca.use_initial_context()   #  epics.ca.create_context()
    start_time = time.time()
    pvs = [epics.PV(pvn, callback=onChanges) for pvn in pvnames]

    while time.time()-start_time < runtime:
        time.sleep(0.1)

    [p.clear_callbacks() for p in pvs]
    stdout.write( 'Completed Thread  %s\n' % ( run_name))

stdout.write( "First, create a PV in the main thread:\n")
p = epics.PV(updating_pvlist[0])

stdout.write("Run 2 Background Threads simultaneously:\n")
th1 = Thread(target=run_test,args=(3, pvlist_a,  'A'))
th1.start()

th2 = Thread(target=run_test,args=(6, pvlist_b, 'B'))
th2.start()

th2.join()
th1.join()
stdout.write('Done\n')

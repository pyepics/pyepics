"""This script tests using EPICS CA and Python threads together

  Based on code from  Friedrich Schotte, NIH
  modified by Matt Newville 19-Apr-2010

  modified MN, 22-April-2011 (1 year later!)
  to support new context-switching modes

"""

import time
import epics
import sys
from threading import Thread
from epics.ca import CAThread, withInitialContext
from  pvnames import updating_pvlist
write = sys.stdout.write
flush = sys.stdout.flush


pvs_b = []
names_b = []
for pvname in updating_pvlist:
    names_b.append(pvname)

names_a = names_b[1:]
pvs_a   = pvs_b[1:]

epics.ca.create_context()

def wait_for_changes(pvnames, runtime, runname):
    """basic test procedure called by other tests
    """
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        write('   %s= %s (%s)\n' % (pvname, char_value, runname))
        flush()
    t0 = time.time()
    pvs = []
    for pvn in pvnames:
        p = epics.PV(pvn)
        p.get()
        p.add_callback(onChanges)
        pvs.append(p)

    while time.time()-t0 < runtime:
        try:
            time.sleep(0.01)
        except:
            sys.exit()

    for p in pvs:
        p.clear_callbacks()

def run_initcontext(pvnames, runtime, run_name):
    write(' -> force inital ca context: thread=%s will run for %.3f sec\n' % (run_name, runtime))
    epics.ca.use_initial_context()
    wait_for_changes(pvnames, runtime, run_name)
    write( 'Done with Thread  %s\n' % ( run_name))

@withInitialContext
def run_decorator(pvnames, runtime, run_name):
    write(' -> use withInitialContext decorator: thread=%s will run for %.3f sec\n' % (run_name, runtime))
    wait_for_changes(pvnames, runtime, run_name)
    write( 'Done with Thread  %s\n' % ( run_name))

def run_CAThread(pvnames, runtime, run_name):
    write(' -> used with CAThread: thread=%s will run for %.3f sec\n' % (run_name, runtime))
    wait_for_changes(pvnames, runtime, run_name)
    write( 'Done with Thread  %s\n' % ( run_name))

def run_threads(threadlist):
    for th in threadlist:
        th.start()
    time.sleep(0.01)
    for th in threadlist:
        th.join()
    time.sleep(0.01)

def test_initcontext():
    write( 'Test use plain threading.Thread, force use of initial CA Context \n')
    th1 = Thread(target=run_initcontext, args=(names_a, 2, 'A'))
    th2 = Thread(target=run_initcontext, args=(names_b, 3, 'B'))
    run_threads((th1, th2))

def test_decorator():
    write( 'Test use plain threading.Thread, withInitialContext decorator\n')
    th1 = Thread(target=run_decorator, args=(names_a, 3, 'A'))
    th2 = Thread(target=run_decorator, args=(names_b, 5, 'B'))
    run_threads((th1, th2))

def test_cathread():
    write( 'Test use CAThread\n')
    th1 = CAThread(target=run_CAThread, args=(names_a, 3, 'A'))
    th2 = CAThread(target=run_CAThread, args=(names_b, 5, 'B'))
    run_threads((th1, th2))

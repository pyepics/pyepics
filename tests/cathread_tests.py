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
from epics.ca import CAThread
from  pvnames import updating_pvlist
write = sys.stdout.write
flush = sys.stdout.flush

epics.ca.PREEMPTIVE_CALLBACK=True
def create_pvs_test(pvnames, runtime, run_name, create_ctx=False, init_ctx=True):
    write(' -> create_pvs thread=%s will run for %.3f sec\n' % (run_name, runtime))
    write(' -> thread=%s: create_ctx=%s, init_ctx=%s\n' % (run_name, create_ctx, init_ctx))

    ###print 'Thread: current context= ', run_name, epics.ca.current_context(), epics.ca.initial_context
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        write('   %s= %s (%s)\n' % (pvname, char_value, run_name))
        flush()

    #if create_ctx:
    #    epics.ca.create_context()
    #elif init_ctx:
    #    epics.ca.use_initial_context()

    t0 = time.time()
    pvs = []
    for pvn in pvnames:
        p = epics.PV(pvn)
        p.get()
        p.add_callback(onChanges)
        pvs.append(p)

    while time.time()-t0 < runtime:
        time.sleep(0.01)

    for p in pvs:
        p.clear_callbacks()
    write( 'Done with Thread  %s\n' % ( run_name))
    if create_ctx:
        epics.ca.destroy_context()

def pass_pvs_test(pvs, runtime, run_name, create_ctx=False, init_ctx=False):
    write(' -> pass_pvs thread=%s will run for %.3f sec\n' % (run_name, runtime))
    write(' -> thread=%s: create_ctx=%s, init_ctx=%s\n' % (run_name, create_ctx, init_ctx))

    # print 'Thread: current context= ', epics.ca.current_context()
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        write('   %s= %s (%s)\n' % (pvname, char_value, run_name))
        flush()

    if create_ctx:
        epics.ca.create_context()
    elif init_ctx:
        epics.ca.use_initial_context()

    write('Name=%s, context=%s, %i pvs monitored\n' % (run_name,
                                                       repr(epics.ca.current_context()),
                                                       len(pvs)))
    t0 = time.time()
    for p in pvs:
        p.add_callback(onChanges)

    while time.time()-t0 < runtime:
        time.sleep(0.01)

    for p in pvs:
        p.clear_callbacks()
    write( 'Done with Thread  %s\n' % ( run_name))
    if create_ctx:
        epics.ca.destroy_context()

def run_threads(th1, th2):
    th1.start() ; th2.start()
    time.sleep(0.01)
    th1.join() ; th2.join()
    time.sleep(0.01)

# MAIN
write("Connecting to PVs\n")
pvs_b = []
names_b = []
for pvname in updating_pvlist:
    ###pvs_b.append(epics.PV(pvname))
    # pvs_b.append(pvname)
    names_b.append(pvname)

names_a = names_b[1:]
pvs_a   = pvs_b[1:]

##
write( 'Test 1: use plain threading.Thread, force use of initial CA Context \n')
kws = dict(create_ctx=True, init_ctx=True)
th1 = Thread(target=create_pvs_test,args=(names_a, 3, 'A'), kwargs=kws)
th2 = Thread(target=create_pvs_test,args=(names_b, 5, 'B'), kwargs=kws)
run_threads(th1, th2)
write('Test 1 Done\n---------------------\n')
sys.exit()

write('Test 2: use plain threading.Thread, create/destroy CA Context \n')
kws = dict(create_ctx=True, init_ctx=False)
th1 = Thread(target=create_pvs_test,args=(names_a, 3, 'A'), kwargs=kws)
th2 = Thread(target=create_pvs_test,args=(names_b, 5, 'B'), kwargs=kws)
run_threads(th1, th2)
write('Test 2 Done\n')

write('Test 3: use CAThread\n')
kws = dict(create_ctx=False, init_ctx=False)
th1 = CAThread(target=create_pvs_test,args=(names_a, 3, 'A'), kwargs=kws)
th2 = CAThread(target=create_pvs_test,args=(names_b, 5, 'B'), kwargs=kws)
run_threads(th1, th2)
write('Test 3 Done\n')

write('Test 4: pass_pvs, use plain threading.Thread, force use of initial CA Context\n')
kws = dict(create_ctx=False, init_ctx=True)
th1 = Thread(target=pass_pvs_test,args=(pvs_a, 3, 'A'), kwargs=kws)
th2 = Thread(target=pass_pvs_test,args=(pvs_b, 5, 'B'), kwargs=kws)
run_threads(th1, th2)
write('Test 4 Done\n---------------------\n')

write('Test 5: pass_pvs, use CAThread\n')
kws = dict(create_ctx=False, init_ctx=False)
th1 = CAThread(target=pass_pvs_test,args=(pvs_a, 3, 'A'), kwargs=kws)
th2 = CAThread(target=pass_pvs_test,args=(pvs_b, 5, 'B'), kwargs=kws)
run_threads(th1, th2)
write('Test 5 Done\n---------------------\n')

write('Test 6: pass_pvs, use Thread, PVS only, and NO context switching\n')
kws = dict(create_ctx=False, init_ctx=False)
th1 = Thread(target=pass_pvs_test,args=(pvs_a, 3, 'A'), kwargs=kws)
th2 = Thread(target=pass_pvs_test,args=(pvs_b, 5, 'B'), kwargs=kws)
run_threads(th1, th2)
write('Test 6 Done\n---------------------\n')


write('Test 7_pvs, use Thread, PVS only, and NO context switching\n')
kws = dict(create_ctx=False, init_ctx=False)
th1 = Thread(target=create_pvs_test,args=(names_a, 3, 'A'), kwargs=kws)
th2 = Thread(target=create_pvs_test,args=(names_b, 5, 'B'), kwargs=kws)
run_threads(th1, th2)
write('Test 7 Done\n---------------------\n')







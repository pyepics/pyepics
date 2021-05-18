from __future__ import print_function

import epics
import time
import pvnames
pvname1 = pvnames.updating_pvlist[0]
pvname2 = pvnames.updating_pvlist[1]

def wait(t=30):
    t0 = time.time()
    while time.time()-t0 < t:
        time.sleep(0.01)

change_count = 0
def onChange(pvname,  value=None, char_value=None, timestamp=None, **kw):
    global change_count
    change_count += 1
    print('  new value: %s = %s (%s) ' % ( pvname, char_value, time.ctime(timestamp)))

def test_pv1():
    global change_count
    change_count = 0
    epics.camonitor(pvname1, callback=onChange)
    wait(5)
    epics.camonitor_clear(pvname1)
    assert change_count > 5

def test_pv2():
    global change_count
    change_count = 0
    epics.camonitor(pvname2, callback=onChange)
    wait(5)
    epics.camonitor_clear(pvname2)
    assert change_count > 5

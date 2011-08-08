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

def onChange(pvname,  value=None, char_value=None, timestamp=None, **kw):
    print('  new value: %s = %s (%s) ' % ( pvname, char_value, time.ctime(timestamp)))

epics.camonitor(pvname1, callback=onChange)
epics.camonitor(pvname2, callback=onChange)


print('## Monitor 2 PVs with epics.camonitor for 10sec')

wait(10)

print('## clear monitor for ', pvname2)

epics.camonitor_clear(pvname2)

print('## Monitor remaining PV for 10sec')
wait(10)

print('done!')

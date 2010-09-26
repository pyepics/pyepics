import time
import epics

import pvnames

pvname = pvnames.updating_pv1 # motor1

mypv = epics.PV(pvname)

print 'Created PV = ', mypv
def onChanges(pvname=None, value=None, char_value=None, **kw):
    print 'PV Changed! ', pvname, value, char_value

mypv.add_callback(onChanges)

print 'Added a callback.  Now wait for changes'

def wait(timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout: time.sleep(1.e-4)

wait(10)

from epics import ca

import time
import sys
import pvnames
mypv = pvnames.updating_pv1

change_count = 0

def onChanges(pvname=None, value=None, **kw):
    global change_count
    change_count += 1
    sys.stdout.write( 'New Value: %s  value=%s, kw=%s\n' %( pvname, str(value), repr(kw)))

def wait(step=0.1, maxtime=30):
    t0 = time.time()
    while time.time()-t0 < maxtime:
        time.sleep(step)

def test_subscribe():
    global change_count
    chid = ca.create_channel(mypv)
    eventID = ca.create_subscription(chid, callback=onChanges)
    wait(maxtime=10)
    assert change_count > 5

import time
import sys

from epics import ca

import pvnames

pvname = pvnames.updating_pv1

def wait(step=0.1, maxtime=30):
    t0 = time.time()
    while time.time()-t0 < maxtime:
        time.sleep(step)

    
def setup_callback(pvname):
    def my_cb(pvname=None, value=None, **kw):
       sys.stdout.write( 'get: %s  value=%s, kw=%s\n' %( pvname, str(value), repr(kw)))
       sys.stdout.flush()

    chid = ca.create_channel(pvname)
    return ca.create_subscription(chid, callback=my_cb)

cb_ref = setup_callback(pvname)

wait()
    


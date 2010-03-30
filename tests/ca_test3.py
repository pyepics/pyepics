import time
from epics import ca

import pvnames

pvname = pvnames.updating_pv1

def wait(step=0.1, maxtime=30):
    t0 = time.time()
    while time.time()-t0 < maxtime:
        time.sleep(step)
    
def setup_callback(pvname):
    def my_cb(pvname=None, value=None, **kw):
       sys.stdout.write( 'get: %s  value=%s, kw=%s' %( pvname, str(value), repr(kw)))

    chid = ca.create_channel(pvname)
    return ca.create_subscription(chid, userfcn=my_cb)

cb_ref = setup_callback(pvname)

wait()
    

# ret   = ca.connect_channel(chid)
# ca.pend_event(1.e-3)
# 
# ftype = ca.field_type(chid)
# count = ca.element_count(chid)
# 
# host  = ca.host_name(chid)
# rwacc = ca.access(chid)
# 
# print chid, ftype, count, rwacc, host



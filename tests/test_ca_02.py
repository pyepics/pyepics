import time
from epics import ca

import pvnames

pvname = pvnames.updating_pv1
# '13IDA:DMM1Ch3_calc.VAL'

def wait(step=0.1, maxtime=30):
    t0 = time.time()
    while time.time()-t0 < maxtime:
        time.sleep(step)
    
def setup_callback(pvname):
    def my_cb(pvname=None, value=None, **kw):
        print 'get: ', pvname, value, kw

    chid = ca.create_channel(pvname)
    return ca.create_subscription(chid, userfcn=my_cb)

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

cb_ref = setup_callback(pvname)

wait()
    


#
#  demonstrates using the PV attribute  put_complete to
#  "poll for put complete", as an alternative to using
#   put(wait=True), which blocks.
# 

from EpicsCA import PV,  pend_event, connect_all
import time
import sys


pvname = sys.argv[1]
print ' Testing Non-blocking Put, checking wait status: ', pvname

def onChanges(pv=None):
    print ' PV Changed!!  ', pv.pvname, pv.value

rbv_events = 0
def rbvChanged(pv=None,**kw):
    x =pv.value
    global rbv_events
    rbv_events = rbv_events + 1



x = PV(pvname,use_control=True,callback=onChanges)

if pvname.endswith('.VAL'): pvname  = pvname[:-4]

rbpv =PV('%s.RBV' % pvname, callback=rbvChanged)


connect_all()


if x.count == 1:
    target = max(x.llim,min(x.hlim,-x.value))
    print x
    print x.llim, x.value
    print 'Moving PV %s to %i ' % (x.pvname, target)
    t0 = time.time()
    x.put(target,user_wait=True)
    while not x.put_complete:
        pend_event(0.1)
        print 'still moving: ', rbpv.value
        
print 'done!  # readback events seen during wait: ', rbv_events

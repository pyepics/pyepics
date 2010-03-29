
from EpicsCA import PV, connect_all
import time
import sys


pvname = sys.argv[1]
wait_time = float(sys.argv[2])
print ' Testing Put with Wait: ', pvname, wait_time

rbv_events = 0
def rbvChanged(pv=None,**kw):
    x =pv.value
    global rbv_events
    rbv_events = rbv_events + 1


def onChanges(pv=None):
    print ' PV Changed!!  ', pv.pvname, pv.value

def change2(pv=None):
    print ' Second callback: change #2  ', pv.pvname, pv.value, pv.units

x = PV(pvname,use_control=True,callback=onChanges)
x.add_callback(change2)
print x.get_info()

rbpv = None
if pvname.endswith('.VAL'):
    rbpv =PV(pvname[:-4] + '.RBV', callback=rbvChanged)

connect_all()
print rbpv
if x.count == 1:
    target = max(x.llim,min(x.hlim,-x.value))
    print 'Moving PV %s to %f ' % (x.pvname, target)
    t0 = time.time()
    x.put(target, wait=True, timeout=wait_time)
    print 'Move to %.3f seconds ' % (time.time()-t0)
else:
    print 'not testing put(wait=True) for array data'


print '# readback events seen during wait: ', rbv_events
print 'done.'

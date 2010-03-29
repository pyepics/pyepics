
from EpicsCA import PV, connect_all, pend_event
import time
import sys

pv = PV('13XRM:m3.VAL')
pv.get()
values = (-10,10,-10,11,0)
for v in values:
    pv.put(v,user_wait=True)
    print 'move to %f' % v
    while not pv.put_complete:
        pend_event(0.1)
        print '. '
    print 'done.'
    time.sleep(1.0)

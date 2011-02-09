from epics import ca

import time
import sys

mypv = '13IDA:DMM1Ch3_calc.VAL'

def onChanges(pvname=None, value=None, **kw):
    sys.stdout.write( 'New Value: %s  value=%s, kw=%s\n' %( pvname, str(value), repr(kw)))
    sys.stdout.flush()
    
chid = ca.create_channel(mypv)
eventID = ca.create_subscription(chid, callback=onChanges)

t0 = time.time()
while time.time()-t0 < 15.0:
    time.sleep(0.001)




#
# example of using a connection callback that will be called
# for any change in connection status

import epics
import time

from  pvnames import motor1

def onConnectionChange(pvname=None, conn= None, **kws):
    print 'PV connection status changed:  ', pvname,  conn
    
def onValueChange(pvname=None, value=None, host=None, **kws):
    print 'PV value changed:  ', pvname, value, host
    
mypv = epics.PV(motor1, 
                connection_callback= onConnectionChange,
                callback= onValueChange)

mypv.get()

print 'Now waiting, watching values and connection changes:'
t0 = time.time()
while time.time()-t0 < 300:
    time.sleep(0.001)

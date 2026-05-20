#
# example of using a connection callback that will be called
# for any change in connection status

import epics
import time
import sys
from  pvnames import motor1

write = sys.stdout.write
def onConnectionChange(pvname=None, conn= None, **kws):
    write('PV connection status changed: %s %s\n' % (pvname,  repr(conn)))
    sys.stdout.flush()

def onValueChange(pvname=None, value=None, host=None, **kws):
    write('PV value changed: %s (%s)  %s\n' % ( pvname, host, repr(value)))
    sys.stdout.flush()
mypv = epics.PV(motor1, 
                connection_callback= onConnectionChange,
                callback= onValueChange)

mypv.get()

write('Now waiting, watching values and connection changes:\n')
t0 = time.time()
while time.time()-t0 < 300:
    time.sleep(0.01)

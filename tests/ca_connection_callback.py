#
# example of using a connection callback that will be called
# for any change in connection status

import epics
import time


motor1 = '13IDC:m1'

def onConnectionChange(pvname=None,  **kws):
    print 'ca connection status changed:  ', pvname,  kws
    
chid = epics.ca.create_channel(motor1, userfcn=onConnectionChange)


print 'Now waiting, watching values and connection changes:'
t0 = time.time()
while time.time()-t0 < 300:
    time.sleep(0.001)

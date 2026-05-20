#
# example of using a connection callback that will be called
# for any change in connection status

import epics
import time
import pvnames



import sys
write = sys.stdout.write
def onConnectionChange(pvname=None,  **kws):
    write('ca connection status changed:  %s %s\n' % ( pvname, repr(kws)))
    
chid = epics.ca.create_channel(pvnames.long_pv, callback=onConnectionChange)

write('Now, restart simulation IOC -- waiting, watching values and connection changes:\n')
t0 = time.time()
while time.time()-t0 < 15:
    time.sleep(0.001)

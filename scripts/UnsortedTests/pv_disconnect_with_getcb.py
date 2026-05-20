#
# example of using a connection callback that will be called
# for any change in connection status

import epics
import time
import sys
from  pvnames import updating_pv1, updating_pvlist
epics.ca.PREEMPTIVE_CALLBACK = True 
write = sys.stdout.write
def onConnectionChange(pvname=None, conn= None, **kws):
    write('Connection changed: %s conn=%s (%s)\n' % (pvname,  repr(conn), time.ctime()))
    sys.stdout.flush()

def onValueChange(pvname=None, value=None, host=None, **kws):
    write('Value changed: %s = %s (%s)\n' % ( pvname, repr(value), time.ctime()))
    sys.stdout.flush()


# pv1 = epics.PV(updating_pv1, 
#                 connection_callback= onConnectionChange,
#                 callback= onValueChange)
# 
pxs = [epics.PV(thispv, 
                connection_callback= onConnectionChange,
                callback= onValueChange) for thispv in updating_pvlist]

for x in pxs:
    write("%s = %s\n" % (x.pvname, x.get(as_string=True)))

write('Now waiting, watching values and connection changes:\n')
t0 = time.time()
while time.time()-t0 < 300:
    try:
        time.sleep(0.01)
    except KeyboardInterrupt:
        break
#
# write('Some value changes should have been seens\n')
# write('Now, restart the IOC:\n')
# t0 = time.time()
# while time.time()-t0 < 60:
#     time.sleep(0.01)
# 
# write('You should have seen a connection message and new values\n')


write("done!\n")

epics.ca.show_cache()


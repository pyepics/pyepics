from __future__ import print_function

import time
import epics
import pvnames
print('== Test get/put for synchronous groups')

pvs = pvnames.motor_list

chids = [epics.ca.create_channel(pvname) for pvname in pvs]

for chid in chids:
    epics.ca.connect_channel(chid)
    epics.ca.put(chid, 0)

print('Now create synch group ')
sg = epics.ca.sg_create()

data = [epics.ca.sg_get(sg, chid) for chid in chids]

print('Now change these PVs for the next 10 seconds')
time.sleep(10.0)

print('Synchronous block:')
epics.ca.sg_block(sg)
print('Done.  Values')
for pvname, dat, chid in zip(pvs, data, chids):
    print("%s = %s" % (pvname, str( epics.ca._unpack(dat, chid=chid))))

epics.ca.sg_reset(sg)

print('OK, now we will put everything back to 0 synchronously')

for chid in chids:
    epics.ca.sg_put(sg, chid, 0)
print('sg_put done, but not blocked / commited. Sleep for 5 seconds ')
time.sleep(5.0)
print('Now Go: ')
epics.ca.sg_block(sg)
print('done.')


          

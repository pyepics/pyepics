import time
import sys
from epics import ca

import pvnames

pvname = pvnames.double_pv
host      = pvnames.double_pv_host


chid = ca.create_channel(pvname)
ret   = ca.connect_channel(chid)
ca.pend_event(1.e-3)
 
ftype  = ca.field_type(chid)
count  = ca.element_count(chid)
host    = ca.host_name(chid)
rwacc = ca.access(chid)
 
if  ftype ==6 and count == 1 and host.startswith(host) and rwacc.startswith('read'):
    sys.stdout.write('OK!\n')
else:
    sys.stdout.write("Error\n")


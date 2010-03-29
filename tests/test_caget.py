
from epics import caget, poll
import pvnames

pvs = (pvnames.double_pv, pvnames.enum_pv, pvnames.str_pv)

for p in pvs:
    print p, caget(p)


from epics.pv import PV
import EpicsArchiver
import time
import sys

NMAX = int(sys.argv[1])
N0 = 0
if len(sys.argv) > 2:
    N0 = int(sys.argv[2])
    

master = EpicsArchiver.MasterDB()

all_pvs = master.cache.select('*')

pv_names = [i['pvname'] for i in all_pvs[N0:N0+NMAX]]


# create
pvs = []
t0 = time.time()
for pvname in pv_names:
    o = PV(pvname)
    pvs.append(o)

t1 = time.time()

# connect
unconnected = 0
for o  in pvs:
    o.connect(timeout=0.1)
    if not o.connected:
        unconnected += 1

t2 = time.time()

# get
out = []
for o in pvs:
    if o.connected:
        v = o.get()
        out.append('%s = %s' % (o.pvname, repr(v)))

t3 = time.time()

print " %i PVS connected and fetched in %.4f seconds.  %i PVs did not connect." %(NMAX,  t3-t0, unconnected)

print " Times:      Create:     Connect:   Get: " 
print " Total       %.4f      %.4f     %.4f  " %( t1-t0, t2-t1, t3-t2)
print " perPV       %.4f      %.4f     %.4f " %( (t1-t0)/NMAX, (t2-t1)/NMAX, (t3-t2)/NMAX)


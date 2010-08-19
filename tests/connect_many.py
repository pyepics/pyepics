from epics.pv import PV
import EpicsArchiver
import time
import sys

NMAX = int(sys.argv[1])
N0 = 0
if len(sys.argv) > 1:
    N0 = int(sys.argv[2])
    
t0 = time.time()

master = EpicsArchiver.MasterDB()

all_pvs = master.cache.select('*')

pv_names = [i['pvname'] for i in all_pvs[N0:N0+NMAX]]
print 'A'
t1 = time.time() - t0
pvs = []
for pvname in pv_names:
    o = PV(pvname)
    pvs.append(o)

print 'B'

t2 = time.time() - t0
unconnected = 0
for o  in pvs:
    o.connect(timeout=0.1)
    if not o.connected:
        unconnected += 1
    xx = o.value
print 'C'               
t3 = time.time() - t0
#for o  in pvs:
#    xx = o.value

t4 = time.time() - t0

print " %i PVS: DB connect: Epics Connect: Epics Get:   ReGet:   Time=%.4f Not Connected=%i" %(NMAX,  t4, unconnected)
print "           %.4f         %.4f          %.4f        %.4f" %(t1, t2-t1, t3-t2, t4-t3 )
print "           %.4f         %.4f          %.4f        %.4f" %(t1/NMAX, (t2-t1)/NMAX, (t3-t2)/NMAX, (t4-t3)/NMAX )


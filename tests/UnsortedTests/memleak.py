import time
import gc
import os

import epics
import pvnames

pvlist = pvnames.updating_pvlist

def show_memory():
    gc.collect()
    if os.name == 'nt':
        return 'Windows memory usage?? pid=%i' % os.getpid()
    f = open("/proc/%i/statm" % os.getpid())
    mem = f.readline().split()
    f.close()
    return 'Memory: VmSize = %i kB  /  VmRss = %i kB' %( int(mem[0])*4 , int(mem[1])*4)

N_new = 0
def get_callback(pvname=None,value=None,**kw):
    global N_new
    N_new = N_new + 1
    
def monitor_events(t = 60.0):
    print( 'Processing PV requests:')
    t0 = time.time()
    endtime = t0 + t
    global N_new
    nnotify = 10
    while time.time() < endtime:
        epics.ca.pend_event(0.01)
        if N_new >= nnotify:
            print( "Saw %i changes in %.3f seconds:  %s" % (N_new,  time.time()-t0, show_memory()))
            N_new = 0
            t0 = time.time()

def run(t=10.0):
    pvs = [epics.PV(i, callback=get_callback) for i in pvlist]
    epics.ca.pend_io(1.0)
    for p in pvs: p.get()
    print( 'Monitoring %i PVs'  % len(pvs))
    monitor_events(t=t)
    
    print( 'Destroying PVs: ')
    for i in pvs:
        i.disconnect()
    print( epics.ca._cache.keys())
    epics.ca.show_cache()
    epics.ca.poll(0.01, 10.0)
    time.sleep(1.0)
    
for i in range(4):
    print( "==run #  ", i+1)
    run(t=15)

print( 'memory leak test complete.')



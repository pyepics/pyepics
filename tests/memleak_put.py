import time
import gc
import os
import epics

# a test for possible memory leaks on put()


pvlist = [ '13XRM:edb:clientID',
           '13XRM:edb:serverID',
           '13XRM:edb:arg01',
           '13XRM:edb:arg02',
           '13XRM:edb:arg03',
           '13XRM:edb:status']
       
def show_memory():
    gc.collect()
    if os.name == 'nt':
        return 'Windows memory usage?? pid=%i' % os.getpid()
    f = open("/proc/%i/statm" % os.getpid())
    mem = f.readline().split()
    f.close()
    return 'Memory: VmSize = %i kB  /  VmRss = %i kB' %( int(mem[0])*4 , int(mem[1])*4)

N_new = 0
def get_callback(pv=None):
    global N_new
    N_new = N_new + 1
    # print 'New value: ', pv.pvname, pv.char_value
    
def monitor_events(t = 600.0):
    print 'Processing PV requests:'
    t0 = time.time()
    endtime = t0 + t
    nx = 0
    global N_new
    nnotify = int(t / 30)
    while time.time() < endtime:
        epics.ca.pend_event(0.05)
        nx  = nx + 1
        if nx >=nnotify:
            print "changes (%i) / %.3f /  %s" % (N_new,  time.time()-t0, show_memory())
            N_new = 0
            nx = 0

pvs = [epics.PV(i, callback=get_callback) for i in pvlist]
epics.ca.pend_io()

for i in range(500):
    for p in pvs:
        p.put('test: run %i' % (i))
    epics.ca.pend_event(0.02)
    if i%20 == 0:     print "==run #  ", i,  show_memory()
    time.sleep(0.02)
    
epics.ca.pend_io(1.0)

print 'really done.'


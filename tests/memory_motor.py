import time
import sys

import epics
import gc

import pvnames

import os
def show_memory():
    gc.collect()
    if os.name == 'nt':
        return 'Windows memory usage?? pid=%i' % os.getpid()

    f = open("/proc/%i/statm" % os.getpid())
    mem = f.readline().split()
    f.close()
    sys.stdout.write('Memory: VmSize = %i kB  /  VmRss = %i kB\n' %( int(mem[0])*4 , int(mem[1])*4))

def get_callback(pvname=None, char_value=None,**kw):
    sys.stdout.write('OnGet %s: %s\n'  % (pvname, char_value))
    
def monitor_events(t = 10.0):
    sys.stdout.write('Processing PV requests:\n')
    t0 = time.time()
    while time.time()-t0 < t :
        epics.ca.poll()
    
def round():
    sys.stdout.write('== Creating some PVs\n ')
    pvs = []
    for field in ('VAL','DESC', 'OFF','FOFF', 'HLM','LLM','SET'):
        pvs.append(epics.PV("%s.%s" % (pvnames.motor1,field), callback=get_callback) )
    epics.ca.poll()

    for p in pvs: p.connect()
    monitor_events(t=4.)
    
    epics.ca.show_cache()
    sys.stdout.write('Destroying PVs:\n ')
    sys.stdout.flush()    
    for i in pvs:  i.disconnect()

    monitor_events(t=0.5)
        
for i in range(20):
    round()
    show_memory()

epics.ca.pend_io(1.0)


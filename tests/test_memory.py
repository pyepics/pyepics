import time
import EpicsCA
import gc
frm = '13XRM:m%i.%s'

import os
def show_memory():
    gc.collect()
    if os.name == 'nt':
        return 'Windows memory usage?? pid=%i' % os.getpid()

    f = open("/proc/%i/statm" % os.getpid())
    mem = f.readline().split()
    f.close()

    print 'Memory: VmSize = %i kB  /  VmRss = %i kB' %( int(mem[0])*4 , int(mem[1])*4)

def get_callback(pv=None):
    x = 'OnGet %s: %s '  % (pv.pvname, str(pv.value))
    
def monitor_events(t = 10.0):
    print 'Processing PV requests:'
    nx = 1
    while nx < int(10*t):
        EpicsCA.pend_event(0.1)
        time.sleep(0.01)
        nx  = nx + 1
        

def connect_pv(pvname):
    return  EpicsCA.PV(pvname , connect=False, callback=get_callback)
    
def round():
    pvs = []
    for i in range(1,2): # 6):
        for field in ('VAL','DESC','HLM','LLM','SET'):
            pvs.append( EpicsCA.PV(frm % (i,field), callback=get_callback) )
    EpicsCA.connect_all()

    monitor_events(t=1.2)
    
    EpicsCA.show_pvcache()
    print 'Destroying PVs: '
    for i in pvs:  i.disconnect()
    
    # EpicsCA.disconnect_all()
    monitor_events(t=0.5)

        
for i in range(20):
    print "================ ", i
    round()
    show_memory()

EpicsCA.pend_io(1.0)

print 'really done.'


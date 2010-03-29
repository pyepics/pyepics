import time
import gc
import os

import epics

# a list of pvs, some changing often

pvlist = [ '13IDC:scan1.P1PA',
           '13BMA:DMM1Ch2_calc.VAL',
           '13BMA:DMM1Ch3_calc.VAL',
           '13IDA:DMM1Ch2_calc.VAL',
           '13IDA:DMM1Ch3_calc.VAL',
           '13IDA:DMM2Ch9_raw.VAL',
           '13IDD:DMM3Dmm_raw.VAL',
           '13IDC:AbortScans.PROC',
           '13XRM:edb:file',
           '13XRM:edb:ExecState',
           '13IDA:m2.VAL', '13IDA:m2.DESC',
           '13IDA:m2.FOFF', '13IDA:m2.SET', '13IDA:m2.SPMG' ]
       
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
    
def monitor_events(t = 60.0):
    print 'Processing PV requests:'
    t0 = time.time()
    endtime = t0 + t
    nx = 0
    global N_new
    nnotify = int(t / 30)
    while time.time() < endtime:
        epics.ca.pend_event(0.005)
        nx  = nx + 1
        if nx >=nnotify:
            print "changes (%i) / %.3f /  %s" % (N_new,  time.time()-t0, show_memory())
            N_new = 0
            nx = 0

def run():
    pvs = [epics.PV(i, callback=get_callback) for i in pvlist]
    epics.ca.pend_io(1.0)
    print 'Monitoring %i PVs'  % len(pvs)
    monitor_events(t=60.0)
    
    # EpicsCA.show_pvcache()
    print 'Destroying PVs: '
    for i in pvs:  i=0.0
        
for i in range(10):
    print "==run #  ", i+1
    run()
    show_memory()

print 'really done.'


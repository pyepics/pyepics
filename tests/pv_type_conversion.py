import sys
import time
import epics
import pvnames

pvlist = (
    pvnames.str_pv,
    pvnames.int_pv,
    pvnames.float_pv,       
    pvnames.enum_pv,
    pvnames.char_arr_pv,
    pvnames.long_pv,
    pvnames.long_arr_pv,       
    pvnames.double_pv,
    pvnames.double_arr_pv,
    )

def onConnect(pvname=None,  **kw):
    print ' on Connect ', pvname, kw
    
def onChanges(pvname=None, value=None, **kw):
    print ' on Change ', pvname, value
        

def RunTest(pvlist, use_preempt=True, maxlen=16384, 
            use_numpy=True, use_time=False, use_ctrl=False):
    msg= ">>>Run Test: %i pvs, numpy=%s, time=%s, ctrl=%s, preempt=%s"
    print msg % (len(pvlist), use_numpy, use_time, use_ctrl, use_preempt)

    epics.ca.HAS_NUMPY = use_numpy
    epics.ca.PREEMPTIVE_CALLBACK = use_preempt
    epics.ca.AUTOMONITOR_MAXLENGTH = maxlen
    mypvs= []
    for pvname in pvlist:
        pv = epics.PV(pvname, connection_callback=onConnect,
                      callback=onChanges)
        mypvs.append(pv)
    epics.poll(evt=0.10, iot=10.0)

    for pv in mypvs:
        print '== ', pv.pvname, pv
        # time.sleep(0.1)
        # epics.poll(evt=0.01, iot=1.0)
        val  = pv.get()
        cval = pv.get(as_string=True)    
        if pv.count > 1:
            val = val[:12]
        print  pv.type, val, cval
    for pv in mypvs:
        pv.disconnect()
    time.sleep(0.01)


for use_preempt in (True, False):
    for use_numpy in (True, False):
        for use_time, use_ctrl in ((False, False), (True, False), (False, True)):
            time.sleep(0.001)
            RunTest(pvlist,
                    use_preempt=use_preempt,
                    use_numpy=use_numpy,
                    use_time=use_time,
                    use_ctrl=use_ctrl)
        # sys.exit()


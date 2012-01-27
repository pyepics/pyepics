import sys
import time
import epics
import pvnames

HAS_NUMPY = False
try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    pass
   
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
    print(' on Connect %s --  %s' % (pvname, repr(kw)))
    
def onChanges(pvname=None, value=None, **kw):
    print(' on Change %s =  %s' % (pvname, repr(value)))
        

def RunTest(pvlist, use_preempt=True, maxlen=16384, 
            use_numpy=True, form='native'):
    msg= ">>>Run Test: %i pvs, numpy=%s, form=%s, preempt=%s"
    print( msg % (len(pvlist), use_numpy, form, use_preempt))

    epics.ca.HAS_NUMPY = use_numpy and HAS_NUMPY
    epics.ca.PREEMPTIVE_CALLBACK = use_preempt
    epics.ca.AUTOMONITOR_MAXLENGTH = maxlen
    mypvs= []
    for pvname in pvlist:
        pv = epics.PV(pvname, form=form,
                      # connection_callback=onConnect,
                      # callback=onChanges
                      )
        mypvs.append(pv)
    epics.poll(evt=0.10, iot=10.0)

    for pv in mypvs:
        # time.sleep(0.1)
        # epics.poll(evt=0.01, iot=1.0)
        val  = pv.get()
        cval = pv.get(as_string=True)    
        if pv.count > 1:
            val = val[:12]
        print( '-> ', pv, cval)
        print( '   ', type(val), val)
    for pv in mypvs:
        pv.disconnect()
    time.sleep(0.01)


for use_preempt in (True, False):
    for use_numpy in (False,):
        for form in ('native', 'time', 'ctrl'):
            time.sleep(0.001)
            RunTest(pvlist,
                    use_preempt=use_preempt,
                    use_numpy=use_numpy,
                    form=form)
        # sys.exit()


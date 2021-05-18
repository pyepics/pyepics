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

pvlist = (pvnames.str_pv, pvnames.int_pv, pvnames.float_pv,
          pvnames.enum_pv, pvnames.char_arr_pv, pvnames.long_pv,
          pvnames.long_arr_pv, pvnames.double_pv, pvnames.double_arr_pv,
          pvnames.string_arr_pv)

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
        pv = epics.PV(pvname, form=form)
        mypvs.append(pv)
    epics.poll(evt=0.10, iot=10.0)

    for pv in mypvs:
        val  = pv.get()
        cval = pv.get(as_string=True)
        if pv.count > 1:
            val = val[:12]
        print( '-> ', pv, cval)
        print( '   ', type(val), val)
    for pv in mypvs:
        pv.disconnect()
    time.sleep(0.01)


def test_v1():
    RunTest(pvlist, use_preempt=True, use_numpy=True, form='native')

def test_v2():
    RunTest(pvlist, use_preempt=True, use_numpy=True, form='time')

def test_v3():
    RunTest(pvlist, use_preempt=True, use_numpy=True, form='ctrl')

def test_v4():
    RunTest(pvlist, use_preempt=True, use_numpy=False, form='native')

def test_v5():
    RunTest(pvlist, use_preempt=True, use_numpy=False, form='time')

def test_v6():
    RunTest(pvlist, use_preempt=True, use_numpy=False, form='ctrl')

from __future__ import print_function

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


def RunTest(pvlist, use_preempt=True, maxlen=16384, 
            use_numpy=True, use_time=False, use_ctrl=False):
    msg= ">>>Run Test: %i pvs, numpy=%s, time=%s, ctrl=%s, preempt=%s"
    print( msg % (len(pvlist), use_numpy, use_time, use_ctrl, use_preempt))

    epics.ca.HAS_NUMPY =  epics.ca.HAS_NUMPY and use_numpy
    epics.ca.PREEMPTIVE_CALLBACK = use_preempt
    epics.ca.AUTOMONITOR_MAXLENGTH = maxlen
    chids= []
    epics.ca.initialize_libca()    

    def onConnect(pvname=None,  **kw):
        print(' on Connect %s %s' % (pvname, repr(kw)))
        
    def onChanges(chid=None, value=None, **kw):
        print(' on Change chid=%i value=%s' % (int(chid), repr(value)))
        
    for pvname in pvlist:
        chid = epics.ca.create_channel(pvname, callback=onConnect)
        epics.ca.connect_channel(chid)
        eventID = epics.ca.create_subscription(chid, callback=onChanges)
        chids.append((chid, eventID))
        epics.poll(evt=0.025, iot=5.0)
    epics.poll(evt=0.025, iot=10.0)
    time.sleep(0.05)
    for (chid, eventID) in chids:
        print('=== %s   chid=%s' % (epics.ca.name(chid), repr(chid)))
        time.sleep(0.005)
        ntype = epics.ca.promote_type(chid, use_ctrl=use_ctrl,
                                      use_time=use_time)
        val  = epics.ca.get(chid, ftype=ntype)
        cval = epics.ca.get(chid, as_string=True)    
        if epics.ca.element_count(chid) > 10:
            val = val[:10]
        time.sleep(0.005)
        print("%i %s %s" % (ntype, epics.dbr.Name(ntype).lower(), cval))
    time.sleep(0.5)        
    print('----- finalizing CA')
    epics.ca.finalize_libca()
    time.sleep(0.05)
    
for use_preempt in (True, False):
    for use_numpy in (True, False): 
        for use_time, use_ctrl in ((False, False),
                                   (True, False),
                                   (False, True),
                                   ):
            print("====  NUMPY/TIME/CTRL ", use_numpy, use_time, use_ctrl)
            RunTest(pvlist,
                    use_preempt=use_preempt,
                    use_numpy=use_numpy,
                    use_time=use_time,
                    use_ctrl=use_ctrl)
        # sys.exit()
            

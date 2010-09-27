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
    print msg % (len(pvlist), use_numpy, use_time, use_ctrl, use_preempt)

    epics.ca.HAS_NUMPY = use_numpy
    epics.ca.PREEMPTIVE_CALLBACK = use_preempt
    epics.ca.AUTOMONITOR_MAXLENGTH = maxlen
    chids= []
    epics.ca.initialize_libca()    

    def onChanges(chid=None, value=None, **kw):
        print ' on Change ', chid, value
        
    for pvname in pvlist:
        chid = epics.ca.create_channel(pvname)
        epics.ca.connect_channel(chid)
        eventID = epics.ca.create_subscription(chid, userfcn=onChanges)
        chids.append((chid, eventID))
        epics.poll(evt=0.025, iot=5.0)
    epics.poll(evt=0.10, iot=10.0)

    for (chid,eventID) in chids:
        print '== ', epics.ca.name(chid), chid
        time.sleep(0.1)
        ntype = epics.ca.promote_type(chid, use_ctrl=use_ctrl,
                                      use_time=use_time)
        val  = epics.ca.get(chid, ftype=ntype)
        cval = epics.ca.get(chid, as_string=True)    
        if epics.ca.element_count(chid) > 1:
            val = val[:12]
        print ntype, epics.dbr.Name(ntype).lower(), val, cval
    print '----- finalizing CA'
    epics.ca.finalize_libca()
    
for use_preempt in (True, False):
    for use_numpy in (True, False):
        for use_time, use_ctrl in ((False, False), (True, False), (False, True)):
                RunTest(pvlist,
                        use_preempt=use_preempt,
                        use_numpy=use_numpy,
                        use_time=use_time,
                        use_ctrl=use_ctrl)
        # sys.exit()
                

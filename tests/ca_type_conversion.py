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

write = sys.stdout.write

def RunTest(pvlist, use_preempt=True, maxlen=16384, 
            use_numpy=True, use_time=False, use_ctrl=False):
    msg= ">>>Run Test: %i pvs, numpy=%s, time=%s, ctrl=%s, preempt=%s\n"
    write( msg % (len(pvlist), use_numpy, use_time, use_ctrl, use_preempt))

    epics.ca.HAS_NUMPY =  epics.ca.HAS_NUMPY and use_numpy
    epics.ca.PREEMPTIVE_CALLBACK = use_preempt
    epics.ca.AUTOMONITOR_MAXLENGTH = maxlen
    chids= []
    epics.ca.initialize_libca()    

    def onConnect(pvname=None,  **kw):
        write(' on Connect %s %s\n' % (pvname, repr(kw)))
        
    def onChanges(chid=None, value=None, **kw):
        write(' on Change chid=%i value=%s\n' % (int(chid), repr(value)))
        
    for pvname in pvlist:
        chid = epics.ca.create_channel(pvname, callback=onConnect)
        epics.ca.connect_channel(chid)
        eventID = epics.ca.create_subscription(chid, callback=onChanges)
        chids.append((chid, eventID))
        epics.poll(evt=0.025, iot=5.0)
    epics.poll(evt=0.025, iot=10.0)

    for (chid, eventID) in chids:
        write('=== %s   chid=%s\n' % (epics.ca.name(chid), repr(chid)))
        time.sleep(0.005)
        ntype = epics.ca.promote_type(chid, use_ctrl=use_ctrl,
                                      use_time=use_time)
        val  = epics.ca.get(chid, ftype=ntype)
        cval = epics.ca.get(chid, as_string=True)    
        if epics.ca.element_count(chid) > 10:
            val = val[:10]
        write("%i %s  %s %s \n" % (ntype, epics.dbr.Name(ntype).lower(), repr(val), cval))
    write('----- finalizing CA\n')
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
                

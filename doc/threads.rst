
===============================================
Using Python Threads with EPICS Channel Access
===============================================

An important feature of the epics python package is that it can be used
with Python threads.  This section of the document focuses on using Python
threads both with the `PV` objacte and with the procedural functions in the
`ca` module.

Using threads in Python is fairly simple, but Channel Access adds a
complication that the underlying CA library will call Python code within a
particular thread, and you need to set which thread that is.  The most rule
for using Threads with the epics module is to use
:data:`PREEMPTIVE_CALLBACK` =  ``True``.   This is the default  value, so
you usually do not need to change anything.

Example
=======

This is a simplified verstion of test code using Python threads.  It is
based on code from Friedrich Schotte, NIH, and included as `thread_test.py`
in the `tests` directory of the source distribution. 

In this example, we define a `run_test` procedure which will create PVs
from a supplied list, and monitor these PVs, printing out the values when
they change.  Two threads are created and run concurrently, with
overlapping PV lists, though one thread is run for a shorter time than the
other.::

    import time
    from threading import Thread
    import epics
        
    pvlist1 = ('13IDA:DMM1Ch2_raw.VAL', 'S:SRcurrentAI.VAL')
    pvlist2 = ( '13IDA:DMM1Ch3_raw.VAL', 'S:SRcurrentAI.VAL')
       
    def run_test(runtime=1, pvnames=None,  run_name='thread c'):
        print ' |-> thread  "%s"  will run for %.3f sec ' % ( run_name, runtime)
         
        def onChanges(pvname=None, value=None, char_value=None, **kw):
            print '      %s = %s (%s)' % (pvname, char_value, run_name)
                
        epics.ca.context_create()
        t0 = time.time()
        pvs = []
        for pvn in pvnames:
            p = epics.PV(pvn)
            p.get()
            p.add_callback(onChanges)
            pvs.append(p)
            
        while time.time()-t0 < runtime:
            time.sleep(0.01)
        for p in pvs: p.clear_callbacks()
        print 'Done with Thread ', run_name
            
    print "Run 2 Threads simultaneously:"
    th1 = Thread(target=run_test,args=(3, pvlist1,  'A'))
    th1.start()
    
    th2 = Thread(target=run_test,args=(6, pvlist2, 'B'))
    th2.start()
    
    th1.join()
    th2.join()
     
    print 'Done'
    
    
The `epics.ca.context_create()`  here is recommended, but appears to not be
necessary.  The output from this will look like::

    Run 2 Threads simultaneously:
     |-> thread  "A"  will run for 3.000 sec 
     |-> thread  "B"  will run for 6.000 sec 
          13IDA:DMM1Ch2_raw.VAL = -183.71218999999999 (A)
          13IDA:DMM1Ch3_raw.VAL = -133.09033299999999 (B)
          S:SRcurrentAI.VAL = 102.19321199346312 (A)
          S:SRcurrentAI.VAL = 102.19321199346312 (B)
          S:SRcurrentAI.VAL = 102.19109399346311 (A)
           S:SRcurrentAI.VAL = 102.19109399346311 (B)
          13IDA:DMM1Ch2_raw.VAL = -183.67300399999999 (A)
          13IDA:DMM1Ch3_raw.VAL = -133.04856000000001 (B)
          S:SRcurrentAI.VAL = 102.18830251346313 (A)
          S:SRcurrentAI.VAL = 102.18830251346313 (B)
          S:SRcurrentAI.VAL = 102.18780211346312 (B)
           S:SRcurrentAI.VAL = 102.18780211346312 (A)
          13IDA:DMM1Ch2_raw.VAL = -183.69587200000001 (A)
          13IDA:DMM1Ch3_raw.VAL = -133.00154800000001 (B)
          S:SRcurrentAI.VAL = 102.18441979346312 (A)
	  S:SRcurrentAI.VAL = 102.18441979346312 (B)
    Done with Thread  A
          S:SRcurrentAI.VAL = 102.18331875346311 (B)
          13IDA:DMM1Ch3_raw.VAL = -133.170962 (B)
          S:SRcurrentAI.VAL = 102.18109007346312 (B)
          S:SRcurrentAI.VAL = 102.18066463346311 (B)
          13IDA:DMM1Ch3_raw.VAL = -133.09478999999999 (B)
          S:SRcurrentAI.VAL = 102.17867355346313 (B)
          S:SRcurrentAI.VAL = 102.17707979346312 (B)
          13IDA:DMM1Ch3_raw.VAL = -133.04619199999999 (B)
          S:SRcurrentAI.VAL = 102.17559191346312 (B)
    Done with Thread  B
    Done
    
    
Note that while both threads ''A''  and ''B'' are running. a callback for
the PV `S:SRcurrentAI.VAL` is generated in each thread.

Note also that the callbacks for the PVs created in each thread are
'''explicitly cleared''' with `for p in pvs: p.clear_callbacks()`.
Without this, the callbacks for thread ''A'' '''will persist even after the
thread has completed!!!
     
    

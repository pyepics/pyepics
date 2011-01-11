===============================================
Advanced Topic with Python Channel Access
===============================================

.. _advanced-large-arrays-label:


Strategies for working with large arrays
============================================

EPICS Channels / Process Variables usually have values that can be stored
with a small number of bytes.  This means that their storage and transfer
speeds over real networks is not a significant concern.  However, some
Process Variables can store much larger amounts of data (say, several
megabytes) which means that some of the assumptions about dealing with
Channels / PVs may need reconsideration.  

When using PVs with large array sizes (here, I'll assert that *large* means
more than 1000 or so elements), it is necessary to make sure that the
environmental variable ``EPICS_CA_MAX_ARRAY_SIZE`` is suitably set.
Unfortunately, this represents a pretty crude approach to memory management
within Epics for handling array data as it is used not only sets how large
an array the client can accept, but how much memory will be allocated on
the server.  In addition, this value must be set prior to using the CA
library -- it cannot be altered during the running of a CA program.

Normally, the default value for ``EPICS_CA_MAX_ARRAY_SIZE`` is 16384 (16k,
and it turns out that you cannot set it smaller than this value!).  As
Python is used for clients, generally running on workstations or servers
with sufficient memory, this default value is changed to 2**24, or 16Mb)
when :mod:`epics.ca` is initialized.  If the environmental variable
``EPICS_CA_MAX_ARRAY_SIZE`` has not already been set.

The other main issue for PVs holding large arrays is whether they should be
automatically monitored.  For PVs holding scalar data or small arrays, any
penalty for automatically monitoring these variables (that is, causing
network traffic every time a PV changes) is a small price to pay for being
assured that the latest value is always available.  As arrays get larger
(as for data streams from Area Detectors), it is less obvious that
automatic monitoring is desirable.  

The Python :mod:`epics.ca` module defines a variable
:data:`AUTOMONITOR_MAXLENGTH` which controls whether array PVs are
automatically monitored.  The default value for this variable is 16384, but
can be changed at runtime.  Arrays with fewer elements than
:data:`AUTOMONITOR_MAXLENGTH` will be automatically monitored, unless
explicitly set, and arrays larger than :data:`AUTOMONITOR_MAXLENGTH` will
not be automatically monitored unless explicitly set. Auto-monitoring of
PVs can be be explicitly set with

   >>> pv2 = epics.PV('ScalerPV', auto_monitor=True)
   >>> pv1 = epics.PV('LargeArrayPV', auto_monitor=False)


Example handling Large Arrays
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is an example reading data from an `EPICS areaDetector
<http://cars9.uchicago.edu/software/epics/areaDetector.html>`_, as if it
were an image from a digital camera.  This uses the `Python Imaging Library
<http://www.pythonware.com/products/pil/>`_ for much of the image
processing:


>>> import epics
>>> import Image
>>> pvname = '13IDCPS1:image1:ArrayData'
>>> img_pv  = epics.PV(pvname)
>>>
>>> raw_image = img_pv.get(as_numpy=False)
>>> im_mode = 'RGB'
>>> im_size = (1360, 1024)
>>> img = Image.frombuffer(im_mode, im_size, raw_image, 'raw', im_mode, 0, 1)
>>> img.show()

The result looks like this (taken with a Prosilica GigE camera):


.. image:: AreaDetector1.png


Example using Character Waveforms as Long Strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


As EPICS strings can be only 40 characters long, Character Waveforms are
sometimes used to allow Long Strings.  While this can be a common usage for
character waveforms, this module resists the temptation to implicitly
convert such byte arrays to strings using ``as_string=True``.

As an exmple, let's say you've created a character waveform PV, as with
this EPICS database::
   
     grecord(waveform,"$(P):filename")  {
             field(DTYP,"Soft Channel")
             field(DESC,"file name")
             field(NELM,"128")
             field(FTVL,"CHAR")
     }
  
You can then use this with:

   >>> import epics
   >>> pvname = 'PREFIX:filename.VAL'
   >>> pv  = epics.PV(pvname)
   >>> print pv.info
   .... 
   >>> plain_val = pv.get()
   >>> print plain_val
   array([ 84,  58,  92, 120,  97, 115,  95, 117, 115, 101, 114,  92,  77,
        97, 114,  99, 104,  50,  48,  49,  48,  92,  70,  97, 115, 116,
        77,  97, 112,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0])
   >>> char_val = pv.get(as_string=True)
   >>> print char_val
   'T:\\xas_user\\March2010\\FastMap'


This uses the PV class, but the :meth:`get` method of :mod:`ca` is
essentially equivalent, as its *as_string* parameter works exactly the same
way.

.. _advanced-threads-label:


Using Python Threads 
=========================

An important feature of the epics python package is that it can be used
with Python threads.  This section of the document focuses on using Python
threads both with the `PV` object and with the procedural functions in the
`ca` module.

Using threads in Python is fairly simple, but Channel Access adds a
complication that the underlying CA library will call Python code within a
particular thread, and you need to set which thread that is.  The most rule
for using Threads with the epics module is to use
:data:`PREEMPTIVE_CALLBACK` =  ``True``.   This is the default  value, so
you usually do not need to change anything.

Thread Example
~~~~~~~~~~~~~~~

This is a simplified version of test code using Python threads.  It is
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
    pvlist2 = ('13IDA:DMM1Ch3_raw.VAL', 'S:SRcurrentAI.VAL')
       
    def run_test(runtime=1, pvnames=None,  run_name='thread c'):
        print ' |-> thread  "%s"  will run for %.3f sec ' % ( run_name, runtime)
        
        def onChanges(pvname=None, value=None, char_value=None, **kw):
            print '      %s = %s (%s)' % (pvname, char_value, run_name)
                
        # A new CA context must be created per thread
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
        for p in pvs: 
            p.clear_callbacks()
        print 'Done with Thread ', run_name
	epics.ca.context_destroy()     
            
    print "Run 2 Threads simultaneously:"
    th1 = Thread(target=run_test,args=(3, pvlist1,  'A'))
    th1.start()
    
    th2 = Thread(target=run_test,args=(6, pvlist2, 'B'))
    th2.start()
    
    th1.join()
    th2.join()
     
    print 'Done'
        
The calls to `epics.ca.context_create()` and `epics.ca.context_destroy()`
are required: forgetting them will suppress all callbacks, and is likely to
to lead in core dumps.  The output from this will look like::

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
    
Note that while both threads *A*  and *B* are running, a callback for
the PV `S:SRcurrentAI.VAL` is generated in each thread.

Note also that the callbacks for the PVs created in each thread are
**explicitly cleared**  with::

    for p in pvs: 
        p.clear_callbacks()

Without this, the callbacks for thread *A*  will persist even after the
thread has completed!!!
     
    
.. _advanced-sleep-label:

time.sleep() or epics.poll()?
================================

In order for a program to communicate with Epics devices, it needs to allow
some time for this communication to happen.   With
:data:`ca.PREEMPTIVE_CALLBACK` set to  ``True``, this communication  will
be handled in a thread separate from the main Python thread.  This means
that CA events can happen at any time, and :meth:`ca.pend_event` does not
need to be called to explicitly allow for event processing.   

Still, some time must be released from the main Python thread on occasion
in order for events to be processed.  The simplest way to do this is with 
:meth:`time.sleep`, so that an event loop can simply be::
 
    >>> while True:
    >>>     time.sleep(0.001)

Unfortunately, the :meth:`time.sleep` method is not a very high-resolution
clock, with typical resolutions of 1 to 10 ms, depending on the system.
Thus, even though events will be asynchronously generated and epics with
pre-emptive callbacks does not *require* :meth:`ca.pend_event` or
:meth:`ca.poll` to be run, better performance may be achieved with an event
loop of::

    >>> while True:
    >>>     epics.poll(evt=1.e-5, iot=0.1)

as the loop will be run more often than using :meth:`time.sleep`.




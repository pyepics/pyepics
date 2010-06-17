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
more than 100 or so elements), it is necessary to make sure that the
environmental variable ``EPICS_CA_MAX_ARRAY_SIZE`` is suitably set.
Practically, this should not be a significant concern, as this is set (to
2**31, or 2 Gb) when :mod:`epics.ca` is initialized.  If you do have the 
environmental variable ``EPICS_CA_MAX_ARRAY_SIZE`` set, that value will be
used instead.

The main issues for large arrays are:
  * should large arrays automatically be immediately converted to numpy
    arrays? 
  * should PVs for large arrays normally be automatically monitored?
  * should large arrays of character / byte arrays be automatically
    converted to strings as a way to overcome the very low limit on the
    length of normal EPICS strings?

For most scalar PVs and for small arrays, the answer to each of these would
almost certainly be *Yes*.  As arrays get larger (say, to the size of the
data stream from a typical Area Detector), answering *Yes* is much less
obvious.  The Python :mod:`epics.ca` module defines a variable
:data:`AUTOMONITOR_MAXLENGTH` which controls this behavior.  This value, with
the default value of 16384, controls both behaviors:

 * arrays of size for which PVs are automatically monitored.  That is,
   arrays with few elements than :data:`AUTOMONITOR_MAXLENGTH` will be
   automatically monitored.  In any case,  the auto-monitoring of PVs can
   be explicitly set with  

   >>> pv2 = epics.PV('ScalerPV', auto_monitor=True)
   >>> pv1 = epics.PV('LargeArrayPV', auto_monitor=False)

 * array size for automatic conversion of data to numpy arrays.  That is,
   arrays with few elements than :data:`AUTOMONITOR_MAXLENGTH` will be
   automatically converted to numpy arrays (if appropriate). 
   In any case,  this conversion can be overridden, with

   >>> chid = epics.ca.create_channel('SimplePV')
   >>> val1 = epics.ca.get(chid,  as_numpy = False)
   >>>
   >>> pv2  = epics.PV('ArrayPV')
   >>> val2 = pv2.get(as_numpy=False)

   When values for large arrays (that is, with more than
   :data:`AUTOMONITOR_MAXLENGTH` elements) are returned, this will be a *raw
   ctype* array.   This data can be iterated over or sent to many other
   modules, such as the :mod:`Image` module.

Finally, though it is common to use arrays of characters or bytes to
emulate a long string (EPICS sets a limit of 40 characters for its own
STRING type), this module resists the temptation to implicitly convert
byte arrays to strings.   You'll have to be explicit and use either

   >>> chid = epics.ca.create_channel('CharArrayPV')
   >>> val1 = epics.ca.get(chid,  as_string = True)
   >>>
   >>> pv2  = epics.PV('CharArrayPV')
   >>> val2 = pv2.get(as_string=True)

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
sometimes used to allow Long Strings.  Let's say you've created a character
waveform PV, as with this EPICS database:
   
   {{{ grecord....
   }}}
  
You can then use this with:

   >>> import epics
   >>> pvname = 'CharArrayPV.VAL'
   >>> pv  = epics.PV(pvname)
   >>> print pv.info
   .... 
   >>> plain_val = pv.get()
   >>> print plan_val
   >>> char_val = pv.get(as_string=True)
   >>> print char_val


This example uses PV objects, but the :meth:`get` method of :mod:`ca` is
essentially equivalent, as its *as_string* parameter works exactly the same
way.


.. _advanced-threads-label:


Using Python Threads 
======================

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
    
    
Note that while both threads *A*  and *B* are running. a callback for
the PV `S:SRcurrentAI.VAL` is generated in each thread.

Note also that the callbacks for the PVs created in each thread are
**explicitly cleared**  with::

    for p in pvs: 
        p.clear_callbacks()


Without this, the callbacks for thread *A*  will persist even after the
thread has completed!!!
     
    

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
environmental variable ``EPICS_CA_MAX_ARRAY_BYTES`` is suitably set.
Unfortunately, this represents a pretty crude approach to memory management
within Epics for handling array data as it is used not only sets how large
an array the client can accept, but how much memory will be allocated on
the server.  In addition, this value must be set prior to using the CA
library -- it cannot be altered during the running of a CA program.

Normally, the default value for ``EPICS_CA_MAX_ARRAY_BYTES`` is 16384 (16k,
and it turns out that you cannot set it smaller than this value!).  As
Python is used for clients, generally running on workstations or servers
with sufficient memory, this default value is changed to 2**24, or 16Mb)
when :mod:`epics.ca` is initialized.  If the environmental variable
``EPICS_CA_MAX_ARRAY_BYTES`` has not already been set.

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

As an example, let's say you've created a character waveform PV, as with
this EPICS database::

    record(waveform,"$(P):filename")  {
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


This uses the :class:`PV` class, but the :meth:`get` method of :mod:`ca` is
essentially equivalent, as its *as_string* parameter works exactly the same
way.

.. _advanced-threads-label:


Using Python Threads
=========================

An important feature of the PyEpics package is that it can be used with
Python threads, as Epics 3.14 supports threads for client code.  Even in
the best of cases, working with threads can be somewhat tricky and lead to
unexpected behavior, and the Channel Access library adds a small level of
complication for using CA with Python threads.  The result is that some
precautions may be in order when using PyEpics and threads.  This section
discusses the strategies for using threads with PyEpics.

First, to use threads with Channel Access, you must have
:data:`epics.ca.PREEMPTIVE_CALLBACK` = ``True``.  This is the default
value, but if :data:`epics.ca.PREEMPTIVE_CALLBACK` has been set to
``False``, threading will not work.

Second, if you are using :class:`PV` objects and not making heavy use of
the :mod:`ca` module (that is, not making and passing around chids), then
the complications below are mostly hidden from you.   If you're writing
threaded code, it's probably a good idea to read this just to understand
what the issues are.

Channel Access Contexts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Channel Access library uses a concept of *contexts* for its own thread
model, with contexts holding sets of threads as well as Channels and
Process Variables.  For non-threaded work, a process will use a single
context that is initialized prior doing any real CA work (done in
:meth:`ca.initialize_libca`).  In a threaded application, each new thread
begins with a new, uninitialized context that must be initialized or
replaced.  Thus each new python thread that will interact with CA must
either explicitly create its own context with :meth:`ca.create_context`
(and then, being a good citizen, destroy this context as the thread ends
with :meth:`ca.destroy_context`) or attach to an existing context.

The generally recommended approach is to use a single CA context throughout
an entire process and have each thread attach to the first context created
(probably from the main thread).  This avoids many potential pitfalls (and
crashes), and can be done fairly simply.  It is the default mode when using
PV objects.

The most explicit use of contexts is to put :func:`epics.ca.create_context`
at the start of each function call as a thread target, and
:func:`epics.ca.destroy_context` at the end of each thread.  This will
cause all the activity in that thread to be done in its own context.  This
works, but means more care is needed, and so is not the recommended.


The best way to attach to the initially created context is to call
:meth:`epics.ca.use_initial_context` before any other CA calls in each
function that will be called by :meth:`Thread.run`.  Equivalently, you can
add a :func:`withInitialContext` decorator to the function.  Creating a PV
object will implicitly do this for you, as long as it is your first CA
action in the function.  Each time you do a :meth:`PV.get` or
:meth:`PV.put` (or a few other methods), it will also check that the initial
context is being used.

Of course, this approach requires CA to be initialized already.  Doing that
*in the main thread* is highly recommended.  If it happens in a child
thread, that thread must exist for all CA work, so either the life of the
process or with great care for processes that do only some CA calls.  If
you are writing a threaded application in which the first real CA calls are
inside a child thread, it is recommended that you initialize CA in the main
thread,

As a convenience, the :class:`CAThread` in the :mod:`ca` module is
is a very thin wrapper around the standard :class:`threading.Thread` which
adding a call of  :meth:`epics.ca.use_initial_context` just before your
threaded function is run.  This allows your target functions to not
explicitly set the context, but still ensures that the initial context is
used in all functions.

How to work with CA and Threads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Summarizing the discussion above, to use threads you must use run in
PREEMPTIVE_CALLBACK mode.  Furthermore, it is recommended that you use a
single context, and that you initialize CA in the main program thread so
that your single CA context belongs to the main thread.  Using PV objects
exclusively makes this easy, but it can also be accomplished relatively
easily using the lower-level ca interface.  The options for using threads
(in approximate order of reliability) are then:

 1. use PV objects for threading work.

 2. use :class:`CAThread` instead of :class:`Thread` for threads that
 will use CA calls.

 3. put :func:`epics.ca.use_initial_context` at the top of all
 functions that might be a Thread target function, or decorate them with
 :func:`withInitialContext` decorator, *@withInitialContext*.

 4. use :func:`epics.ca.create_context` at the top of all functions
 that are inside a new thread, and be sure to put
 :func:`epics.ca.destroy_context` at the end of the function.

 5. ignore this advise and hope for the best.  If you're not creating
 new PVs and only reading values of PVs created in the main thread
 inside a child thread, you may not see a problems, at least not until
 you try to do something fancier.


Thread Examples
~~~~~~~~~~~~~~~

This is a simplified version of test code using Python threads.  It is
based on code originally from Friedrich Schotte, NIH, and included as
`thread_test.py` in the `tests` directory of the source distribution.

In this example, we define a `run_test` procedure which will create PVs
from a supplied list, and monitor these PVs, printing out the values when
they change.  Two threads are created and run concurrently, with
overlapping PV lists, though one thread is run for a shorter time than the
other.

.. literalinclude:: ../tests/thread_test.py

In light of the long discussion above, a few remarks are in order: This
code uses the standard Thread library and explicitly calls
:func:`epics.ca.use_initial_context` prior to any CA calls in the target
function.  Also note that the :func:`run_test` function is first called
from the main thread, so that the initial CA context does belong to the
main thread.  Finally, the :func:`epics.ca.use_initial_context` call in
:func:`run_test` above could be replaced with
:func:`epics.ca.create_context`, and run OK.

The output from this will look like::

    First, create a PV in the main thread:
    Run 2 Background Threads simultaneously:
    -> thread "A" will run for 3.000 sec, monitoring ['Py:ao1', 'Py:ai1', 'Py:long1']
    -> thread "B" will run for 6.000 sec, monitoring ['Py:ai1', 'Py:long1', 'Py:ao2']
       Py:ao1 = 8.3948 (A)
       Py:ai1 = 3.14 (B)
       Py:ai1 = 3.14 (A)
       Py:ao1 = 0.7404 (A)
       Py:ai1 = 4.07 (B)
       Py:ai1 = 4.07 (A)
       Py:long1 = 3 (B)
       Py:long1 = 3 (A)
       Py:ao1 = 13.0861 (A)
       Py:ai1 = 8.49 (B)
       Py:ai1 = 8.49 (A)
       Py:ao2 = 30 (B)
    Completed Thread  A
       Py:ai1 = 9.42 (B)
       Py:ao2 = 30 (B)
       Py:long1 = 4 (B)
       Py:ai1 = 3.35 (B)
       Py:ao2 = 31 (B)
       Py:ai1 = 4.27 (B)
       Py:ao2 = 31 (B)
       Py:long1 = 5 (B)
       Py:ai1 = 8.20 (B)
       Py:ao2 = 31 (B)
    Completed Thread  B
    Done

Note that while both threads *A* and *B* are running, a callback for the
PV `Py:ai1` is generated in each thread.

Note also that the callbacks for the PVs created in each thread are
**explicitly cleared**  with::

    [p.clear_callbacks() for p in pvs]

Without this, the callbacks for thread *A*  will persist even after the
thread has completed!


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




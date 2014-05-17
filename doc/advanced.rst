===============================================
Advanced Topic with Python Channel Access
===============================================

This chapter contains a variety of "usage notes" and implementation
details that may help in getting the best performance from the
pyepics module.


.. _advanced-get-timeouts-label:


The wait and timeout options for get(), ca.get_complete()
==============================================================

The *get* functions, :func:`epics.caget`, :func:`pv.get` and :func:`ca.get`
all ask for data to be transferred over the network.  For large data arrays
or slow networks, this can can take a noticeable amount of time.  For PVs
that have been disconnected, the *get* call will fail to return a value at
all.  For this reason, these functions all take a `timeout` keyword option.
The lowest level :func:`ca.get` also has a `wait` option, and a companion
function :func:`ca.get_complete`.  This section describes the details of
these.

If you're using :func:`epics.caget` or :func:`pv.get` you can supply a
timeout value.  If the value returned is ``None``, then either the PV has
truly disconnected or the timeout passed before receiving the value.  If
the *get* is incomplete, in that the PV is connected but the data has
simply not been received yet, a subsequent :func:`epics.caget` or
:func:`pv.get` will eventually complete and receive the value.  That is, if
a PV for a large waveform record reports that it is connected, but a
:func:`pv.get` returns None, simply trying again later will probably work::

    >>> p = epics.PV('LargeWaveform')
    >>> val = p.get()
    >>> val
    >>> time.sleep(10)
    >>> val = p.get()


At the lowest level (which :func:`pv.get` and :func:`epics.caget` use),
:func:`ca.get` issues a get-request with an internal callback function.
That is, it calls the CA library function
:func:`libca.ca_array_get_callback` with a pre-defined callback function.
With `wait=True` (the default), :func:`ca.get` then waits up to the timeout
or until the CA library calls the specified callback function.  If the
callback has been called, the value can then be converted and returned.

If the callback is not called in time or if `wait=False` is used but the PV
is connected, the callback will be called eventually, and simply waiting
(or using :func:`ca.pend_event` if :data:`ca.PREEMPTIVE_CALLBACK` is
``False``) may be sufficient for the data to arrive.  Under this condition,
you can call :func:`ca.get_complete`, which will NOT issue a new request
for data to be sent, but wait (for up to a timeout time) for the previous
get request to complete.

:func:`ca.get_complete` will return ``None`` if the timeout is exceeded or
if there is not an "incomplete get" that it can wait to complete.  Thus,
you should use the return value from :func:`ca.get_complete` with care.

Note that :func:`pv.get` (and so :func:`epics.caget`) will normally rely on
the PV value to be filled in automatically by monitor callbacks.  If
monitor callbacks are disabled (as is done for large arrays and can be
turned off) or if the monitor hasn't been called yet, :func:`pv.get` will
check whether it should can :func:`ca.get` or :func:`ca.get_complete`.

If not specified, the timeout for :func:`ca.get_complete` (and all other
get functions) will be set to::

   timeout = 0.5 + log10(count)

Again, that's the maximum time that will be waited, and if the data is
received faster than that, the *get* will return as soon as it can.


.. _advanced-connecting-many-label:

Strategies for connecting to a large number of PVs
====================================================

Occasionally, you may find that you need to quickly connect to a large
number of PVs, say to write values to disk.  The most straightforward way
to do this, say::

    import epics

    pvnamelist = read_list_pvs()
    pv_vals = {}
    for name in pvnamelist:
        pv = epics.PV(name)
	pv_vals[name] = pv.get()

does incur some small performance penalty.  As shown below, the penalty
is generally pretty small in absolute terms, but can be noticeable when
you are connecting to a large number (say, more than 100) PVs at once.

The cause for the penalty, and its remedy, are two-fold.  First, a `PV`
object automatically use connection and event callbacks.  Normally, these
are advantages, as you don't need to explicitly deal with them.  But,
internally, they do pause for network responses using :meth:`ca.pend_event`
and these pauses can add up.  Second, the :meth:`ca.get` also pauses for
network response, so that the returned value actually contains the latest
data right away, as discussed in the previous section.

The remedies are to
   1. not use connection or event callbacks.
   2. not explicitly wait for values to be returned for each :meth:`get`.

A more complicated but faster approach relies on a carefully-tuned use of
the CA library, and would be the following::

    from epics import ca

    pvnamelist = read_list_pvs()

    pvdata = {}
    for name in pvnamelist:
        chid = ca.create_channel(name, connect=False, auto_cb=False) # note 1
	pvdata[name] = (chid, None)

    for name, data in pvdata.items():
        ca.connect_channel(data[0])
    ca.poll()
    for name, data in pvdata.items():
        ca.get(data[0], wait=False)  # note 2

    ca.poll()
    for name, data in pvdata.items():
        val = ca.get_complete(data[0])
        pvdata[name][1] = val

    for name, data in pvdata.items():
        print name, data[1]

The code here probably needs detailed explanation.  The first thing to
notice is that this is using the `ca` level, not `PV` objects.  Second
(Note 1), the `connect=False` and `auto_cb=False` options to
:meth:`ca.create_channel`.  These respectively tell
:meth:`ca.create_channel` to not wait for a connection before returning,
and to not automatically assign a connection callback.  Normally, these are
not what you want, as you want a connected channel and to know if the
connection state changes.  But we're aiming for maximum speed here, so we
avoid these.

We then explicitly call :meth:`ca.connect_channel` for all the channels.
Next (Note 2), we tell the CA library to request the data for the channel
without waiting around to receive it.  The main point of not having
:meth:`ca.get` wait for the data for each channel as we go is that each
data transfer takes time.  Instead we request data to be sent in a separate
thread for all channels without waiting.  Then we do wait by calling
:meth:`ca.poll` once and only once, (not len(channels) times!).  Finally,
we use the :meth:`ca.get_complete` method to convert the data that has now
been received by the companion thread to a python value.

How much faster is the more explicit method?  In my tests, I used 20,000
PVs, all scalar values, all actually connected, and all on the same subnet
as the test client, though on a mixture of several vxWorks and linux IOCs.
I found that the simplest, obvious approach as above took around 12 seconds
to read all 20,000 PVs.  Using the `ca` layer with connection callbacks and
a normal call to :meth:`ca.get` also took about 12 seconds.  The method
without connection callbacks and with delayed unpacking above took about 2
seconds to read all 20,000 PVs.

Is that performance boost from 12 to 2 seconds significant?  If you're
writing a script that is intended to run once, fetch a large number of PVs
and get their values (say, an auto-save script that runs on demand), then
the boost is definitely significant.  On the other hand, if you're writing
a long running process or a process that will retain the PV connections and
get their values multiple times, the difference in start-up speed is less
significant.  For a long running auto-save script that periodically writes
out all the PV values, the "obvious" way using automatically monitored PVs
may be much *better*, as the time for the initial connection is small, and
the use of event callbacks will reduce network traffic for PVs that don't
change between writes.

Note that the tests also show that, with the simplest approach, 1,000 PVs
should connect and receive values in under 1 second.  Any application that
is sure it needs to connect to PVs faster than that rate will want to do
careful timing tests.  Finally, note also that the issues are not really a
classic *python is slow compared to C* issue, but rather a matter of how
much pausing with :meth:`ca.poll` one does to make sure values are
immediately useful.

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


.. index:: Threads
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

 1. use PV objects for threading work.  This ensures you're working in a
 single CA context.

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


.. index:: Multiprocessing
.. _advanced-multiprocessing-label:

Using Multiprocessing with PyEpics
===========================================

An alternative to Python threads that has some very interesting and
important features is to use multiple *processes*, as with the standard
Python :mod:`multiprocessing` module.  While using multiple processes has
some advantages over threads, it also has important implications for use
with PyEpics.  The basic issue is that multiple processes need to be fully
separate, and do not share global state.  For epics Channel Access, this
means that all those things like established communication channels,
callbacks, and Channel Access **context** cannot easily be share between
processes.

The solution is to use a :class:`CAProcess`, which acts just like
:class:`multiprocessing.Process`, but knows how to separate contexts
between processes.  This means that you will have to create PV objects for
each process (even if they point to the same PV).

.. class:: CAProcess(group=None, target=None, name=None, args=(), kwargs={})

    a subclass of :class:`multiprocessing.Process` that clears the global
    Channel Access context before running you target function in its own
    process.

.. class:: CAPool(processes=None, initializer=None, initargs=(), maxtasksperchild=None)

    a subclass of :class:`multiprocessing.pool.Pool`, creating a Pool of
    :class:`CAProcess` instances.


A simple example of using multiprocessing successfully is given:


.. literalinclude:: ../tests/test_multiprocessing.py

here, the main process and the subprocess can each interact with the same
PV, though they need to create a separate connection (here, using :class:`PV`)
in each process.

Note that different :class:`CAProcess` instances can communicate via
standard :class:`multiprocessing.Queue`.   At this writing,  no testing has
been done on using multiprocessing Managers.

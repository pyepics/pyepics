===============================================
Advanced Topic with Python Channel Access
===============================================

This chapter contains a variety of "usage notes" and implementation
details that may help in getting the best performance from the
pyepics module.


.. _advanced-get-timeouts-label:


The wait and timeout options for get(), ca.get_complete()
==============================================================

The *get* functions, :func:`epics.caget`, :func:`pv.get` and :func:`epics.ca.get`
all ask for data to be transferred over the network.  For large data arrays
or slow networks, this can can take a noticeable amount of time.  For PVs
that have been disconnected, the *get* call will fail to return a value at
all.  For this reason, these functions all take a `timeout` keyword option.
The lowest level :func:`epics.ca.get` also has a `wait` option, and a companion
function :func:`epics.ca.get_complete`.  This section describes the details of
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
:func:`epics.ca.get` issues a get-request with an internal callback function.
That is, it calls the CA library function
:func:`libca.ca_array_get_callback` with a pre-defined callback function.
With `wait=True` (the default), :func:`epics.ca.get` then waits up to the timeout
or until the CA library calls the specified callback function.  If the
callback has been called, the value can then be converted and returned.

If the callback is not called in time or if `wait=False` is used but the PV
is connected, the callback will be called eventually, and simply waiting
(or using :func:`epics.ca.pend_event` if :data:`epics.ca.PREEMPTIVE_CALLBACK` is
``False``) may be sufficient for the data to arrive.  Under this condition,
you can call :func:`epics.ca.get_complete`, which will NOT issue a new request
for data to be sent, but wait (for up to a timeout time) for the previous
get request to complete.

:func:`epics.ca.get_complete` will return ``None`` if the timeout is exceeded or
if there is not an "incomplete get" that it can wait to complete.  Thus,
you should use the return value from :func:`epics.ca.get_complete` with care.

Note that :func:`pv.get` (and so :func:`epics.caget`) will normally rely on
the PV value to be filled in automatically by monitor callbacks.  If
monitor callbacks are disabled (as is done for large arrays and can be
turned off) or if the monitor hasn't been called yet, :func:`pv.get` will
check whether it should can :func:`epics.ca.get` or :func:`epics.ca.get_complete`.

If not specified, the timeout for :func:`epics.ca.get_complete` (and all other
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

or even just::

    values = [epics.caget(name) for name in pvnamelist]


does incur some performance penalty. To minimize the penalty, we need to
understand its cause.

Creating a `PV` object (using any of :class:`pv.PV`, or :func:`pv.get_pv`,
or :func:`epics.caget`) will automatically use connection and event
callbacks in an attempt to keep the `PV` alive and up-to-date during the
seesion.  Normally, this is an advantage, as you don't need to explicitly
deal with many aspects of Channel Access.  But creating a `PV` does request
some network traffic, and the `PV` will not be "fully connected" and ready
to do a :meth:`PV.get` until all the connection and event callbacks are
established.  In fact, :meth:`PV.get` will not run until those connections
are all established.  This takes very close to 30 milliseconds for each PV.
That is, for 1000 PVs, the above approach will take about 30 seconds.

The simplest remedy is to allow all those connections to happen in parallel
and in the background by first creating all the PVs and then getting their
values.  That would look like::

    # improve time to get multiple PVs:  Method 1
    import epics

    pvnamelist = read_list_pvs()
    pvs = [epics.PV(name) for name in pvnamelist]
    values = [p.get() for p in pvs]

Though it doesn't look that different, this improves performance by a
factor of 100, so that getting 1000 PV values will take around 0.4 seconds.

Can it be improved further?  The answer is Yes, but at a price.  For the
discussion here, we'll can the original version "Method 0" and the method
of creating all the PVs then getting their values "Method 1".  With both of
these approaches, the script has fully connected PV objects for all PVs
named, so that subsequent use of these PVs will be very efficient.

But this can be made even faster by turning off any connection or event
callbacks, avoiding `PV` objects altogether, and using the `epics.ca`
interface.  This has been encapsulated into :func:`epics.caget_many` which
can be used as::

    # get multiple PVs as fast as possible:  Method 2
    import epics
    pvnamelist = read_list_pvs()
    values = epics.caget_many(pvlist)

In tests using 1000 PVs that were all really connected, Method 2 will take
about 0.25 seconds, compared to 0.4 seconds for Method 1 and 30 seconds for
Method 0.  To understand what :func:`epics.caget_many` is doing, a more
complete version of this looks like this::

    # epics.caget_many made explicit:  Method 3
    from epics import ca

    pvnamelist = read_list_pvs()

    pvdata = {}
    pvchids = []
    # create, don't connect or create callbacks
    for name in pvnamelist:
        chid = ca.create_channel(name, connect=False, auto_cb=False) # note 1
	pvchids.append(chid)

    # connect
    for chid in pvchids:
        ca.connect_channel(chid)

    # request get, but do not wait for result
    ca.poll()
    for chid in pvchids:
        ca.get(chid, wait=False)  # note 2

    # now wait for get() to complete
    ca.poll()
    for chid in pvchids:
        val = ca.get_complete(data[0])
        pvdata[ca.name(chid)] = val

The code here probably needs detailed explanation.  As mentioned above, it
uses the `ca` level, not `PV` objects.  Second, the call to
:meth:`epics.ca.create_channel` (Note 1) uses `connect=False` and `auto_cb=False`
which mean to not wait for a connection before returning, and to not
automatically assign a connection callback.  Normally, these are not what
you want, as you want a connected channel and to be informed if the
connection state changes, but we're aiming for maximum speed here.  We then
use :meth:`epics.ca.connect_channel` to connect all the channels.  Next (Note 2),
we tell the CA library to request the data for the channel without waiting
around to receive it.  The main point of not having :meth:`epics.ca.get` wait for
the data for each channel as we go is that each data transfer takes time.
Instead we request data to be sent in a separate thread for all channels
without waiting.  Then we do wait by calling :meth:`epics.ca.poll` once and only
once, (not `len(pvnamelist)` times!).  Finally, we use the
:meth:`epics.ca.get_complete` method to convert the data that has now been
received by the companion thread to a python value.

Method 2 and 3 have essentially the same runtime, which is somewhat faster
than Method 1, and much faster than Method 0. Which method you should use
depends on use case.  In fact, the test shown here only gets the PV values
once.  If you're writing a script to get 1000 PVs, write them to disk, and
exit, then Method 2 (:func:`epics.caget_many`) may be exactly what you
want.  But if your script will get 1000 PVs and stay alive doing other
work, or even if it runs a loop to get 1000 PVs and write them to disk once
a minute, then Method 1 will actually be faster.  That is doing
:func:`epics.caget_many` in a loop, as with::

    # caget_many() 10 times
    import epics
    import time
    pvnamelist = read_list_pvs()
    for i in range(10):
        values = epics.caget_many(pvlist)
	time.sleep(0.01)

will take around considerably *longer* than creating the PVs once and
getting their values in a loop with::

    # pv.get() 10 times
    import epics
    import time
    pvnamelist = read_list_pvs()
    pvs = [epics.PV(name) for name in pvnamelist]
    for i in range(10):
        values = [p.get() for p in pvs]
	time.sleep(0.01)

In tests with 1000 PVs, looping with :func:`epics.caget_many` took about
1.5 seconds, while the version looping over :meth:`PV.get()` took about 0.5
seconds.

To be clear, it is **connecting** to Epics PVs that is expensive, not the
retreiving of data from connected PVs.  You can lower the connection
expense by not retaining the connection or creating monitors on the PVs,
but if you are going to re-use the PVs, that savings will be lost quickly.
In short, use Method 1 over :func:`epics.caget_many` unless you've benchmarked
your use-case and have demonstrated that :func:`epics.caget_many` is better for
your needs.

.. _advanced-sleep-label:

time.sleep() or epics.poll()?
================================

In order for a program to communicate with Epics devices, it needs to allow
some time for this communication to happen.   With
:data:`epics.ca.PREEMPTIVE_CALLBACK` set to  ``True``, this communication  will
be handled in a thread separate from the main Python thread.  This means
that CA events can happen at any time, and :meth:`epics.ca.pend_event` does not
need to be called to explicitly allow for event processing.

Still, some time must be released from the main Python thread on occasion
in order for events to be processed.  The simplest way to do this is with
:meth:`time.sleep`, so that an event loop can simply be::

    >>> while True:
    >>>     time.sleep(0.001)

Unfortunately, the :meth:`time.sleep` method is not a very high-resolution
clock, with typical resolutions of 1 to 10 ms, depending on the system.
Thus, even though events will be asynchronously generated and epics with
pre-emptive callbacks does not *require* :meth:`epics.ca.pend_event` or
:meth:`epics.ca.poll` to be run, better performance may be achieved with an event
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
the :mod:`epics.ca` module (that is, not making and passing around chids), then
the complications below are mostly hidden from you.   If you're writing
threaded code, it's probably a good idea to read this just to understand
what the issues are.

Channel Access Contexts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Channel Access library uses a concept of *contexts* for its own thread
model, with contexts holding sets of threads as well as Channels and
Process Variables.  For non-threaded work, a process will use a single
context that is initialized prior doing any real CA work (done in
:meth:`epics.ca.initialize_libca`).  In a threaded application, each new thread
begins with a new, uninitialized context that must be initialized or
replaced.  Thus each new python thread that will interact with CA must
either explicitly create its own context with :meth:`epics.ca.create_context`
(and then, being a good citizen, destroy this context as the thread ends
with :meth:`epics.ca.destroy_context`) or attach to an existing context.

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

As a convenience, the :class:`CAThread` in the :mod:`epics.ca` module is
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

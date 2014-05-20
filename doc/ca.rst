=================================================
ca: Low-level Channel Access module
=================================================

.. module:: ca
   :synopsis: low-level Channel Access  module.

.. module:: epics.ca
   :synopsis: low-level Channel Access  module.

The :mod:`ca` module provides a low-level wrapping of the EPICS
Channel Access (CA) library, using ctypes.  Most users of the `epics`
module will not need to be concerned with most of the details here, and
will instead use the simple functional interface (:func:`epics.caget`,
:func:`epics.caput` and so on), or use the :class:`epics.PV` class to
create and use epics PV objects.


General description, difference with C library
=================================================

The goal of the :mod:`ca` module is to provide a fairly complete
mapping of the C interface to the CA library while also providing a
pleasant Python experience.  It is expected that anyone looking
into the details of this module is somewhat familiar with Channel
Access and knows where to consult the `Channel Access Reference
Documentation
<http://www.aps.anl.gov/epics/base/R3-14/11-docs/CAref.html>`_.
This document focuses on the differences with the C interface,
assuming a general understanding of what the functions are meant to
do.


Name Mangling
~~~~~~~~~~~~~

As a general rule, a CA function named `ca_XXX` in the C library will have the
equivalent function called `XXX` in the `ca` module.  This is because the
intention is that one will import the `ca` module with

    >>> from epics import ca

so that the Python function :func:`ca.XXX` will corresponds to the C
function `ca_XXX`.  That is, the CA library called its functions `ca_XXX`
because C does not have namespaces.  Python does have namespaces, and so
they are used.

Similar name *un-mangling* also happens with the DBR prefixes for
constants, held here in the `dbr` module.  Thus, the C constant DBR_STRING
becomes dbr.STRING in Python.


Other Changes and Omissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several function in the C version of the CA library are not implemented in
the Python module.  Most of these unimplemented functions are currently
seen as unnecessary for Python, though some of these could be added without
much trouble if needed. See :ref:`ca-omissions-label` for further details.

In addition, while the CA library supports several `DBR` types in C, not
all of these are supported in Python. Only native types and their DBR_TIME
and DBR_CTRL variants are supported here.  The DBR_STS and DBR_GR variants
are not, as they are subsets of the DBR_CTRL type, and space optimization
is not something you'll be striving for with Python.  Several `dbr_XXX`
functions are also not supported, as they appear to be needed only to be
able to dynamically allocate memory, which is not necessary in Python.


..  _ca-init-label:

Initialization, Finalization, and Life-cycle
==============================================

The Channel Access library must be initialized before it can be used.
There are 3 main reasons for this need:

  1. CA requires a context model (preemptive callbacks or  non-preemptive
  callbacks) to be specified before any actual calls can be made.

  2. the ctypes interface requires that the shared library be loaded
  before it is used.

  3. ctypes also requires that references to the library and callback
  functions be kept for the life-cycle of CA-using part of a program (or
  else they will be garbage collected).

As far as is possible, the :mod:`ca` module hides the details of the CA
lifecyle from the user, so that it is not necessary to to worry about
explicitly initializing a Channel Access session.  Instead, the library is
initialized as soon as it is needed, and intervention is really only
required to change default settings.  The :mod:`ca` module also handles
finalizing the CA session, so that core-dumps and warning messages do not
happen due to CA still being 'alive' as a program ends.

Because some users may wish to customize the initialization and
finalization process, the detailed steps will be described here.  These
initialization and finalization tasks are handled in the following way:

   * The :data:`libca` variable in the :mod:`ca` module holds a permanent,
     global reference to the CA shared object library (DLL).

   * the function :func:`initialize_libca` is called to initialize libca.
     This function takes no arguments, but does use the global Boolean
     :data:`PREEMPTIVE_CALLBACK` (default value of ``True``) to control
     whether preemptive callbacks are used.

   * the function :func:`finalize_libca` is used to finalize libca.
     Normally, this is function is registered to be called when a program
     ends with :func:`atexit.register`.  Note that this only gets called on
     a graceful shutdown. If the program crashes (for a non-CA related
     reason, for example), this finalization may not be done, and
     connections to Epics Variables may not be closed completely on the
     Channel Access server.

.. data:: PREEMPTIVE_CALLBACK

   sets whether preemptive callbacks will be used.  The default value is
   ``True``.  If you wish to run without preemptive callbacks this variable
   *MUST* be set before any other use of the CA library.  With preemptive
   callbacks enabled, EPICS communication will not require client code to
   continually poll for changes.   With preemptive callback disables,  you
   will need to frequently poll epics with :func:`pend_io` and
   func:`pend_event`.

.. data:: DEFAULT_CONNECTION_TIMEOUT

   sets the default `timeout` value (in seconds) for
   :func:`connect_channel`.  The default value is `2.0`

.. data:: AUTOMONITOR_MAXLENGTH

   sets the default array length (ie, how many elements an array has) above
   which automatic conversion to numpy arrays *and* automatic monitoring
   for PV variables is suppressed.  The default value is 65536.  To be
   clear: waveforms with fewer elements than this value will be
   automatically monitored changes, and will be converted to numpy arrays
   (if numpy is installed).  Larger waveforms will not be automatically
   monitored.

   :ref:`arrays-label` and :ref:`arrays-large-label` for more details.

Using the CA module
====================

Many general-purpose CA functions that deal with general communication and
threading contexts are very close to the C library:

.. autofunction:: initialize_libca

.. autofunction:: finalize_libca

.. function:: context_create()
.. autofunction:: create_context

.. function:: context_destroy()
.. autofunction:: destroy_context

.. autofunction:: current_context()

.. autofunction:: attach_context(context)

.. autofunction:: detach_context()

.. autofunction:: use_initial_context()

.. autofunction:: client_status(context, level)

.. autofunction:: version()

.. autofunction:: message(status)

.. autofunction:: flush_io()

.. autofunction:: replace_printf_handler(fcn=None)

.. autofunction:: pend_io(timeout=1.0)

.. autofunction:: pend_event(timeout=1.e-5)

.. autofunction:: poll(evt=1.e-5[, iot=1.0])


Creating and Connecting to Channels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The basic channel object is the Channel ID or ``chid``.  With the CA
library (and ``ca`` module), one creates and acts on the ``chid`` values.
These are simply :data:`ctypes.c_long` (C long integers) that hold the
memory address of the C representation of the channel, but it is probably
a good idea to treat these as object instances.

.. autofunction:: create_channel(pvname, connect=False, callback=None, auto_cb=True)

.. autofunction:: connect_channel(chid, timeout=None, verbose=False)


Many other functions require a valid Channel ID, but not necessarily a
connected Channel.  These functions are essentially identical to the CA
library versions, and include:

.. autofunction:: name(chid)

.. autofunction:: host_name(chid)

.. autofunction:: element_count(chid)

.. autofunction::   read_access(chid)

.. autofunction::   write_access(chid)

.. autofunction::   field_type(chid)

   See the *ftype* column from :ref:`Table of DBR Types <dbrtype_table>`.

.. autofunction::   clear_channel(chid)

.. autofunction::   state(chid)


A few additional pythonic functions have been added:

.. autofunction:: isConnected(chid)

.. autofunction:: access(chid)

.. autofunction:: promote_type(chid, [use_time=False, [use_ctrl=False]])

   See :ref:`Table of DBR Types <dbrtype_table>`.

.. data::  _cache

   The ca module keeps a global cache of Channels that holds connection
   status and a bit of internal information for all known PVs.  This cache
   is not intended for general use.

.. autofunction:: show_cache(print_out=True)


.. autofunction:: clear_cache()



Interacting with Connected Channels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a ``chid`` is created and connected there are several ways to
communicating with it.  These are primarily encapsulated in the functions
:func:`get`, :func:`put`, and :func:`create_subscription`, with a few
additional functions for retrieving specific information.

These functions are where this python module differs the most from the
underlying CA library, and this is mostly due to the underlying CA function
requiring the user to supply DBR TYPE and count as well as ``chid`` and
allocated space for the data.  In python none of these is needed, and
keyword arguments can be used to specify such options.

.. autofunction:: get(chid, ftype=None, count=None, as_string=False, as_numpy=True, wait=True, timeout=None)

   
   See :ref:`Table of DBR Types <dbrtype_table>` for a listing of values of
   *ftype*,


   See :ref:`arrays-large-label` for a discussion of strategies
   for how to best deal with very large arrays.


   See :ref:`advanced-connecting-many-label` for a discussion of when using
   `wait=False` can give a large performance boost.

   See :ref:`advanced-get-timeouts-label` for further discussion of the
   *wait* and *timeout* options and the associated :func:`get_complete`
   function.


.. autofunction:: get_complete(chid, ftype=None, count=None, as_string=False, as_numpy=True, timeout=None)

   See :ref:`advanced-get-timeouts-label` for further discussion.

.. autofunction::  put(chid, value, wait=False, timeout=30, callback=None, callback_data=None)

   For more on this *put callback*, see :ref:`ca-callbacks-label` below.

.. autofunction:: create_subscription(chid, use_time=False, use_ctrl=False, mask=None, callback=None)

   For more on writing the user-supplied callback, see :ref:`ca-callbacks-label` below.

.. warning::

   *event_id* is the id for the event (useful for clearing a subscription).
   You **must** keep the returned tuple in active variables, either as a
   global variable or as data in an encompassing class.
   If you do *not* keep this data, the return value will be garbage
   collected, the C-level reference to the callback will disappear, and you
   will see coredumps.

   On Linux, a message like::

       python: Objects/funcobject.c:451: func_dealloc: Assertion 'g->gc.gc_refs != (-2)' failed.
       Abort (core dumped)

   is a hint that you have *not* kept this data.


.. data:: DEFAULT_SUBSCRIPTION_MASK

   This value is the default subscription type used when calling
   :func:`create_subscription` with `mask=None`. It is also used by
   default when creating a :class:`PV` object with auto_monitor is set
   to ``True``.

   The initial default value is *dbr.DBE_ALARM|dbr.DBE_VALUE*
   (i.e. update on alarm changes or value changes which exceeds the
   monitor deadband.)  The other possible flag in the bitmask is
   *dbr.DBE_LOG* for archive-deadband changes.

   If this value is changed, it will change the default for all
   subsequent calls to :func:`create_subscription`, but it will not
   change any existing subscriptions.

.. autofunction:: clear_subscription(event_id)

Several other functions are provided:

.. autofunction::  get_timestamp(chid)

.. autofunction::  get_severity(chid)

.. autofunction::  get_precision(chid)

.. autofunction:: get_enum_strings(chid)

.. autofunction:: get_ctrlvars(chid)

    See :ref:`Table of Control Attributes <ctrlvars_table>`

.. _ctrlvars_table:

   Table of Control Attributes

    ==================== ==============================
     *attribute*             *data types*
    ==================== ==============================
     status
     severity
     precision             0 for all but double, float
     units
     enum_strs             enum only
     upper_disp_limit
     lower_disp_limit
     upper_alarm_limit
     lower_alarm_limit
     upper_warning_limit
     lower_warning_limit
     upper_ctrl_limit
     lower_ctrl_limit
    ==================== ==============================

Note that *enum_strs* will be a tuple of strings for the names of ENUM
states.

.. autofunction:: get_timevars(chid)


..  _ca-sg-label:

Synchronous Groups
~~~~~~~~~~~~~~~~~~~~~~~

Synchronous Groups can be used to ensure that a set of Channel Access calls
all happen together, as if in a *transaction*.  Synchronous Groups work in
PyEpics as of version 3.0.10, but more testing is probably needed.

The idea is to first create a synchronous group, then add a series of
:func:`sg_put` and :func:`sg_get` which do not happen immediately, and
finally block while all the channel access communication is done for the
group as a unit.  It is important to *not* issue :func:`pend_io` during the
building of a synchronous group, as this will cause pending :func:`sg_put`
and :func:`sg_get` to execute.

.. autofunction::  sg_create()

.. autofunction::  sg_delete(gid)

.. autofunction::  sg_block(gid[, timeout=10.0])

.. autofunction::  sg_get(gid, chid[, ftype=None[, as_string=False[, as_numpy=True]]])

   See further example below.

.. autofunction::  sg_put(gid, chid, value)

.. autofunction::  sg_test(gid)

.. autofunction::  sg_reset(gid)

An example use of a synchronous group::

    from epics import ca
    import time

    pvs = ('X1.VAL', 'X2.VAL', 'X3.VAL')
    chids = [ca.create_channel(pvname) for pvname in pvs]

    for chid in chids:
        ca.connect_channel(chid)
        ca.put(chid, 0)

    # create synchronous group
    sg = ca.sg_create()

    # get data pointers from ca.sg_get
    data = [ca.sg_get(sg, chid) for chid in chids]

    print 'Now change these PVs for the next 10 seconds'
    time.sleep(10.0)

    print 'will now block for i/o'
    ca.sg_block(sg)
    #
    # CALL ca._unpack with data points and chid to extract data
    for pvname, dat, chid in zip(pvs, data, chids):
        val = ca._unpack(dat, chid=chid)
        print "%s = %s" % (pvname, str(val))

    ca.sg_reset(sg)

    #  Now a SG Put
    print 'OK, now we will put everything back to 0 synchronously'

    for chid in chids:
        ca.sg_put(sg, chid, 0)

    print 'sg_put done, but not blocked / committed. Sleep for 5 seconds '
    time.sleep(5.0)
    ca.sg_block(sg)
    print 'done.'

..  _ca-implementation-label:

Implementation details
================================

The details given here should mostly be of interest to those looking at the
implementation of the `ca` module, those interested in the internals, or
those looking to translate lower-level C or Python code to this module.

DBR data types
~~~~~~~~~~~~~~~~~

.. _dbrtype_table:

   Table of DBR Types

    ============== =================== ========================
     *CA type*       *integer ftype*     *Python ctypes type*
    ============== =================== ========================
     string              0                 string
     int                 1                 integer
     short               1                 integer
     float               2                 double
     enum                3                 integer
     char                4                 byte
     long                5                 integer
     double              6                 double

     time_string        14
     time_int           15
     time_short         15
     time_float         16
     time_enum          17
     time_char          18
     time_long          19
     time_double        20
     ctrl_string        28
     ctrl_int           29
     ctrl_short         29
     ctrl_float         30
     ctrl_enum          31
     ctrl_char          32
     ctrl_long          33
     ctrl_double        34
    ============== =================== ========================

`PySEVCHK` and ChannelAccessExcepction: checking CA return codes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. exception:: ChannelAccessException

   This exception is raised when the :mod:`ca` module experiences
   unexpected behavior and must raise an exception

.. autofunction:: PySEVCHK(func_name, status[, expected=dbr.ECA_NORMAL])

.. autofunction:: withSEVCHK(fcn)


Function Decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to :func:`withSEVCHK`, several other decorator functions are
used heavily inside of ca.py or are available for your convenience.

.. autofunction:: withCA(fcn)

.. autofunction:: withCHID(fcn)

.. autofunction:: withConnectedCHID(fcn)

.. autofunction:: withInitialContext(fcn)

    See :ref:`advanced-threads-label` for further discussion.


Unpacking Data from Callbacks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Throughout the implementation, there are several places where data returned
by the underlying CA library needs to be be converted to Python data.  This
is encapsulated in the :func:`_unpack` function.  In general, you will not
have to run this code, but there is one exception:  when using
:func:`sg_get`, the values returned will have to be unpacked with this
function.

.. autofunction:: _unpack(chid, data[, count=None[, ftype=None[, as_numpy=None]]])

..  _ca-callbacks-label:

User-supplied Callback functions
================================

User-supplied callback functions can be provided for both :func:`put` and
:func:`create_subscription`.  Note that callbacks for `PV` objects are
slightly different: see :ref:`pv-callbacks-label` in the :mod:`pv` module
for details.

When defining a callback function to be run either when a :func:`put`
completes or on changes to the Channel, as set from
:func:`create_subscription`, it is important to know two things:

    1)  how your function will be called.
    2)  what is permissible to do inside your callback function.

In both cases, callbacks will be called with keyword arguments.  You should be
prepared to have them passed to your function.  Use `**kw` unless you are very
sure of what will be sent.

For callbacks sent when a :func:`put` completes, your function will be passed these:

    * `pvname` : the name of the pv
    * `data`:  the user-supplied callback_data (defaulting to ``None``).

For subscription callbacks, your function will be called with keyword/value
pairs that will include:

    * `pvname`: the name of the pv
    * `value`: the latest value
    * `count`: the number of data elements
    * `ftype`: the numerical CA type indicating the data type
    * `status`: the status of the PV (1 for OK)
    * `chid`:   the integer address for the channel ID.

Depending on the data type, and whether the CTRL or TIME variant was used,
the callback function may also include some of these as keyword arguments:

    * `enum_strs`: the list of enumeration strings
    * `precision`: number of decimal places of precision.
    * `units`:  string for PV units
    * `severity`: PV severity
    * `timestamp`: timestamp from CA server.

Note that a the user-supplied callback will be run *inside* a CA function,
and cannot reliably make any other CA calls.  It is helpful to think "this
all happens inside of a :func:`pend_event` call", and in an epics thread
that may or may not be the main thread of your program.  It is advisable to
keep the callback functions short and not resource-intensive.  Consider
strategies which use the callback only to record that a change has occurred
and then act on that change later -- perhaps in a separate thread, perhaps
after :func:`pend_event` has completed.

..  _ca-omissions-label:

Omissions
=========

Several parts of the CA library are not implemented in the Python module.
These are currently seen as unneeded (with notes where appropriate for
alternatives), though they could be added on request.

.. function:: ca_add_exception_event

   *Not implemented*: Python exceptions are raised where appropriate and
   can be used in user code.

.. function:: ca_add_fd_registration

   *Not implemented*

.. function:: ca_replace_access_rights_event

   *Not implemented*

.. function:: ca_client_status

   *Not implemented*

.. function:: ca_set_puser

   *Not implemented* : it is easy to pass user-defined data to callbacks as needed.

.. function:: ca_puser

   *Not implemented*: it is easy to pass user-defined data to callbacks as needed.

.. function:: ca_SEVCHK

   *Not implemented*: the Python function :func:`PySEVCHK` is
   approximately the same.

.. function:: ca_signal

   *Not implemented*: the Python function :func:`PySEVCHK` is
   approximately the same.

.. function:: ca_test_event

   *Not implemented*:  this appears to be a function for debugging events.
   These are easy enough to simulate by directly calling Python callback
   functions.

.. function:: ca_dump_dbr

   *Not implemented*

In addition, not all `DBR` types in the CA C library are supported.

Only native types and their DBR_TIME and DBR_CTRL variants are supported:
DBR_STS and DBR_GR variants are not. Several `dbr_XXX` functions are also
not supported, as they are needed only to dynamically allocate memory.

:class:`CAThread` class
==========================

.. class:: CAThread(group=None[, target=None[, name=None[, args=()[, kwargs={}]]]])

  create a CA-aware subclass of a standard Python :class:`threading.Thread`.  See the
  standard library documentation for further information on how to use Thread objects.

  A `CAThread` simply runs :func:`use_initial_context` prior to running each target
  function, so that :func:`use_initial_context` does not have to be explicitly put inside
  the target function.

  The See :ref:`advanced-threads-label` for further discussion.


Examples
=========

Here are some example sessions using the :mod:`ca` module.

Create, Connect, Get Value of Channel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note here that several things have been simplified compare to using CA in C:
initialization and creating a main-thread context are handled, and connection
of channels is handled in the background::

    from epics import ca
    chid  = ca.create_channel('XXX:m1.VAL')
    count = ca.element_count(chid)
    ftype = ca.field_type(chid)
    print "Channel ", chid, count, ftype
    value = ca.get()
    print value

Put, waiting for completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here we set a PVs value, waiting for it to complete::

    from epics import ca
    chid  = ca.create_channel('XXX:m1.VAL')
    ca.put(chid,  1.0, wait=True)

The  :func:`put` method will wait to return until the processing is
complete.

Define a callback to Subscribe to Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here, we *subscribe to changes* for a PV, which is to say we define a
callback function to be called whenever the PV value changes.   In the case
below, the function to be called will simply write the latest value out to
standard output::

    from epics import ca
    import time
    import sys

    # define a callback function.  Note that this should
    # expect certain keyword arguments, including 'pvname' and 'value'
    def onChanges(pvname=None, value=None, **kw):
        fmt = 'New Value: %s  value=%s, kw=%s\n'
        sys.stdout.write(fmt % (pvname, str(value), repr(kw)))
        sys.stdout.flush()

    # create the channel
    mypv = 'XXX.VAL'
    chid = ca.create_channel(mypv)

    # subscribe to events giving a callback function
    eventID = ca.create_subscription(chid, callback=onChanges)

    # now we simply wait for changes
    t0 = time.time()
    while time.time()-t0 < 10.0:
        time.sleep(0.001)

It is **vital** that the return value from :func:`create_subscription` is
kept in a variable so that it cannot be garbage collected.  Failure to keep
this value will cause trouble, including almost immediate segmentation
faults (on Windows) or seemingly inexplicable crashes later (on linux).

Define a connection callback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here, we define a connection callback -- a function to be called when the
connection status of the PV changes. Note that this will be called on
initial connection::

    import epics
    import time

    def onConnectionChange(pvname=None, conn=None, chid=None):
        print 'ca connection status changed:  ', pvname,  conn, chid

    # create channel, provide connection callback
    motor1 = '13IDC:m1'
    chid = epics.ca.create_channel(motor1, callback=onConnectionChange)

    print 'Now waiting, watching values and connection changes:'
    t0 = time.time()
    while time.time()-t0 < 30:
        time.sleep(0.001)

This will run the supplied callback soon after the channel has been
created, when a successful connection has been made.  Note that the
callback should be prepared to accept keyword arguments of `pvname`,
`chid`, and `conn` for the PV name, channel ID, and connection state
(``True`` or ``False``).


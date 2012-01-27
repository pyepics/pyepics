=================================================
ca: Low-level Channel Access module
=================================================

.. module:: ca
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

   :ref:`advanced-arrays-label` and :ref:`advanced-large-arrays-label` for
   more details. 

Using the CA module
====================

Many general-purpose CA functions that deal with general communication and
threading contexts are very close to the C library:

.. function:: initialize_libca()

   This initializes the CA library.  This must be called prior to any
   actual use of the CA library, but it is called automatically by the  :func:`withCA`
   decorator, so you should never need to call this in a real program.

.. function::  context_create()
.. function::  create_context()

   This will create a new context, using the value of
   :data:`PREEMPTIVE_CALLBACK` to set the context type. Note that CA
   library function has the irritating name of *context_create*.  Both that
   and *create_context* (which is more consistent with the Verb_Object of
   the rest of the CA library) are allowed.


.. function::  context_destroy()
.. function::  destroy_context()

   This will destroy the current context.

.. function::  current_context()

   This returns an integer value for the current context.

.. function::  attach_context(context)

   This attaches to the context supplied.

.. function::  detach_context()

   This detaches from the current context.

.. function::  use_initial_context()

   This attaches to the context created when libca is initialized.
   Using this function is recommended when writing Threaded programs that
   using CA.  See :ref:`advanced-threads-label` for further discussion.

.. function::  client_status(context, level)
   
   Print (to stderr) information about Channel Access status, including
   status for each channel, and search and connection statistics.

.. function::  version()

   Print Channel Access version string.  Currently, this should report
   '4.13' 

.. function::  message(status)

   Print a message corresponding to a Channel Access status return value. 

.. function::  flush_io()

.. function::  replace_printf_handler(fcn)

   replace the :func:`printf` function with the supplied function (defaults
   to :func:`sys.stderr.write` )

.. function::  pend_io([t=1.0])

.. function::  pend_event([t=1.e-5])

.. function::  poll([evt=1.e-5, [iot=1.0]])

   a convenience function which is equivalent to::

       pend_event(evt)
       pend_io_(iot)


Creating and Connecting to Channels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The basic channel object is the Channel ID or ``chid``.  With the CA
library (and ``ca`` module), one creates and acts on the ``chid`` values.
These are simply :data:`ctypes.c_long` (C long integers) that hold the
memory address of the C representation of the channel, but it is probably
a good idea to treat these as object instances.

.. function:: create_channel(pvname, [connect=False, [callback=None, auto_cb=True]]])

   creates a channel, returning the Channel ID ``chid`` used by other
   functions to identify this channel.

   :param pvname:   the name of the PV to create.
   :param connect:  whether to (try to) connect to PV as soon as possible.
   :type  connect:  ``True``/``False``
   :param callback:  user-defined Python function to be called when the connection state changes.
   :type callback:  ``None`` or callable.
   :param auto_cb:  whether to automatically use an internal callback.
   :type  auto_cb:  ``True``/``False``

   The user-defined callback function should be  prepared to accept keyword arguments of
         * `pvname`  name of PV
         * `chid`    ``chid`` Channel ID
         * `conn`    ``True``/``False``:  whether channel is connected.

   If `auto_cb` is ``True``, an internal connection callback is used so
   that you should not need to explicitly connect to a channel, unless you
   are having difficulty with dropped connections.


.. function:: connect_channel(chid, [timeout=None, [verbose=False]])

   explicitly connect to a channel (usually not needed, as implicit
   connection will be done when needed), waiting up to timeout for a
   channel to connect.  It returns the connection state, ``True`` or
   ``False``.

   :param chid:     ``chid`` Channel ID
   :param timeout:  maximum time to wait for connection.
   :type  timeout:  float or ``None``.
   :param verbose:  whether to print out debugging information

   if *timeout* is ``None``, the value of  :data:`DEFAULT_CONNECTION_TIMEOUT`
   is used (usually 2.0 seconds).

   Normally, channels will connect in milliseconds, and the connection
   callback will succeed on the first attempt.

   For un-connected Channels (that are nevertheless queried), the 'ts'
   (timestamp of last connection attempt) and 'failures' (number of failed
   connection attempts) from the :data:`_cache` will be used to prevent
   spending too much time waiting for a connection that may never happen.

Many other functions that require a valid Channel ID, but not necessarily a
connected Channel.  These functions are essentially identical to the CA
library are:

.. function::   name(chid)

   return PV name for Channel.

.. function::   host_name(chid)

   return host name and port serving Channel.

.. function::   element_count(chid)

   return number of elements in Channel's data.

.. function::   read_access(chid)

   return *read access* for a Channel: 1 for ``True``, 0 for ``False``.

.. function::   write_access(chid)

   return *write access* for a channel: 1 for ``True``, 0 for ``False``.

.. function::   field_type(chid)

   return the integer DBR field type. See the *ftype* column from
   :ref:`Table of DBR Types <dbrtype_table>`.

.. function::   clear_channel(chid)

   clear the channel.

.. function::   state(chid)

   return the state of the channel.

A few additional pythonic functions have been added:

.. function::     isConnected(chid)

   returns `dbr.CS_CONN==state(chid)` ie ``True`` for a connected channel
   or ``False`` for an unconnected channel.

.. function:: access(chid)

   returns a string describing read/write access: one of
   `no access`, `read-only`, `write-only`, or `read/write`

.. function::    promote_type(chid,[use_time=False, [use_ctrl=False]])

  promotes the native field type of a ``chid`` to its TIME or CTRL
  variant. See :ref:`Table of DBR Types <dbrtype_table>`.  Returns the
  integer corresponding to the promoted field value.

..  data::  _cache

    The ca module keeps a global cache of Channels that holds connection
    status and a bit of internal information for all known PVs.  This cache
    is not intended for general use.

.. function:: show_cache([print_out=True])

   this function will print out a listing of PVs in the current session to
   standard output.  Use the *print_out=False* option to be returned the
   listing instead of having it printed.

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

.. method:: get(chid[, ftype=None[, count=None[, as_string=False[, as_numpy=True[, wait=True[, timeout=None]]]]]])

   return the current value for a Channel. Note that there is not a separate form for array data.

   :param chid:  ``chid`` Channel ID
   :type  chid:  ctypes.c_long
   :param ftype:  field type to use (native type is default)
   :type ftype:  integer or ``None``
   :param count:  maximum element count to return (full data returned by default)
   :type count:  integer or ``None``
   :param as_string:  whether to return the string representation of the value.  See notes below.
   :type as_string:  ``True``/``False``
   :param as_numpy:  whether to return the Numerical Python representation  for array / waveform data.
   :type as_numpy:  ``True``/``False``
   :param wait:  whether to wait for the data to be received, or return immediately.
   :type wait:  ``True``/``False``
   :param timeout:  maximum time to wait for data before returning ``None``.
   :type timeout:  float or ``None``

   :func:`get` returns the value for the PV with channel ID *chid* or
   ``None``, which indicates an *incomplete get*

   For a listing of values of *ftype*, see :ref:`Table of DBR Types
   <dbrtype_table>`.  The optional *count* can be used to limit the
   amount of data returned for array data from waveform records.

   The *as_string* option warrants special attention: The feature is not
   as complete as as the *as_string* argument for :meth:`PV.get`.  Here,
   a string representing the value will always be returned. For Enum
   types, the name of the Enum state will be returned.  For waveforms of
   type CHAR, the string representation will be returned.  For other
   waveforms (with *count* > 1), a string like `<array count=3, type=1>`
   will be returned.  For all other types the result will from Python's
   :func:`str` function.

   The *as_numpy* option will cause an array value to be returned as a
   numpy array.  This is only applied if numpy can be imported.  See
   :ref:`advanced-large-arrays-label` for a discussion of strategies for
   how to best deal with very large arrays.

   The *wait* option controls whether to wait for the data to be
   received over the network and actually return the value, or to return
   immediately after asking for it to be sent.  If `wait=False` (that
   is, immediate return), the *get* operation is said to be
   *incomplete*.  The data will be still be received (unless the channel
   is disconnected) eventually but stored internally, and can be read
   later with :func:`get_complete`.  Using `wait=False` can be useful in
   some circumstances.  See :ref:`advanced-connecting-many-label` for a
   discussion.

   The *timeout* option sets the maximum time to wait for the data to be
   received over the network before returning ``None``.  Such a timeout
   could imply that the channel is disconnected or that the data size is
   larger or network slower than normal.  In that case, the *get*
   operation is said to be *incomplete*, and the data may become
   available later with :func:`get_complete`.

   See :ref:`advanced-get-timeouts-label` for further discussion of the
   *wait* and *timeout* options and the associated :func:`get_complete`
   function.


.. method:: get_complete(chid[, ftype=None[, count=None[, as_string=False[, as_numpy=True[, timeout=None]]]]])

   return the current value for a Channel, completing an earlier incomplete
   :func:`get` that returned ``None``, either because `wait=False` was
   used or because the data transfer did not complete before the timeout passed.

   :param chid:  ``chid`` Channel ID
   :type  chid:  ctypes.c_long
   :param ftype:  field type to use (native type is default)
   :type ftype:  integer
   :param count:  maximum element count to return (full data returned by default)
   :type count:  integer
   :param as_string:  whether to return the string representation of the value.  See notes below.
   :type as_string:  ``True``/``False``
   :param as_numpy:  whether to return the Numerical Python representation  for array / waveform data.
   :type as_numpy:  ``True``/``False``
   :param timeout:  maximum time to wait for data before returning ``None``.
   :type timeout:  float or ``None``

   This function will return ``None`` if the previous :func:`get`
   actually completed, or if this data transfer also times out.  See
   :ref:`advanced-get-timeouts-label` for further discussion.

.. method::  put(chid, value[, wait=False[, timeout=30[, callback=None[, callback_data=None]]]])

   sets the Channel to a value, with options to either wait (block) for the
   process to complete, or to execute a supplied callback function when the
   process has completed.  The chid and value are required.

   :param chid:  ``chid`` Channel ID
   :type  chid:  ctypes.c_long
   :param wait:  whether to wait for processing to complete (or time-out) before returning.
   :type  wait:  ``True``/``False``
   :param timeout:  maximum time to wait for processing to complete before returning anyway.
   :type  timeout:  float or ``None``
   :param callback: user-supplied function to run when processing has completed.
   :type callback: ``None`` or callable
   :param callback_data: extra data to pass on to a user-supplied callback function.

   :meth:`put` returns 1 on success and -1 on timed-out

   Specifying a callback will override setting `wait=True`.  This
   callback function will be called with keyword arguments

       pvname=pvname, data=callback_data

   For more on this *put callback*, see :ref:`ca-callbacks-label` below.

.. method::  create_subscription(chid[, use_time=False[, use_ctrl=False[, mask=None[, callback=None]]]])

   create a *subscription to changes*, The user-supplied callback function
   will be called on any changes to the PV.

   :param use_time: whether to use the TIME variant for the PV type
   :type use_time:  ``True``/``False``
   :param use_ctrl: whether to use the CTRL variant for the PV type
   :type use_ctrl:  ``True``/``False``
   :param  mask:    bitmask (combination of dbr.DBE_ALARM, dbr.DBE_LOG, dbr.DBE_VALUE) to control which changes result in a callback. Defaults to :data:`DEFAULT_SUBSCRIPTION_MASK`.
   :type mask:      integer
   :param callback:  user-supplied callback function
   :type callback:   ``None`` or callable

   :rtype: tuple containing *(callback_ref, user_arg_ref, event_id)*

   The returned tuple contains *callback_ref* an *user_arg_ref* which are
   references that should be kept for as long as the subscription lives
   (otherwise they may be garbage collected, causing no end of trouble).
   *event_id* is the id for the event (useful for clearing a subscription).

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
   :meth:`create_subscription` with `mask=None`. It is also used by
   default when creating a :class:`PV` object with auto_monitor is set
   to ``True``.

   The initial default value is *dbr.DBE_ALARM|dbr.DBE_VALUE*
   (i.e. update on alarm changes or value changes which exceeds the
   monitor deadband.)  The other possible flag in the bitmask is
   *dbr.DBE_LOG* for archive-deadband changes.

   If this value is changed, it will change the default for all
   subsequent calls to :meth:`create_subscription`, but it will not
   change any existing subscriptions.

.. method:: clear_subscription(event_id)

   clears a subscription given its *event_id*.

Several other functions are provided:

.. method::  get_timestamp(chid)

   return the timestamp of a channel -- the time of last update.

.. function::  get_severity(chid)

   return the severity of a channel.

.. function::  get_precision(chid)

   return the precision of a channel.  For channels with native type other
   than FLOAT or DOUBLE, this will be 0.

.. function:: get_enum_strings(chid)

    return the list of names for ENUM states of a Channel.  Returns  ``None``
    for non-ENUM Channels.

.. function:: get_ctrlvars(chid)

    returns a dictionary of CTRL fields for a Channel.  Depending on the
    native data type, the keys in this dictionary may include
    :ref:`Table of Control Attributes <ctrlvars_table>`

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

.. function:: get_timevars(chid)

    returns a dictionary of TIME fields for a Channel.  This will contain a
    *status*, *severity*, and *timestamp* key.

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

.. function::  sg_create()

   create synchronous group.  Returns a *group id*, `gid`, which is used to
   identify this group and is passed to all other synchronous group commands.

.. function::  sg_delete(gid)

   delete a synchronous group

.. function::  sg_block(gid[, t=10.0])

   block for a synchronous group to complete processing

.. function::  sg_get(gid, chid[, ftype=None[, as_string=False[, as_numpy=True]]])

   perform a `get` within a synchronous group.

   This function will not immediately return the value, of course, but the
   address of the underlying data.

   After the :func:`sg_block` has completed, you must use :func:`_unpack`
   to convert this data address to the actual value(s).

   See example below.

.. function::  sg_put(gid, chid, value)

   perform a `put` within a synchronous group.  This `put` cannot wait for
   completion.

.. function::  sg_test(gid)

  test whether a synchronous group has completed.

.. function::  sg_reset(gid)

   resets a synchronous group

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

..  function:: PySEVCHK(func_name, status[, expected=dbr.ECA_NORMAL])

    This checks the return *status* returned from a `libca.ca_***` and
    raises a :exc:`ChannelAccessException` if the value does not match the
    *expected* value.

    The message from the exception will include the *func_name* (name of
    the Python function) and the CA message from :mod:`message`.

..  function:: withSEVCHK

    this decorator handles the common case of running :func:`PySEVCHK` for
    a function whose return value is from a `libca.ca_***` function and
    whose return value should be ``dbr.ECA_NORMAL``.

Function Decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to :func:`withSEVCHK`, several other decorator functions are
used heavily inside of ca.py or are available for your convenience.

.. function:: withCA

   ensures that the CA library is initialized before many CA functions are
   called.  This prevents, for example, one creating a channel ID before CA
   has been initialized.

.. function:: withCHID

   ensures that CA functions which require a ``chid`` as the first argument
   actually have a  ``chid`` as the first argument.  This is not a highly
   robust test (it actually checks for a ctypes.c_long or int) but is
   useful enough to catch most errors before they would cause a crash of
   the CA library.

..  function:: withConnectedCHID

    ensures that the first argument of a function is a connected ``chid``.
    This test is (intended to be) robust, and will (try to) make sure a
    ``chid`` is actually connected before calling the decorated function.

..  function:: withInitialContext

    ensures that the called function uses the threading context initially defined.
    The See :ref:`advanced-threads-label` for further discussion.


Unpacking Data from Callbacks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Throughout the implementation, there are several places where data returned
by the underlying CA library needs to be be converted to Python data.  This
is encapsulated in the :func:`_unpack` function.  In general, you will not
have to run this code, but there is one exception:  when using
:func:`sg_get`, the values returned will have to be unpacked with this
function.

..  function:: _unpack(cdata, chid=None[, count=None[, ftype=None[, as_numpy=None]]])

    This takes the ctypes data `cdata` and returns the Python data.

   :param cdata:   cdata as returned by internal libca functions, and :func:`sg_get`.
   :param chid:    channel ID (optional: used for determining count and ftype)
   :param count:   number of elements to fetch (defaults to element count of chid  or 1)
   :param ftype:   data type of channel (defaults to native type of chid)
   :param as_numpy:  whether to convert to numpy array.
   :type as_numpy:  ``True``/``False``

..  _ca-callbacks-label:

User-supplied Callback functions
================================

User-supplied callback functions can be provided for both :meth:`put` and
:meth:`create_subscription`.  Note that callbacks for `PV` objects are
slightly different: see :ref:`pv-callbacks-label` in the :mod:`pv` module
for details.

When defining a callback function to be run either when a :meth:`put`
completes or on changes to the Channel, as set from
:meth:`create_subscription`, it is important to know two things:

    1)  how your function will be called.
    2)  what is permissible to do inside your callback function.

In both cases, callbacks will be called with keyword arguments.  You should be
prepared to have them passed to your function.  Use `**kw` unless you are very
sure of what will be sent.

For callbacks sent when a :meth:`put` completes, your function will be passed these:

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

.. function::  ca_add_exception_event

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

.. function::  ca_SEVCHK

   *Not implemented*: the Python function :func:`PySEVCHK` is
   approximately the same.
.. function::  ca_signal

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

The  :meth:`put` method will wait to return until the processing is
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

It is **vital** that the return value from :meth:`create_subscription` is
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


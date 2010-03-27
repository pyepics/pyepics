=========================================
:mod:`epics.ca` Low-Level Epics Interface
=========================================

Overview, difference with C library
===================================

This module provides a low-level wrapping of the EPICS Channel Access (CA)
library, using ctypes.  Most users of the `epics` module will not need to
be concerned with most the details here, and will only use the simple
functional interface (:func:`epics.caget`, :func:`epics.caput` and so on),
or create and use epics PV objects with :class:`epics.PV`, or define epics
devices with :class:`epics.Device`. 

The goal of this module is to stay fairly close to the C interface to the
CA library while also providing a pleasant Python experience.  It is
expected that anyone looking into the details of this module is somewhat
familar with Channel Access and knows where to consult the CA reference
documentation.  To that end, this document mostly describe the differences
with the C interface.


Name Mangling
~~~~~~~~~~~~~

As a general rule, a CA function named `ca_XXX` in the C library, the
equivalent function is called `XXX` in this module, as the intention is
that importing `ca` module with

    >>> from epics import ca

will result in a Python function named :func:`ca.XXX` that correpsonds to
the C function `ca_XXX`.
That is, Python namespaces are used in place of the name-mangling done in C
due to its lack of namespaces.

Similar name *un-mangling* also happens with the DBR prefixes for
constants, held here in the `dbr` module.  Thus, the C constant DBR_STRING
becomes dbr.STRING in Python.


Other Changes and Omissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several function in the C version of the CA library are not implemented in
the Python module.  These are currently seen as unnecessary for Python, 
though some could be added without much trouble.

In addition, while the CA library supports several `DBR` types in C, not
all of these are supported in Python. Only native types and their DBR_TIME
and DBR_CTRL variants are supported here.  The DBR_STS and DBR_GR variants
are not, as they are subsets of the DBR_CTRL type, and space optimization
is not something you'll be striving for with Python.  In additon, several
`dbr_XXX` functions are also not supported, as they appear to be needed
only to dynamically allocate memory.

See :ref:`ca-omissions-label` for further details.


..  _ca-init-label:

Initialization, Finalization, and Lifecycle
===========================================

.. module:: ca
   :synopsis: low-level Channel Access  module.

The CA library must be initialized before it can be used.  There are 3 main
reasons for this: 

  1. CA requires a context model (preemptive callbacks or  non-preemptive
  callbacks) to be specified before any actual calls are  made. 

  2. the ctypes interface requires that the shared library be loaded
  before it is used.

  3. because ctypes requires references to the library and callback
  functions be kept for the lifecycle of CA-using part of a program (or
  else they will be garbage collected). 

For these reasons, the handling of the lifecycle here for a CA session can
be slightly complicated.  As far as is possible, this module tries to
prevent the user from needing to worry about explicitly initializing the CA
session.  Instead, the library is initialized as soon as it is needed (but
not on loading the module!).  This module also handles finalizing the CA
session, so that coredumps and warning messages do not happen due to CA
still being 'alive' as a program ends.

Here, these tasks are handled by the following constructs:

   * :data:`libca` holds a permanent, global reference to the CA shared
     library.

   * the function :func:`initialze_libca` is called to ... initialize
     libca.  It takes no arguments, but uses the global boolean
     :data:`PREEMPTIVE_CALLBACK` (default of ``True``) to control whether
     preemtive callbacks are used.

   * the function :func:`finalize_libca` is used to finalize libca.
     Normally, this is function is registered to be called when a program
     ends with :func:`atexit.register`.  Note that this only gets called on
     a graceful shutdown. If the program crashes (for a non-CA related
     reason, for example), this finalization may not be done.
       

.. data:: PREEMPTIVE_CALLBACK 

   sets whether preemptive callbacks will be used.  The default value is
   ``True``.  This **MUST** be set before any other use of the CA library.

   With preemptive callbacks enabled, EPICS communication will
   not require client code to continually poll for changes.  

   More information on 

Using the CA module
====================

Many general-purpose CA functions that deal with general communication and
threading contexts are very close to the C library:

.. function::  context_create(context=0)

.. function::  context_destroy()

.. function::  attach_context(context)

.. function::  detach_context()

.. function::  current_context()

.. function::  client_status(context,level)

.. function::  message(status)

.. function::  flush_io()

.. function::  pend_io(t=1.0)

.. function::  pend_event(t=1.e-5)

.. function::  poll(ev=1.e-4,io=1.0)

     A notable addition the function which is equivalent to::
    
         pend_event(ev) 
	 pend_io_(io)


Creating and Connecting to Channels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The basic channel object is the "Channel ID" or ``chid``.  With the CA
library (and ``ca`` module), one creates and acts on the ``chid`` values, which are
:data:`ctypes.c_long`.

To create a channel, use

.. function:: create_channel(pvname,connect=False,userfcn=None)
   
    *pvname*   
      the name of the PV to create.
    *connect* 
     (True/False) whether to (try to) connnect now.
    *userfcn*
      a Python callback function to be called when the
      connection state changes.   This function should be
      prepared to accept keyword arguments of
      
         * `pvname`  name of pv
         * `chid`    chid value 
         * `conn`    True/False:  whether channel is connected.

   This returns a ``chid``.  Here


    Internally, a connection callback is used so that you should
    not need to explicitly connect to a channel.

To explicitly connect to a channel (usually not needed as implicit connection
will be done when needed), use

.. function:: connect_channel(chid,timeout=None,verbose=False,force=True)

  
   This explicitly tries to connect to a channel, waiting up to timeout for a
   channel to connect.  It returns the connection state.

    Normally, channels will connect very fast, and the connection callback
    will succeed the first time.

    For un-connected Channels (that are nevertheless queried), the 'ts'
    (timestamp of last connecion attempt) and 'failures' (number of failed
    connection attempts) from the _cache will be used to prevent spending too
    much time waiting for a connection that may never happen.

Other functions that require a valid (but not necessarily connected) Channel areessentially identical to the CA library are:

.. function::   name(chid)

.. function::   host_name(chid)

.. function::   element_count(chid)

.. function::     read_access(chid)

.. function::     write_access(chid)

.. function::     field_type(chid)

.. function::     clear_channel(chid)

.. function::     state(chid)

Three additional pythonic functions have been added:

.. function::     isConnected(chid)

   returns (dbr.CS_CONN==state(chid)) ie True or False for a connected, 
   unconnected channel

.. function:: access(chid)

   returns (read_access(chid) + 2 * write_access(chid))

.. function::    promote_type(chid,use_time=False,use_ctrl=False)

  which promotes the native field type of a chid to its TIME or CTRL variant.
  See :ref:`Table of DBR Types <dbrtype_table>`.

..  data::  _cache

    The ca module keeps a global cache of Channels that holds connection
    status and a bit of internal information for all known PVs.  This cache
    is not intended for general use, .... but ...

.. function:: show_cache(print_out=True)

   this function will print out a listing of PVs in the current session to
   standard output.  Use the *print_out=False* option to be returned the
   listing instead of having it printed. 


Interacting with Connected Channels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a chid is created and connected there are several ways to
communicating with it.  These are primarily encapsulated in the functions
:func:`get`, :func:`put`, and :func:`create_subscription`, with a few
additional functions for retrieving specific information.

These functions are where this python module differs the most from the
underlying CA library, and this is mostly due to the underlying CA function
requiring the user to supply DBR TYPE and count as well as chid and allocated
space for the data.  In python none of these is needed, and keyword arguments
can be used to specify such options.

To get a PV's value, use:

.. method::    get(chid[, ftype=None[, as_string=False[, as_numpy=False]]])

   return the current value for a Channel. Note that there is not a separate form for array data.

   :param chid:  channel ID
   :type  chid:  ctypes.c_long
   :param ftype:  field type to use (native type is default)
   :type ftype:  integer
   :param as_string:  whether to return the string representation of the
       value.  This is not nearly as full-featured as *as_string* for :meth:`PV.get`.
   :type as_string:  True/False
   :param as_numpy:  whether to return the Numerical Python representation
       for array / waveform data.  This is only applied if numpy can be imported.
   :type as_numpy:  True/False

For a listing of values of `ftype`, see :ref:`Table of DBR Types <dbrtype_table>`.

The 'as_string' option warrants special attention.  When used, this will
always return a string representation of the value.  For Enum types, this will
be the name of the Enum state. For Floats and Doubles, this will be the value
formatted according the the precision of the PV.  For waveforms of type CHAR,
this will be the string representation.  See :meth:`PV.get` for a more
full-featured version.

To set a PV's value, use:

.. function::  put(chid, value, wait=False, timeout=20, callback=None,callback_data=None) 

   set the Channel to a value, with options to either wait (block) for the
   process to complete, or to execute a supplied callback function when the
   process has completed.  The chid and value are required.

   :param chid:  channel ID
   :type  chid:  ctypes.c_long
   :param wait:  whether to wait for processing to complete (or time-out) before returning.
   :type  wait:  True/False
   :param timeout:  maximum time to wait for processing to complete before returning anyway.
   :type  timeout:  double
   :param callback: user-supplied function to run when processing has completed.
   :type callback: None or callable
   :param callback_data: extra data to pass on to a user-supplied callback function.

   :meth:`put` returns 1 on success and -1 on timed-out

   Specifying a callback will override setting *wait*=``True``.  This
   callback function will be called with keyword arguments 

       pvname=pvname, data=callback_data

   For more on this *put callback*, see :ref:`ca-callbacks-label` below.

.. function::   create_subscription(chid, use_time=False,use_ctrl=False,  mask=7, userfcn=None)

   create a *change* subscription, so that the user-supplied callback
   function is called on changes to the PV.

   :param use_time: whether to use the TIME variant for the PV type
   :type use_time:  True/False
   :param use_ctrl: whether to use the CTRL variant for the PV type
   :type use_ctrl:  True/False
   :param  mask:    integer bitmask to control which changes result in a     callback   
   :type mask:      integer
   :param userfcn:  user-supplied callback function
   :type userfcn:   callable or None
      
   :rtype: tuple containing *(callback_ref, user_arg_ref, event_id)*
   
   The returned tuple contains *callback_ref* an *user_arg_ref* which are
   references that should be kept for as long as the subscription lives
   (otherwise they may be garbage collected, causing no end of trouble).
   *event_id* is the id for the event (useful for clearing a subscription).

   For more on writing the user-supplied callback, see
   :ref:`ca-callbacks-label` below. 

.. function:: clear_subscription(event_id)
   
   clears a subscription given its *event_id*.

Other functions that are provided are

.. function::  get_timestamp(chid)

   return the timestamp of a channel -- the time of last update.

.. function::  get_severity(chid)

   return the severity of a channel.

.. function::  get_precision(chid)

   return the precision of a channel.  For channels with native type other
   than FLOAT or DOUBLE, this will be 0

.. function:: get_enum_strings(chid)

    return the list of names for ENUM states of a Channel.  Returns  None
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

.. function::  sg_create()

   create synchronous group.  Returns a *group id*, `gid`, which is used to
   identify this group and is passed to all other synchronous group commands.

.. function::  sg_delete(gid)

   delete a synchronous group

.. function::  sg_block(gid, t=10.0)

   block for a synchronous group to complete processing

.. function::  sg_get(gid,chid[, fype=None[, as_string=False[, as_numpy=True]]])

   perform a `get` within a synchronous group.

.. function::  sg_put(gid,chid, value)

   perform a `put` within a synchronous group.


.. function::  sg_test(gid)
  
  test whether a synchronous group has completed.
 
.. function::  sg_reset(gid)

   resets a synchronous group

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

Function Decorators 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several decorator functions are used heavily inside of ca.py

   * the decorator function :func:`withCA` ensures that the CA library is
     initialzed before many CA functions are called.  This prevents, for
     example, one creating a channel ID before CA has been initialized.
   
   * the decorator function :func:`withCHID` ensures that CA functions
     which require a ``chid`` as the first argument actually have a
     ``chid`` as the first argument.  This is not a highly robust test (it
     actually checks for a ctypes.c_long or int) but is useful enough to
     catch most errors before they would cause a crash of the CA library.

   * Additional decorators exist to check that CHIDs have connected, and to
     check return status codes from `libca` functions.


..  function:: withConnectedCHID 

    which ensures that the first argument of a function is a connected
    ``chid``.  This test is (intended to be) robust, and will (try to) make
    sure a ``chid`` is actually connected before calling the decorated
    function.
   
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

    a decorator to handle the common case of a function whose return value
    is from a `libca.ca_***` function and whose return value should be ``dbr.ECA_NORMAL``.


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
    2)  what is permissable to do inside your callback function.

In both cases, callbacks will be called with keyword arguments.  You should be
prepared to have them passed to your function.  Use `**kw` unless you are very
sure of what will be sent.

For callbacks sent when a :meth:`put` completes, your function will be passed these:

    * `pvname` : the name of the pv 
    * `data`:  the user-supplied callback_data (defaulting to ``None``). 

For subcription callbacks, your function will be called with keyword/value
pairs that will include:

    * `pvname`: the name of the pv 
    * `value`: the latest value
    * `count`: the number of data elements
    * `ftype`: the numerical CA type indicating the data type
    * `status`: the status of the PV (1 for OK)
    * `chid`: the integer address for the channel ID.

Depending on the data type, and whether the CTRL or TIME variant was used,
the callback function may also include some of these as keyword arguments:

    * `enum_strs`: the list of enumeration strings
    * `precision`: number of decimal places of precision.
    * `units`:  string for PV units
    * `severity`: PV severity
    * `timestamp`: timestamp from CA server.

A user-supplied callback will be run 'inside' a CA function, and cannot
reliably make any other CA calls -- this can cause instability..  It is
helpful to think 'this all happens inside of a pend_event call', and in an
epics thread that may or may not be the main thread of your program.  It is
advisable to keep the callback functions short, not resource-intensive, and
to consider strategies which use the callback to record that a change has
occurred and then act on that change outside of the callback (perhaps in a
separate thread, perhaps after pend_event() has completed, etc).

    
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

.. function:: ca_replace_printf_handler

   *Not implemented* 

.. function:: ca_client_status

   *Not implemented* 

.. function:: ca_set_puser

   *Not implemented* : it is easy to pass user-defined data to callbacks as needed.

.. function:: ca_puser

   *Not implemented*: it is easy to pass user-defined data to callbacks as needed.

.. function::  ca_SEVCHK

   *Not implemented*: the Python function :func:`Py_SEVCHK` is
   approximately the same.
.. function::  ca_signal

   *Not implemented*: the Python function :func:`Py_SEVCHK` is
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



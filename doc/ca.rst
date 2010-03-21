=============================
ca: Low-Level Epics Interface
=============================

Overview
========

This module provides a low level wrapping of the EPICS Channel Access (CA)
library, using ctypes.  Most users of the epics module will not need to be
concerned with the details here, and only use the simple functional interface
(caget, caput), or create and use epics PV objects, or define epics devices.

The goal of ths module is to stay fairly close to the C interface to CA while
also providing a pleasant Python experience.  It is expected that anyone
looking into the details of this module is somewhat familar with Channel
Access and knows where to consult the CA reference documentation.  To that
end, this document mostly describe the differences with the C interface.

Name Mangling
=============

In general, for a CA C function named 'ca_XXX', the function here is called
'XXX', as the intention is that importing this module with::

    import ca
or::

   from epics import ca

will make the function 'ca_XXX' be mapped to 'ca.XXX'

Similar name mangling also happens with the DBR in dbr.py, so that, for
example, DBR_STRING becomes dbr.STRING.

Initialization, Finalization, Lifecycle
=======================================

The CA library must be initialized before it can be used.  This is for 3 main
reasons: 1) CA requires a context model (preemptive callbacks or
non-preemptive callbacks) to be set on initialization, 2) the ctypes interface
requires that the shared library be loaded before it is used, and 3) because
ctypes requires references to the library and callback functions be kept for
the lifecycle of CA-using part of a program (or else they will be garbage
collected).

Because of this, the handling of the lifecycle here for a CA session is
slightly complicated.  As far as is possible, this module tries to prevent the
user from needing to explicitly initialez the CA session, and initializes the
library as soon as it is needed (but not on loading the module).  It also
handles finalizing the CA session, so that coredumps and warning messages
do not happen due to CA still being 'alive' as a program ends.


Here, these tasks are  handled by the following constructs:

   * libca holds a permanent, global reference to the CA shared library.

   * the function initialze_libca is called to ... initialize libca.  It takes
     no arguments, but uses the global boolean PREEMPTIVE_CALLBACK (default of
     True) to control whether preemtive callbacks are used.

   * the function finalize_libca() is used to finalize libca.  Normally, this
      is function is registered to be called when a program ends with
      'atexit.register'.  Note that this only gets called on a graceful
      shutdown. If the program crashes (even for a non-CA related reason),
      this finalization may not be done.
       
   * the decorator function withCA ensures that the CA library is initialzed
      before many CA functions are called.  This prevents, for example, one
      creating a channel ID before CA has been initialized.
   
   * the decorator function withCHID ensures that CA functions which require a
      chid as the first argument have a CHID as the first argument.  This is
      not a highly robust test (it actually checks for a ctypes.c_long or int)
      but is useful enough to catch most errors before they would cause a
      crash of the CA library.

   * there is also a decorator withConnectedCHID which ensures that the first
     argument of a function is a connected CHID.  This test is (intended to
     be) robust, and will (try to) make sure a CHID is actually connected before
     calling the decorated function.
   
As noted above, this module enables preemptive callbacks by default, so that
EPICS will communication will be faster and not requiring the client to
continually poll for changes.  To disable preemptive callbacks, set
ca.PREEMPTIVE_CALLBACK = False

*before* making any other calls to the library.

Tthis module keeps a global cache of PVs (in ca._cache) that holds connection
status for all known PVs.  Use the function
    ca.show_cache()

to print a listing of PV names and connection status, or use
    ca.show_cache(print_out=False)
to be returned this listing.


Using the CA module:
=============

Some  general purpose CA functions are very close to the C library:
    context_create(context=0)
    context_destroy()
    attach_context(context)
    detach_context()
    current_context()
    client_status(context,level)
    message(status)
    flush_io()
    pend_io(t=1.0)
    pend_event(t=1.e-5)

A notable addition the function
   poll(ev=1.e-4,io=1.0)

which is equivalent to pend_event(ev) ; pend_io_(io)

Creating and Connecting to Channels
==========================

To create a channel, use

 chid = ca.create_channel(pvname,connect=False,userfcn=None)
    pvname   the name of the PV to create.
    connect  (True/False) whether to (try to) connnect now.
    userfcn  a Python callback function to be called when the
             connection state changes.   This function should be
             prepared to accept keyword arguments 
                 pvname  name of pv
                 chid    ctypes chid value
                 conn    True/False:  whether channel is connected.

    Internally, a connection callback is used so that you should
    not need to explicitly connect to a channel.

To explicitly connect to a channel (usually not needed as implicit connection
will be done when needed), use

  state = connect_channel(chid,timeout=None,verbose=False,force=True):
   This explicitly tries to connect to a channel, waiting up to timeout for a
   channel to connect.

    Normally, channels will connect very fast, and the connection callback
    will succeed the first time.

    For un-connected Channels (that are nevertheless queried), the 'ts'
    (timestamp of last connecion attempt) and 'failures' (number of failed
    connection attempts) from the _cache will be used to prevent spending too
    much time waiting for a connection that may never happen.

Other functions that require a valid (but not necessarily connected) Channel are
essentially identical to the CA library are:
    name(chid)
    host_name(chid)
    element_count(chid)
    read_access(chid)
    write_access(chid)
    field_type(chid)
    clear_channel(chid)
    state(chid)

Three additional pythonic functions have been added:
    isConnected(chid)

which returns (dbr.CS_CONN==state(chid)) ie True or False for a connected,
unconnected channel

   access(chid)
returns (read_access(chid) + 2 * write_access(chid))

   promote_type(chid,use_time=False,use_ctrl=False)
which promotes the native field type of a chid to its TIME or CTRL variant

Interacting with Connected Channels
======================

Once a chid is created and connected there are several ways to communicating
with it.   These are primarily encapsulated in the functions
   get()
   put()
   create_subscription()

with a few additional functions for retrieving specific information.

These functions are where this python module differs the most from the
underlying CA library, and this is mostly due to the underlying CA function
requiring the user to supply DBR TYPE and count as well as chid and allocated
space for the data.  In python none of these is needed, and keyword arguments
can be used to specify such options.

To get a PV's value, use:
    get(chid, ftype=None, as_string=False, as_numpy=False)

This returns the current value for a Channel.  Options

      ftype         field type to use (native type is default)
      as_string    flag(True/False) to get a string representation
                       of the value returned.  This is not nearly as
                       featured as for a PV -- see pv.py for more details.
      as_numpy  flag(True/False) to use numpy array as the
                       return type for array data.       

Note that there is not a separate form for array data.

The 'as_string' option warrants special attention.  When used, this will
always return a string representation of the value.  For Enum types, this will
be the name of the Enum state. For Floats and Doubles, this will be the value
formatted according the the precision of the PV.  For waveforms of type CHAR,
this will be the string representation.

The 'as_numpy' option will promote numerical arrays to numpy arrays if numpy
is available.


To set a PV's value, use:
  put(chid, value, wait=False, timeout=20, callback=None,callback_data=None)

This puts a value to a Channel, with options to either wait (block) for the
process to complete, or to execute a supplied callback function when the
process has completed.  The chid and value are required, with options:

       wait        flag (True/False) for whether to block here while put
                     is processing.  Default = False
       timeout   maximum time to wait for a blocking put.
       callback  user-defined function to be called when put has
                     finished processing.
       callback_data data to pass onto the user-defined callback.

put() returns 1 on sucess and -1 on timed-out

Specifying a callback will override setting wait=True.  The callback function
will be called with keyword arguments
     pvname=pvname, data=callback_data
See note below on user-defined callbacks.

To define a subscription so that a callback is executed every time a PV changes,
use
   create_subscription(chid, use_time=False,use_ctrl=False,
                                  mask=7, userfcn=None)

this function returns a tuple of
   (callback_ref, user_arg_ref, event_id, ret_val)

Where callback_ref, user_arg_ref are references that should be kept for as
long as the subscription lives, event_id is the id for the event (useful for
clearing a subscription), and ret_val is the return value of the CA library call
ca_create_subscription().

Options for create_subscription include:
      use_time  flag(True/False) to use the TIME variant for the PV type
      use_ctrl   flag(True/False) to use the CTRL variant for the PV type
      mask      integer bitmask to control which changes result in a callback
      userfcn   user-supplied callback function

See not below on callback functions.

A subscription can be cleared with 
    clear_subscription(event_id)

Other functions that are provided are

   get_precision(chid)

return the precision of a channel.  For channels with native type other than
FLOAT or DOUBLE, this will be 0

    get_enum_strings(chid)

return the list of names for ENUM states of a Channel.  Returns  None for non-ENUM
Channels.

    get_ctrlvars(chid)

returns a dictionary of CTRL fields for a Channel.  Depending on  the native type,
the keys in this dictionary may include

        status severity precision units enum_strs upper_disp_limit
        lower_disp_limit upper_alarm_limit lower_alarm_limit
        upper_warning_limit lower_warning_limit upper_ctrl_limit
        lower_ctrl_limit
        
enum_strs will be a  list of strings for the names of ENUM states.
        
User-supplied Callback functions
====================

User-supplied callback functions can be provided for both put() and create_subscription()

For both cases, it is important to keep two things in mind:
   how your function will be called
   what is permissable to do inside your callback function.

In both cases, callbacks will be called with keyword arguments.  You should be
prepared to have them passed to your function.  Use **kw unless you are very
sure of what will be sent.

For put callbacks, your function will be passed
    pvname=pvname, data=data,
where pvname is the name of the pv, and data is the user-supplied
callback_data (defaulting to None).

For subcription callbacks, your function will be called with keyword/value
pairs that will include
    pvname=pvname,  value=value
and may include several other pairs depending on the data type and whether the
TIME or CTRL variant was used.

A user-supplied callback will be run 'inside' a CA function, and cannot
reliably make any other CA calls.  It is helpful to think 'this all happens
inside of a pend_event call', and in an epics thread that may or may not be
the main thread of your program.  It is advisable to keep the callback
functions short, not resource-intensive, and to consider strategies which use
the callback to record that a change has occurred and then act on that change
outside of the callback (perhaps in a separate thread, perhaps after
pend_event() has completed, etc).

    
Omissions
======

Several parts of the CA library are not implemented (yet?).
These include the following functions:

    ca_add_exception_event()
    ca_add_fd_registration()
    ca_dump_dbr()  * 
    ca_client_status()
    ca_puser() *
    ca_replace_access_rights_event()
    ca_replace_printf_handler()
    ca_set_puser() *
    ca_signal()
    ca_sg_block()
    ca_sg_create()
    ca_sg_delete()
    ca_sg_array_get()
    ca_sg_array_put()
    ca_sg_reset()
    ca_sg_test()
    ca_test_event() *
    ca_test_io() * 
    ca_SEVCHK() *
    dbr_size() *
    dbr_size_n() *
    dbr_value_size() *

Some of these (marked with *) are probably not necessary.  The others
should probably be added for completeness.

In addition, not all DBR types are supported.  In addition to the native
types, the DBR_TIME and DBR_CTRL variants are supported, but the DBR_STS
and DBR_GR variants are not.


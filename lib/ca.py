#!usr/bin/env python
#
# low level support for Epics Channel Access
#
""" EPICS Channel Access Interface

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
'XXX', as the intention is that importing this module with
    import ca
or
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
    context_create(context=0):
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

"""
import ctypes
import os
import gc
import sys
import time
import atexit

try:
    import numpy
    has_numpy = True
except:
    has_numpy = False

import dbr

## holder for DLL
libca = None

## PREEMPTIVE_CALLBACK determines the CA context
PREEMPTIVE_CALLBACK = True
# PREEMPTIVE_CALLBACK = False

AUTO_CLEANUP = True

## default timeout for connection
#   This should be kept fairly short --
#   as connection will be tried repeatedly
DEFAULT_CONNECTION_TIMEOUT = 5.0

## Cache of existing channel IDs:
#  pvname: {'chid':chid, 'conn': isConnected,
#           'ts': ts_conn, 'userfcn': user_callback)
#  isConnected   = True/False: if connected.
#  ts_conn       = ts of last connection event or failed attempt.
#  user_callback = user function to be called on change
_cache  = {}

## Cache of pvs waiting for put to be done.
_put_done =  {}
        
class ChannelAccessException(Exception):
    """Channel Access Exception"""
    def __init__(self, fcn, msg):
        self.fcn = fcn
        self.msg = msg
    def __str__(self):
        return " %s returned '%s'" % (self.fcn,self.msg)

def initialize_libca():
    """ load DLL (shared object library) to establish Channel Access
    Connection. The value of PREEMPTIVE_CALLBACK sets the pre-emptive
    callback model: 
        False   no preemptive callbacks. pend_io/pend_event must be used.
        True    preemptive callbaks will be done.
    Returns libca where 
        libca = ca library object, used for all subsequent ca calls

 Note that this function must be called prior to any real ca calls.
    """
    load_dll = ctypes.cdll.LoadLibrary
    dllname  = 'libca.so'
    path_sep = ':'
    if os.name == 'nt':
        load_dll = ctypes.windll.LoadLibrary
        dllname  = 'ca.dll'
        path_sep = ';'
        path_dirs = os.environ['PATH'].split(path_sep)
        for p in (sys.prefix,os.path.join(sys.prefix,'DLLs')):
            path_dirs.insert(0,p)
        os.environ['PATH'] = ';'.join(path_dirs)

    libca = load_dll(dllname)
    ca_context = {False:0, True:1}[PREEMPTIVE_CALLBACK]
    ret = libca.ca_context_create(ca_context)
    if ret != dbr.ECA_NORMAL:
        raise ChannelAccessException('initialize_libca',  'Cannot create Epics CA Context')

    if AUTO_CLEANUP: atexit.register(finalize_libca)
    return libca

def finalize_libca(maxtime=10.0,gc_collect=True):
    """shutdown channel access:
    run clear_channel(chid) for all chids in _cache
    then flush_io() and poll() a few times.
    """
    try:
        t0 = time.time()
        flush_io()
        poll()
        for key,val in _cache.items():
            clear_channel(val['chid'])
            _cache[key] = {}
        _cache.clear()

        for i in range(10):
            flush_io()
            poll()
            if time.time()-t0 > maxtime: break

        context_destroy()
        libca = None
    except:
        pass
    ## print 'shutdown in %.3fs' % (time.time()-t0)


def show_cache(print_out=True):
    """Show list of cached PVs"""
    o = []
    o.append('#  PV name    Is Connected?   Channel ID')
    o.append('#---------------------------------------')
    for name,val in _cache.items():
        o.append(" %s   %s     %s " % (name,
                                       repr(val['conn']),
                                       repr(val['chid'])))
    o = '\n'.join(o)
    if print_out:
        print o
    else:
        return o

## 3 decorator functions for ca functionality:
#    decorator name     ensures before running decorated function:
#    --------------     -----------------------------------------------
#    withCA               libca is initialized 
#    withCHID             (crudely) that the 1st arg is a chid (c_long)
#    withConnectedCHID    1st arg is a connected chid.
##

def withCA(fcn):
    """decorator to ensure that libca and a context are created
    prior to function calls to the channel access library. This is
    intended for functions that at the startup of CA, such as
        create_channel

    Note that CA functions that take a Channel ID (chid) as an
    argument are  NOT wrapped by this: to get a chid, the
    library must have been initialized already."""
    def wrapper(*args,**kw):
        global libca
        if libca is None:   libca = initialize_libca()
        return fcn(*args,**kw)
    return wrapper

def withCHID(fcn):
    """decorator to ensure that first argument to a function
    is a chid. This performs a very weak test, as any ctypes
    long or python int will pass.

    It may be worth making a chid class (which could hold connection
    data of _cache) that could be tested here.  For now, that
    seems slightly 'not low-level' for this module.
    """
    def wrapper(*args,**kw):
        if len(args)>0:
            if not isinstance(args[0],(ctypes.c_long,int)):
                raise ChannelAccessException(fcn.func_name, "not a valid chid!")
        return fcn(*args,**kw)
    return wrapper


def withConnectedCHID(fcn):
    """decorator to ensure that first argument to a function is a
    chid that is actually connected. This will attempt to connect
    if needed."""
    def wrapper(*args,**kw):
        if len(args)>0:
            if not isinstance(args[0],ctypes.c_long):
                raise ChannelAccessException(fcn.func_name, "not a valid chid!")
            try:
                mystate = state(args[0])
            except:
                mystate = None
            if mystate != dbr.CS_CONN:
                try:
                    t = kw.get('timeout',DEFAULT_CONNECTION_TIMEOUT)
                    connect_channel(args[0],timeout=t,force=False)
                    mystate = state(args[0])                    
                except:
                    mystate = None
            if mystate != dbr.CS_CONN:
                raise ChannelAccessException(fcn.func_name, "channel cannot connect")
        return fcn(*args,**kw)
    return wrapper

def PySEVCHK(func_name, status, expected=dbr.ECA_NORMAL):
    """raise a ChannelAccessException if the wrapped  status != ECA_NORMAL
    """
    if status == expected: return status
    raise ChannelAccessException(func_name,message(status))

def withSEVCHK(fcn):
    """decorator to raise a ChannelAccessException if the wrapped
    ca function does not return status=ECA_NORMAL
    """
    def wrapper(*args,**kw):
        status = fcn(*args,**kw)
        return PySEVCHK( fcn.func_name, status)
    return wrapper

###
#
# Now we're ready to wrap libca functions
#
###

# contexts
@withCA
@withSEVCHK
def context_create(context=0):
    return libca.ca_context_create(context)

@withCA
@withSEVCHK
def context_destroy():
    return libca.ca_context_destroy()
    
@withCA
def attach_context(context):
    ret = libca.ca_attach_context(context) 
    return PySEVCHK('attach_context',ret, dbr.ECA_ISATTACHED)
        
@withCA
def detach_context():
    return libca.ca_detach_context()

@withCA
def current_context():
    f = libca.ca_current_context
    f.restype = ctypes.c_void_p
    return f()

@withCA
def client_status(context,level):
    f = libca.ca_client_status
    f.argtypes = (ctypes.c_void_p,ctypes.c_long)
    return f(context,level)

@withCA
def flush_io():    return libca.ca_flush_io()

@withCA
def message(status):
    f = libca.ca_message
    f.restype = ctypes.c_char_p
    return f(status)

@withCA
@withSEVCHK
def pend_io(t=1.0):
    f   = libca.ca_pend_io
    f.argtypes = [ctypes.c_double]
    return f(t)

@withCA
def pend_event(t=1.e-5):
    f   = libca.ca_pend_event
    f.argtypes = [ctypes.c_double]
    ret = f(t)
    return PySEVCHK( 'pend_event', ret,  dbr.ECA_TIMEOUT)

@withCA
def poll(ev=1.e-4,io=1.0):
    """polls CA for events and i/o. """
    pend_event(ev)
    return pend_io(io)    

@withCA
def test_io():
    """test if IO is complete: returns True if it is"""
    return (dbr.ECA_IODONE ==  libca.ca_test_io())

## create channel

@withCA
def create_channel(pvname,connect=False,userfcn=None):
    """ create a Channel for a given pvname

    connect=True will try to wait until connection is complete
    before returning

    a user-supplied callback function (userfcn) can be provided
    as a connection callback. This function will be called when
    the connection state changes, and will be passed these keyword
    arguments:
       pvname   name of PV
       chid     channel ID
       conn     connection state (True/False)
    """
    chid = ctypes.c_long()

    # 
    # Note that _CB_connect (defined below) is a global variable, holding
    # a reference to _onConnectionEvent:  This is really the connection
    # callback that is run -- the userfcn here is stored in the _cache
    # and called by _onConnectionEvent.
    ret = libca.ca_create_channel(pvname,_CB_connect,0,0,ctypes.byref(chid))
    PySEVCHK('create_channel',ret)
    
    _cache[pvname] = {'chid':chid, 'conn':False, 'ts':0, 'failures':0,
                      'userfcn': userfcn}
    if connect: connect_channel(chid)
    return chid

@withCHID
def connect_channel(chid,timeout=None,verbose=False,force=True):
    """ wait (up to timeout) until a chid is connected

    Normally, channels will connect very fast, and the
    connection callback will succeed the first time.

    For un-connected Channels (that are nevertheless queried),
    the 'ts' (timestamp of last connecion attempt) and
    'failures' (number of failed connection attempts) from
    the _cache will be used to prevent spending too much time
    waiting for a connection that may never happen.
    
    """
    conn = (state(chid)==dbr.CS_CONN)
    if conn: return conn

    t0 = time.time()
    dt = t0 - _cache[name(chid)]['ts']
    # avoid repeatedly trying to connect to unavailable PV
    nfail = min(20,  1 + _cache[name(chid)]['failures'])
    if force: nfail = min(2,nfail)
    if dt < nfail * DEFAULT_CONNECTION_TIMEOUT: return conn

    if timeout is None: timeout=DEFAULT_CONNECTION_TIMEOUT
    while (not conn and (time.time()-t0 <= timeout)):
        poll()
        conn = (state(chid)==dbr.CS_CONN)
    if verbose:
        print 'connected in %.3f s' % ( time.time()-t0 )
    if not conn:
        _cache[name(chid)]['ts'] = time.time()
        _cache[name(chid)]['failures'] += 1
    return conn

# common functions with similar signatures
@withCHID
def _chid_f(chid,fcn_name,restype=int,arg=None):
    f = getattr(libca,fcn_name)
    if arg is not None:   f.argtypes = arg
    f.restype = restype
    return f(chid)

def name(chid):
    return _chid_f(chid,'ca_name',   restype=ctypes.c_char_p)

def host_name(chid):
    return _chid_f(chid,'ca_host_name',  restype=ctypes.c_char_p)

def element_count(chid):
    return _chid_f(chid,'ca_element_count')

def read_access(chid):
    return _chid_f(chid,'ca_read_access')

def write_access(chid):
    return _chid_f(chid,'ca_write_access')

def field_type(chid):
    return _chid_f(chid,'ca_field_type')

def clear_channel(chid):
    return _chid_f(chid,'ca_clear_channel')

@withCHID
def state(chid):         return libca.ca_state(chid)

@withCHID
def isConnected(chid):   return dbr.CS_CONN==state(chid)

@withCHID
def access(chid):
    acc = read_access(chid) + 2 * write_access(chid)
    return ('no access','read-only','write-only','read/write')[acc]

@withCHID
def promote_type(chid,use_time=False,use_ctrl=False,**kw):
    "promote native field type to TIME or CTRL variant"
    ftype = field_type(chid)
    if   use_ctrl: ftype += dbr.CTRL_STRING 
    elif use_time: ftype += dbr.TIME_STRING 
    if ftype == dbr.CTRL_STRING: ftype = dbr.TIME_STRING
    return ftype

def _unpack(data, count, ftype=dbr.INT,as_numpy=True):
    """unpack raw data returned from an array get or
    subscription callback"""

    ## TODO:  Can these be combined??
    def unpack_simple(data,ntype):
        if count == 1 and ntype != dbr.STRING:
            return data[0]
        out = [i for i in data]
        if ntype == dbr.STRING:
            out = ''.join(out).rstrip()
            if '\x00' in out:   out = out[:out.index('\x00')]
        return out

    def unpack_ctrltime(data,ntype):
        if count == 1 or ntype == dbr.STRING:
            out = data[0].value
            if ntype == dbr.STRING and '\x00' in out:
                out = out[:out.index('\x00')]
            return out
        out = [i.value for i in data]
        return out

    ntype = ftype
    unpack = unpack_simple
    if ftype >= dbr.TIME_STRING: unpack = unpack_ctrltime
    if ftype == dbr.CTRL_STRING: ftype = dbr.TIME_STRING

    if ftype > dbr.CTRL_STRING:    ntype -= dbr.CTRL_STRING
    elif ftype >= dbr.TIME_STRING: ntype -= dbr.TIME_STRING

    out = unpack(data,ntype)
    if has_numpy and as_numpy and count>1 and ntype !=dbr.STRING:
        out = numpy.array(out)
    return out

@withConnectedCHID
def get(chid,ftype=None,as_string=False, as_numpy=True):
    """return the current value for a Channel.  Options are
       ftype       field type to use (native type is default)
       as_string   flag(True/False) to get a string representation
                   of the value returned.  This is not nearly as
                   featured as for a PV -- see pv.py for more details.
       as_numpy    flag(True/False) to use numpy array as the
                   return type for array data.       
    
    """
    if ftype is None: ftype = field_type(chid)
    count = element_count(chid)

    nelem = count
    if ftype == dbr.STRING:  nelem = dbr.MAX_STRING_SIZE
       
    data = (nelem*dbr.Map[ftype])()
    
    ret = libca.ca_array_get(ftype, count, chid, data)
    PySEVCHK('get',ret)
    poll()
    val = _unpack(data,nelem,ftype=ftype,as_numpy=as_numpy)
    if as_string:
        val = __as_string(val,chid,count,ftype)
    return val

def __as_string(val,chid,count,ftype):
    "primitive conversion of value to a string"
    try:
        if ftype==dbr.CHAR:
            val = ''.join([chr(i) for i in val if i>0]).strip()
        elif ftype==dbr.ENUM and count==1:
            val = get_enum_strings(chid)[val]
        elif count > 1:
            val = '<array count=%d, type=%d>' % (count,ftype)
        val = str(val)
    except:
        pass            
    return val
                    
@withConnectedCHID
def put(chid,value, wait=False, timeout=20, callback=None,callback_data=None):
    """put value to a Channel, with optional wait and
    user-defined callback.  Arguments:
       chid      channel id (required)
       value     value to put to Channel (required)
       wait      Flag for whether to block here while put
                 is processing.  Default = False
       timeout   maximum time to wait for a blocking put.
       callback  user-defined to be called when put has
                 finished processing.
       callback_data  data passed on to user-defined callback

    Specifying a callback does NOT require a blocking put().  
    
    returns 1 on sucess and -1 on timed-out
    """
    ftype = field_type(chid)
    count = element_count(chid)
    data  = (count*dbr.Map[ftype])()    
    
    if ftype == dbr.STRING:
        data = (dbr.string_t)()
        count = 1
        data.value = value
    elif count == 1:
        try:
            data[0] = value
        except TypeError:
            data[0] = type(data[0])(value)
        except:
            errmsg = "Cannot put value '%s' to PV of type '%s'"
            raise ChannelAccessException('put',errmsg % (repr(value),
                                                         dbr.Name(ftype).lower()))
    else:
        # auto-convert strings to arrays for character waveforms
        # could consider using
        # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value,(str,unicode)):
            pad = '\x00'*(1+count-len(value))
            value = [ord(i) for i in ("%s%s" % (value,pad))[:count]]
        try:
            ndata = len(data)
            nuser = len(value)
            if nuser > ndata: value = value[:ndata]
            data[:len(value)] = list(value)
        except:
            errmsg = "Cannot put array data to PV of type '%s'"            
            raise ChannelAccessException('put',errmsg % (repr(value)))
      
    # simple put, without wait or callback
    if not (wait or callable(callback)):
        ret =  libca.ca_array_put(ftype,count,chid, data)
        PySEVCHK('put',ret)
        poll()
        return ret
    # wait with wait or callback    # wait with wait or callback
    pvname = name(chid)
    _put_done[pvname] = (False,callback,callback_data)

    ret = libca.ca_array_put_callback(ftype,count,chid,
                                      data, _CB_putwait, 0)
    PySEVCHK('put',ret)
    if wait:
        t0 = time.time()
        finished = False
        while not finished:
            poll()
            finished = _put_done[pvname][0] or (time.time()-t0)>timeout
        if not _put_done[pvname][0]: ret = -ret
    return ret

@withConnectedCHID
def get_ctrlvars(chid):
    """return the CTRL fields for a Channel.  Depending on 
    the native type, these fields may include
        status  precision  units  enum_strs
        upper_disp_limit     lower_disp_limit
        upper_alarm_limit    lower_alarm_limit
        upper_warning_limit  lower_warning_limit
        upper_ctrl_limit    lower_ctrl_limit
        
    note (difference with C lib): enum_strs will be a
    list of strings for the names of ENUM states.
    
    """
    ftype = promote_type(chid, use_ctrl=True)
    d = (1*dbr.Map[ftype])()
    ret = libca.ca_array_get(ftype, 1, chid, d)
    PySEVCHK('get_ctrlvars',ret)
    poll()
    kw = {}
    v = d[0]
    for attr in ('precision','units', 
                 'upper_disp_limit', 'lower_disp_limit',
                 'upper_alarm_limit', 'upper_warning_limit',
                 'lower_warning_limit','lower_alarm_limit',
                 'upper_ctrl_limit', 'lower_ctrl_limit'):
        if hasattr(v,attr):
            kw[attr] = getattr(v,attr)
    if hasattr(v,'strs') and hasattr(v,'no_str') and v.no_str > 0:
        kw['enum_strs'] = tuple([v.strs[i].value for i in range(v.no_str)])
    return kw

@withConnectedCHID
def get_timevars(chid):
    """return the TIME fields for a Channel.  Depending on 
    the native type, these fields may include
        status  severity timestamp
    """
    ftype = promote_type(chid, use_time=True)
    d = (1*dbr.Map[ftype])()
    ret = libca.ca_array_get(ftype, 1, chid, d)
    PySEVCHK('get_timevars',ret)
    poll()
    kw = {}
    v = d[0]
    for attr in ('status', 'severity', 'timestamp'):
        if hasattr(v,attr):
            kw[attr] = getattr(v,attr)
    return kw

def get_timestamp(chid):
    """return the timestamp of a Channel."""
    return get_timevars(chid).get('timestamp',0)

def get_severity(chid):
    """return the severity of a Channel."""
    return get_timevars(chid).get('severity',0)

def get_precision(chid):
    """return the precision of a Channel.  For Channels with
    native type other than FLOAT or DOUBLE, this will be 0"""
    if field_type(chid) in (dbr.FLOAT,dbr.DOUBLE):
        return get_ctrlvars(chid).get('precision',0)
    return 0

def get_enum_strings(chid):
    """return list of names for ENUM states of a Channel.  Returns
    None for non-ENUM Channels"""
    if field_type(chid) == dbr.ENUM:
        return get_ctrlvars(chid).get('enum_strs',None)
    return None

@withConnectedCHID
def create_subscription(chid, use_time=False,use_ctrl=False,
                        mask=7, userfcn=None):
    """setup a callback function to be called when a PVs value
    or state changes."""
    ftype = promote_type(chid, use_ctrl=use_ctrl,use_time=use_time)
    count = element_count(chid)

    cb     = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onGetEvent)   
    uarg  = ctypes.py_object(userfcn)
    evid  = ctypes.c_void_p()
    poll()
    ret = libca.ca_create_subscription(ftype, count, chid, mask,
                                       cb, uarg, ctypes.byref(evid))
    PySEVCHK('create_subscription',ret)
    
    poll()
    return (cb, uarg, evid)

@withCA
@withSEVCHK
def clear_subscription(evid): return libca.ca_clear_subscription(evid)

##
## Event Handlers for get() event callbacks
def _onGetEvent(args):
    """Internal Event Handler for get events: not intended for use"""
    value = dbr.Cast(args).contents
    kw = {'ftype':args.type,'count':args.count,
          'chid':args.chid, 'pvname': name(args.chid),
          'status':args.status}

    # add kw arguments for CTRL and TIME variants
    if args.type >= dbr.CTRL_STRING:
        v = value[0]
        for attr in dbr.ctrl_limits + ('precision','units'):
            if hasattr(v,attr):        
                kw[attr] = getattr(v,attr)
        if hasattr(v,'strs') and hasattr(v,'no_str') and v.no_str > 0:
            kw['enum_strs'] = tuple([v.strs[i].value for i in range(v.no_str)])

    elif args.type >= dbr.TIME_STRING:
        v = value[0]
        kw['status']    = v.status
        kw['severity']  = v.severity
        kw['timestamp'] = (dbr.EPICS2UNIX_EPOCH + v.stamp.secs + 
                           1.e-6*int(v.stamp.nsec/1000.00))

    nelem = args.count
    if args.type in (dbr.STRING,dbr.TIME_STRING,dbr.CTRL_STRING):
        nelem = dbr.MAX_STRING_SIZE

    value = _unpack(value, nelem, ftype=args.type)
    if callable(args.usr):
        args.usr(value=value, **kw)

## connection event handler: 
def _onConnectionEvent(args):
    """set flag in cache holding whteher channel is
    connected. if provided, run a user-function"""
    try:
        pvname = name(args.chid)
        entry  = _cache[pvname]
        entry['conn'] = (args.op == dbr.OP_CONN_UP)
        entry['ts']   = time.time()
        entry['failures'] = 0
        if callable(entry['userfcn']):
            entry['userfcn'](pvname=pvname,
                             chid=entry['chid'],
                             conn=entry['conn'])
    except:
        pass
    return 

## put event handler:
def _onPutEvent(args,*varargs):
    """set put-has-completed for this channel,
    call optional user-supplied callback"""
    pvname = name(args.chid)
    userfcn   = _put_done[pvname][1]
    userdata = _put_done[pvname][2]
    _put_done[pvname] = (True,None,None)
    if callable(userfcn): userfcn(pvname=pvname, data=userdata)

# create global reference to these two callbacks
_CB_connect = ctypes.CFUNCTYPE(None,dbr.ca_connection_args)(_onConnectionEvent)
_CB_putwait = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onPutEvent)   


## Synchronous groups
@withCA
@withSEVCHK
def sg_block(gid,t=10.0):
    f   = libca.ca_sg_block
    f.argtypes = [ctypes.c_ulong, ctypes.c_double]
    return f(gid,t)

@withCA
def sg_create():
    gid  = ctypes.c_ulong()
    pgid = ctypes.pointer(gid)
    ret =  libca.ca_sg_create(pgid)
    PySEVCHK('sg_create',ret)
    return gid

@withCA
@withSEVCHK
def sg_delete(gid):   return libca.ca_sg_delete(gid)

@withCA
def sg_test(gid):
    ret =libca.ca_sg_test(gid)
    return PySEVCHK('sg_test', ret, dbr.ECA_IODONE)

@withCA
@withSEVCHK
def sg_reset(gid):   return libca.ca_sg_reset(gid)

def sg_get(gid, chid, ftype=None,as_string=False,as_numpy=True):
    """synchronous-group get of the current value for a Channel.
    same options as get()
    """
    if not isinstance(chid,ctypes.c_long):
        raise ChannelAccessException('sg_get', "not a valid chid!")

    if ftype is None: ftype = field_type(chid)
    count = element_count(chid)

    nelem = count
    if ftype == dbr.STRING:  nelem = dbr.MAX_STRING_SIZE
    
    data = (nelem*dbr.Map[ftype])()
   
    ret = libca.ca_sg_array_get(gid, ftype, count, chid, data)
    PySEVCHK('sg_get',ret)

    poll()
    val = _unpack(data,nelem,ftype=ftype,as_numpy=as_numpy)
    if as_string:
        val = __as_string(val,chid,count,ftype)
    return val

def sg_put(gid, chid, value):
    """synchronous-group put: cannot wait or get callback!"""
    if not isinstance(chid,ctypes.c_long):
        raise ChannelAccessException('sg_put', "not a valid chid!")

    ftype = field_type(chid)
    count = element_count(chid)
    data  = (count*dbr.Map[ftype])()    
    if ftype == dbr.STRING:
        data = (dbr.string_t)()
        count = 1
        data.value = value
    elif count == 1:
        try:
            data[0] = value
        except TypeError:
            data[0] = type(data[0])(value)
        except:
            errmsg = "Cannot put value '%s' to PV of type '%s'"
            raise ChannelAccessException('put',errmsg % (repr(value),
                                                         dbr.Name(ftype).lower()))
    else:
        # auto-convert strings to arrays for character waveforms
        # could consider using
        # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value,(str,unicode)):
            pad = '\x00'*(1+count-len(value))
            value = [ord(i) for i in ("%s%s" % (value,pad))[:count]]
        try:
            ndata = len(data)
            nuser = len(value)
            if nuser > ndata: value = value[:ndata]
            data[:len(value)] = list(value)
        except:
            errmsg = "Cannot put array data to PV of type '%s'"            
            raise ChannelAccessException('put',errmsg % (repr(value)))
      
    ret =  libca.ca_sg_put(gid,ftype,count,chid, data)
    PySEVCHK('sg_put',ret)
    poll()
    return ret

##
## several methods are not (directly) implemented.
##
#
# def dump_dbr(type,count,data):  return libca.ca_dump_dbr(type,count, data)
# def add_exception_event(): return libca.ca_add_exception_event()
# def add_fd_registration(): return libca.ca_add_fd_registration()
# def replace_access_rights_event(): return libca.ca_replace_access_rights_event()
# def replace_printf_handler(): return libca.ca_replace_printf_handler()
#
# def puser(): return libca.ca_puser()
# def set_puser(): return libca.ca_set_puser()
# def test_event(): return libca.ca_test_event()
# 
# def SEVCHK(): raise NotImplementedError
# def signal(): return libca.ca_signal()


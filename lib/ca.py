#!usr/bin/python
#
# low level support for Epics Channel Access
#
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License
"""
EPICS Channel Access Interface

See doc/  for user documentation.

documentation here is developer documentation.
"""
import ctypes
import ctypes.util

import os
import sys
import time
from copy import copy
from  math import log10
import atexit
import warnings
from threading import Thread

# ignore warning about item size... for now??
warnings.filterwarnings('ignore',
                        'Item size computed from the PEP 3118*',
                        RuntimeWarning)

HAS_NUMPY = False
try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    pass

from . import dbr

PY_MAJOR, PY_MINOR = sys.version_info[:2]

memcopy = copy
if PY_MAJOR >= 3:
    from .utils3 import STR2BYTES, BYTES2STR, NULLCHAR, NULLCHAR_2, strjoin
else:
    from .utils2 import STR2BYTES, BYTES2STR, NULLCHAR, NULLCHAR_2, strjoin
    if PY_MINOR == 5:
        def memcopy(a):
            return a

## print to stdout
def write(msg, newline=True, flush=True):
    """write message to stdout"""
    sys.stdout.write(msg)
    if newline:
        sys.stdout.write("\n")
    if flush:
        sys.stdout.flush()

## holder for shared library
libca = None
initial_context = None

## PREEMPTIVE_CALLBACK determines the CA context
PREEMPTIVE_CALLBACK = True

AUTO_CLEANUP = True

##
# maximum element count for auto-monitoring of PVs in epics.pv
# and for automatic conversion of numerical array data to numpy arrays
AUTOMONITOR_MAXLENGTH = 65536 # 16384

## default timeout for connection
#   This should be kept fairly short --
#   as connection will be tried repeatedly
DEFAULT_CONNECTION_TIMEOUT = 2.0

## Cache of existing channel IDs:
#  pvname: {'chid':chid, 'conn': isConnected,
#           'ts': ts_conn, 'callbacks': [ user_callback... ])
#  isConnected   = True/False: if connected.
#  ts_conn       = ts of last connection event or failed attempt.
#  user_callback = one or more user functions to be called on
#                  change (accumulated in the cache)
_cache  = {}

## Cache of pvs waiting for put to be done.
_put_done =  {}

# get a unique python value that cannot be a value held by an
# actual PV to signal "Get is incomplete, awaiting callback"
class Empty:
    """used to create a unique python value that cannot be
    held as an actual PV value"""
    pass
GET_PENDING = Empty()

class ChannelAccessException(Exception):
    """Channel Access Exception: General Errors"""
    def __init__(self, *args):
        Exception.__init__(self, *args)
        sys.excepthook(*sys.exc_info())

class CASeverityException(Exception):
    """Channel Access Severity Check Exception:
    PySEVCHK got unexpected return value"""
    def __init__(self, fcn, msg):
        Exception.__init__(self)
        self.fcn = fcn
        self.msg = msg
    def __str__(self):
        return " %s returned '%s'" % (self.fcn, self.msg)

def find_libca():
    """
    find location of ca dynamic library
    """
    # Test 1: if PYEPICS_LIBCA env var is set, use it.
    dllpath = os.environ.get('PYEPICS_LIBCA', None)
    if (dllpath is not None and os.path.exists(dllpath) and
        os.path.isfile(dllpath)):
        return dllpath

    # Test 2: look through Python path and PATH env var for dll
    path_sep = ':'
    dylib   = 'lib'
    # For windows, we assume the DLLs are installed with the library
    if os.name == 'nt':
        path_sep = ';'
        dylib = 'DLLs'

    _path = [os.path.split(os.path.abspath(__file__))[0],
             os.path.split(os.path.dirname(os.__file__))[0],
             os.path.join(sys.prefix, dylib)]

    search_path = []
    for adir in (_path + sys.path +
                 os.environ.get('PATH','').split(path_sep) +
                 os.environ.get('LD_LIBRARY_PATH','').split(path_sep) +
                 os.environ.get('DYLD_LIBRARY_PATH','').split(path_sep)):
        if adir not in search_path and os.path.isdir(adir):
            search_path.append(adir)

    os.environ['PATH'] = path_sep.join(search_path)

    # with PATH set above, the ctypes utility, find_library *should*
    # find the dll....
    dllpath  = ctypes.util.find_library('ca')
    if dllpath is not None:
        return dllpath

    # Test 3: on unixes, look expliticly with EPICS_BASE env var and
    # known architectures for ca.so q
    if os.name == 'posix':
        known_hosts = {'Linux':   ('linux-x86', 'linux-x86_64') ,
                       'Darwin':  ('darwin-ppc', 'darwin-x86'),
                       'SunOS':   ('solaris-sparc', 'solaris-sparc-gnu') }

        libname = 'libca.so'
        if sys.platform == 'darwin':
            libname = 'libca.dylib'

        epics_base = os.environ.get('EPICS_BASE', '.')
        host_arch = os.uname()[0]
        if host_arch in known_hosts:
            epicspath = []
            for adir in known_hosts[host_arch]:
                epicspath.append(os.path.join(epics_base, 'lib', adir))
        for adir in search_path + epicspath:
            if os.path.exists(adir) and os.path.isdir(adir):
                if libname in os.listdir(adir):
                    return os.path.join(adir, libname)

    raise ChannelAccessException('cannot find Epics CA DLL')

def initialize_libca():
    """ load DLL (shared object library) to establish Channel Access
    Connection. The value of PREEMPTIVE_CALLBACK sets the pre-emptive
    callback model:
        False  no preemptive callbacks. pend_io/pend_event must be used.
        True   preemptive callbaks will be done.
    Returns libca where
        libca = ca library object, used for all subsequent ca calls

 Note that this function must be called prior to any real ca calls.
    """
    if 'EPICS_CA_MAX_ARRAY_BYTES' not in os.environ:
        os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = "%i" %  2**24

    dllname = find_libca()
    load_dll = ctypes.cdll.LoadLibrary
    global libca, initial_context
    if os.name == 'nt':
        load_dll = ctypes.windll.LoadLibrary
    try:
        libca = load_dll(dllname)
    except:
        raise ChannelAccessException('loading Epics CA DLL failed')

    ca_context = {False:0, True:1}[PREEMPTIVE_CALLBACK]
    ret = libca.ca_context_create(ca_context)
    if ret != dbr.ECA_NORMAL:
        raise ChannelAccessException('cannot create Epics CA Context')

    # set argtypes and non-default return types
    # for several libca functions here
    libca.ca_pend_event.argtypes  = [ctypes.c_double]
    libca.ca_pend_io.argtypes     = [ctypes.c_double]
    libca.ca_client_status.argtypes = [ctypes.c_void_p, ctypes.c_long]
    libca.ca_sg_block.argtypes    = [ctypes.c_ulong, ctypes.c_double]

    libca.ca_current_context.restype = ctypes.c_void_p
    libca.ca_version.restype   = ctypes.c_char_p
    libca.ca_host_name.restype = ctypes.c_char_p
    libca.ca_name.restype      = ctypes.c_char_p
    libca.ca_message.restype   = ctypes.c_char_p

    # save value offests used for unpacking
    # TIME and CTRL data as an array in dbr module
    dbr.value_offset = (39*ctypes.c_short).in_dll(libca,'dbr_value_offset')
    initial_context = current_context()

    if AUTO_CLEANUP:
        atexit.register(finalize_libca)
    return libca

def finalize_libca(maxtime=10.0):
    """shutdown channel access:
    run clear_channel(chid) for all chids in _cache
    then flush_io() and poll() a few times.
    """
    global libca
    global _cache
    if libca is None:
        return
    try:
        start_time = time.time()
        flush_io()
        poll()
        for ctx in _cache.values():
            for key in list(ctx.keys()):
                ctx.pop(key)
        _cache.clear()
        flush_count = 0
        while (flush_count < 5 and
               time.time()-start_time < maxtime):
            flush_io()
            poll()
            flush_count += 1
        context_destroy()
        libca = None
    except StandardError:
        pass

def get_cache(pvname):
    "return cache dictionary for a given pvname in the current context"
    return _cache[current_context()].get(pvname, None)

def show_cache(print_out=True):
    """Show list of cached PVs"""
    out = []
    out.append('#  PVName        ChannelID/Context Connected?')
    out.append('#--------------------------------------------')
    for context, context_chids in  list(_cache.items()):
        for vname, val in list(context_chids.items()):
            chid = val['chid']
            if len(vname) < 15:
                vname = (vname + ' '*15)[:15]
            out.append(" %s %s/%s  %s" % (vname, repr(chid),
                                          repr(context),
                                          isConnected(chid)))
    out = strjoin('\n', out)
    if print_out:
        write(out)
    else:
        return out

## decorator functions for ca functionality:
#  decorator name      ensures before running decorated function:
#  --------------      -----------------------------------------------
#   withCA               libca is initialized
#   withCHID             1st arg is a chid (dbr.chid_t)
#   withConnectedCHID    1st arg is a connected chid.
#   withInitialContext   Force the use of the initially defined context
#
#  These tests are not rigorous CA tests (and ctypes.long is
#  accepted as a chid, connect_channel() is tried, but may fail)
##
def withCA(fcn):
    """decorator to ensure that libca and a context are created
    prior to function calls to the channel access library. This is
    intended for functions that need CA started to work, such as
        create_channel

    Note that CA functions that take a Channel ID (chid) as an
    argument are  NOT wrapped by this: to get a chid, the
    library must have been initialized already."""
    def wrapper(*args, **kwds):
        "withCA wrapper"
        global libca
        if libca is None:
            initialize_libca()
        return fcn(*args, **kwds)
    wrapper.__doc__ = fcn.__doc__
    wrapper.__name__ = fcn.__name__
    wrapper.__dict__.update(fcn.__dict__)
    return wrapper

def withCHID(fcn):
    """decorator to ensure that first argument to a function
    is a chid. This performs a very weak test, as any ctypes
    long or python int will pass.

    It may be worth making a chid class (which could hold connection
    data of _cache) that could be tested here.  For now, that
    seems slightly 'not low-level' for this module.
    """
    def wrapper(*args, **kwds):
        "withCHID wrapper"
        if len(args)>0:
            chid = args[0]
            args = list(args)
            if isinstance(chid, int):
                args[0] = chid = dbr.chid_t(args[0])
            if not isinstance(chid, dbr.chid_t):
                msg = "%s: not a valid chid %s %s args %s kwargs %s!" % (
                    (fcn.__name__, chid, type(chid), args, kwds))
                raise ChannelAccessException(msg)

        return fcn(*args, **kwds)
    wrapper.__doc__ = fcn.__doc__
    wrapper.__name__ = fcn.__name__
    wrapper.__dict__.update(fcn.__dict__)
    return wrapper


def withConnectedCHID(fcn):
    """decorator to ensure that first argument to a function is a
    chid that is actually connected. This will attempt to connect
    if needed."""
    def wrapper(*args, **kwds):
        "withConnectedCHID wrapper"
        if len(args)>0:
            chid = args[0]
            args = list(args)
            if isinstance(chid, int):
                args[0] = chid = dbr.chid_t(chid)
            if not isinstance(chid, dbr.chid_t):
                raise ChannelAccessException("%s: not a valid chid!" % \
                                             (fcn.__name__))
            if not isConnected(chid):
                timeout = kwds.get('timeout', DEFAULT_CONNECTION_TIMEOUT)
                connect_channel(chid, timeout=timeout)
        return fcn(*args, **kwds)
    wrapper.__doc__ = fcn.__doc__
    wrapper.__name__ = fcn.__name__
    wrapper.__dict__.update(fcn.__dict__)
    return wrapper

def withInitialContext(fcn):
    """decorator to ensure that a function uses the initial
    threading context
    """
    def wrapper(*args, **kwds):
        "withInitialContext wrapper"
        use_initial_context()
        return fcn(*args, **kwds)
    wrapper.__doc__ = fcn.__doc__
    wrapper.__name__ = fcn.__name__
    wrapper.__dict__.update(fcn.__dict__)
    return wrapper

def PySEVCHK(func_name, status, expected=dbr.ECA_NORMAL):
    """raise a ChannelAccessException if the wrapped
    status != ECA_NORMAL
    """
    if status == expected:
        return status
    raise CASeverityException(func_name, message(status))

def withSEVCHK(fcn):
    """decorator to raise a ChannelAccessException if the wrapped
    ca function does not return status=ECA_NORMAL
    """
    def wrapper(*args, **kwds):
        "withSEVCHK wrapper"
        status = fcn(*args, **kwds)
        return PySEVCHK( fcn.__name__, status)
    wrapper.__doc__ = fcn.__doc__
    wrapper.__name__ = fcn.__name__
    wrapper.__dict__.update(fcn.__dict__)
    return wrapper

##
## Event Handler for monitor event callbacks
def _onMonitorEvent(args):
    """Event Handler for monitor events: not intended for use"""
    value = dbr.cast_args(args).contents
    pvname = name(args.chid)
    kwds = {'ftype':args.type, 'count':args.count,
           'chid':args.chid, 'pvname': pvname,
           'status':args.status}

    # add kwds arguments for CTRL and TIME variants
    if args.type >= dbr.CTRL_STRING:
        tmpv = value[0]
        for attr in dbr.ctrl_limits + ('precision', 'units', 'severity'):
            if hasattr(tmpv, attr):
                kwds[attr] = getattr(tmpv, attr)
        if (hasattr(tmpv, 'strs') and hasattr(tmpv, 'no_str') and
            tmpv.no_str > 0):
            kwds['enum_strs'] = tuple([tmpv.strs[i].value for
                                      i in range(tmpv.no_str)])

    elif args.type >= dbr.TIME_STRING:
        tmpv = value[0]
        kwds['status']    = tmpv.status
        kwds['severity']  = tmpv.severity
        kwds['timestamp'] = (dbr.EPICS2UNIX_EPOCH + tmpv.stamp.secs +
                            1.e-6*int(tmpv.stamp.nsec/1000.00))
    nelem = args.count
    if args.type in (dbr.STRING, dbr.TIME_STRING, dbr.CTRL_STRING):
        nelem = dbr.MAX_STRING_SIZE

    value = _unpack(args.chid, value, count=nelem, ftype=args.type)
    if hasattr(args.usr, '__call__'):
        args.usr(value=value, **kwds)

## connection event handler:
def _onConnectionEvent(args):
    """set flag in cache holding whteher channel is
    connected. if provided, run a user-function"""
    ctx = current_context()
    pvname = name(args.chid)
    global _cache

    if ctx is None and len(_cache.keys()) > 0:
        ctx = list(_cache.keys())[0]
    if ctx not in _cache:
        _cache[ctx] = {}

    # search for PV in any context...
    pv_found = False
    for context in _cache:
        if pvname in _cache[context]:
            pv_found = True
            break

    if not pv_found:
        _cache[ctx][pvname] = {'conn':False, 'chid': args.chid,
                               'ts':0, 'failures':0, 'value': None,
                               'callbacks': []}

    # set connection time, run connection callbacks
    # in all contexts
    for context, cvals in _cache.items():
        if pvname in cvals:
            entry = cvals[pvname]
            ichid = entry['chid']
            if isinstance(entry['chid'], dbr.chid_t):
                ichid = entry['chid'].value

            if int(ichid) == int(args.chid):
                conn = (args.op == dbr.OP_CONN_UP)
                chid = args.chid
                entry.update({'chid': chid, 'conn': conn,
                              'ts': time.time(), 'failures': 0})
                for callback in entry.get('callbacks', []):
                    poll()
                    if hasattr(callback, '__call__'):
                        callback(pvname=pvname, chid=chid, conn=conn)
    return

## get event handler:
def _onGetEvent(args, **kws):
    """get_callback event: simply store data contents which
    will need conversion to python data with _unpack()."""
    global _cache
    if args.status != dbr.ECA_NORMAL:
        return
    get_cache(name(args.chid))['value'] = memcopy(dbr.cast_args(args).contents)

## put event handler:
def _onPutEvent(args, **kwds):
    """set put-has-completed for this channel,
    call optional user-supplied callback"""
    pvname = name(args.chid)
    fcn  = _put_done[pvname][1]
    data = _put_done[pvname][2]
    _put_done[pvname] = (True, None, None)
    if hasattr(fcn, '__call__'):
        if isinstance(data, dict):
            kwds.update(data)
        elif data is not None:
            kwds['data'] = data
        fcn(pvname=pvname, **kwds)

# create global reference to these callbacks
_CB_CONNECT = ctypes.CFUNCTYPE(None, dbr.connection_args)(_onConnectionEvent)
_CB_PUTWAIT = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onPutEvent)
_CB_GET     = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onGetEvent)
_CB_EVENT   = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onMonitorEvent)

###
#
# Now we're ready to wrap libca functions
#
###

# contexts
@withCA
@withSEVCHK
def context_create(ctx=None):
    "create a context. if argument is None, use PREEMPTIVE_CALLBACK"
    if ctx is None:
        ctx = {False:0, True:1}[PREEMPTIVE_CALLBACK]
    return libca.ca_context_create(ctx)

def create_context(ctx):
    "create a context (fixed naming bug)"
    context_create(ctx=ctx)

@withCA
def context_destroy():
    "destroy current context"
    global _cache
    ctx = current_context()
    ret = libca.ca_context_destroy()
    if ctx in _cache:
        for key in list(_cache[ctx].keys()):
            _cache[ctx].pop(key)
        _cache.pop(ctx)
    return ret

def destroy_context():
    "destroy current context (fixed naming bug)"
    return context_destroy()

@withCA
@withSEVCHK
def attach_context(context):
    "attach a context"
    return libca.ca_attach_context(context)

@withCA
@withSEVCHK
def use_initial_context():
    "attach to the original context"
    global initial_context
    ret = dbr.ECA_NORMAL
    if initial_context != current_context():
        ret = libca.ca_attach_context(initial_context)
    return ret

@withCA
def detach_context():
    "detach a context"
    return libca.ca_detach_context()

@withCA
def replace_printf_handler(fcn=None):
    "replace printf output handler -- test???"
    if fcn is None:
        fcn = sys.stderr.write
    serr = ctypes.CFUNCTYPE(None, ctypes.c_char_p)(fcn)
    return libca.ca_replace_printf_handler(serr)

@withCA
def current_context():
    "return this context"
    ctx = libca.ca_current_context()
    try:
        ctx = int(ctx)
    except TypeError:
        pass
    return ctx

@withCA
def client_status(context, level):
    "return status of client"
    return libca.ca_client_status(context, level)

@withCA
def flush_io():
    "i/o flush"
    return libca.ca_flush_io()

@withCA
def message(status):
    "write message"
    return BYTES2STR(libca.ca_message(status))

@withCA
def version():
    """return CA version"""
    return BYTES2STR(libca.ca_version())

@withCA
def pend_io(timeout=1.0):
    """polls CA for i/o. """
    ret = libca.ca_pend_io(timeout)
    try:
        return PySEVCHK('pend_io', ret)
    except CASeverityException:
        return ret

## @withCA
def pend_event(timeout=1.e-5):
    """polls CA for events """
    ret = libca.ca_pend_event(timeout)
    try:
        return PySEVCHK( 'pend_event', ret,  dbr.ECA_TIMEOUT)
    except CASeverityException:
        return ret

@withCA
def poll(evt=1.e-5, iot=1.0):
    """polls CA for events and i/o. """
    pend_event(evt)
    return pend_io(iot)

@withCA
def test_io():
    """test if IO is complete: returns True if it is"""
    return (dbr.ECA_IODONE ==  libca.ca_test_io())

## create channel
@withCA
def create_channel(pvname, connect=False, auto_cb=True, callback=None):
    """ create a Channel for a given pvname

    connect:  try to wait until connection is complete before returning
    auto_cb:  use the automatic connection callback
    callback: a user-supplied callback function (callback) can be provided
       as a connection callback. This function will be called when the
       connection state changes, and will be passed these keyword args:
          pvname   name of PV
          chid     channel ID
          conn     connection state (True/False)

    If the channel is already connected for the PV name, the callback
    will be called immediately.
    """
    #
    # Note that _CB_CONNECT (defined above) is a global variable, holding
    # a reference to _onConnectionEvent:  This is really the connection
    # callback that is run -- the callack here is stored in the _cache
    # and called by _onConnectionEvent.
    pvn = STR2BYTES(pvname)
    ctx = current_context()
    global _cache
    if ctx not in _cache:
        _cache[ctx] = {}
    if pvname not in _cache[ctx]: # new PV for this context
        entry = {'conn':False,  'chid': None,
                 'ts': 0,  'failures':0, 'value': None,
                 'callbacks': [ callback ]}
        _cache[ctx][pvname] = entry
    else:
        entry = _cache[ctx][pvname]
        if not entry['conn'] and callback is not None: # pending connection
            _cache[ctx][pvname]['callbacks'].append(callback)
        elif (hasattr(callback, '__call__') and
              not callback in entry['callbacks']):
            entry['callbacks'].append(callback)
            callback(chid=entry['chid'], pvname=pvname, conn=entry['conn'])

    conncb = 0
    if auto_cb:
        conncb = _CB_CONNECT
    if entry.get('chid', None) is not None:
        # already have or waiting on a chid
        chid = _cache[ctx][pvname]['chid']
    else:
        chid = dbr.chid_t()
        ret = libca.ca_create_channel(pvn, conncb, 0, 0,
                                      ctypes.byref(chid))
        PySEVCHK('create_channel', ret)
        entry['chid'] = chid

    if connect:
        connect_channel(chid)
    if conncb != 0:
        poll()
    return chid

@withCHID
def connect_channel(chid, timeout=None, verbose=False):
    """ wait (up to timeout) until a chid is connected

    Normally, channels will connect very fast, and the
    connection callback will succeed the first time.

    For un-connected Channels (that are nevertheless queried),
    the 'ts' (timestamp of last connecion attempt) and
    'failures' (number of failed connection attempts) from
    the _cache will be used to prevent spending too much time
    waiting for a connection that may never happen.

    """
    if verbose:
        write(' connect channel -> %s %s %s ' %
               (repr(chid), repr(state(chid)), repr(dbr.CS_CONN)))
    conn = (state(chid) == dbr.CS_CONN)
    if not conn:
        # not connected yet, either indicating a slow network
        # or a truly un-connnectable channel.
        start_time = time.time()
        ctx = current_context()
        pvname = name(chid)
        global _cache
        if ctx not in _cache:
            _cache[ctx] = {}

        if timeout is None:
            timeout = DEFAULT_CONNECTION_TIMEOUT

        while (not conn and ((time.time()-start_time) < timeout)):
            poll()
            conn = (state(chid) == dbr.CS_CONN)
        if not conn:
            _cache[ctx][pvname]['ts'] = time.time()
            _cache[ctx][pvname]['failures'] += 1
    return conn

# functions with very light wrappings:
@withCHID
def name(chid):
    "channel name"
    return BYTES2STR(libca.ca_name(chid))

@withCHID
def host_name(chid):
    "channel host name"
    return BYTES2STR(libca.ca_host_name(chid))

@withCHID
def element_count(chid):
    "channel data size -- element count"
    return libca.ca_element_count(chid)

@withCHID
def read_access(chid):
    "read access for channel"
    return libca.ca_read_access(chid)

@withCHID
def write_access(chid):
    "write access for channel"
    return libca.ca_write_access(chid)

@withCHID
def field_type(chid):
    "integer giving data type for channel"
    return libca.ca_field_type(chid)

@withCHID
def clear_channel(chid):
    "clear channel"
    return libca.ca_clear_channel(chid)

@withCHID
def state(chid):
    "read attachment state for channel"
    return libca.ca_state(chid)

def isConnected(chid):
    "return whether channel is connected"
    return dbr.CS_CONN == state(chid)

def access(chid):
    "string description of access"
    acc = read_access(chid) + 2 * write_access(chid)
    return ('no access', 'read-only', 'write-only', 'read/write')[acc]

def promote_type(chid, use_time=False, use_ctrl=False):
    "promote native field type to TIME or CTRL variant"
    ftype = field_type(chid)
    if   use_ctrl:
        ftype += dbr.CTRL_STRING
    elif use_time:
        ftype += dbr.TIME_STRING
    if ftype == dbr.CTRL_STRING:
        ftype = dbr.TIME_STRING
    return ftype

def native_type(ftype):
    "return native field type from TIME or CTRL variant"
    if ftype == dbr.CTRL_STRING:
        ftype = dbr.TIME_STRING
    ntype = ftype
    if ftype > dbr.CTRL_STRING:
        ntype -= dbr.CTRL_STRING
    elif ftype >= dbr.TIME_STRING:
        ntype -= dbr.TIME_STRING
    return ntype

def _unpack(chid, data, count=None, ftype=None, as_numpy=True):
    """unpack raw data returned from an array get or
    subscription callback"""

    def array_cast(data, count, ntype, use_numpy):
        "cast ctypes array to numpy array (if using numpy)"
        if use_numpy:
            dtype = dbr.NP_Map.get(ntype, None)
            if dtype is not None:
                out = numpy.empty(shape=(count,), dtype=dbr.NP_Map[ntype])
                ctypes.memmove(out.ctypes.data, data, out.nbytes)
            else:
                out = numpy.ctypeslib.as_array(copy(data))
        else:
            out = copy(data)
        return out

    def unpack_simple(data, count, ntype, use_numpy):
        "simple, native data type"
        if count == 1 and ntype != dbr.STRING:
            return data[0]
        if ntype == dbr.STRING:
            out = []
            for elem in range(min(count, len(data))):
                this = strjoin('', data[elem]).rstrip()
                if NULLCHAR_2 in this:
                    this = this[:this.index(NULLCHAR_2)]
                out.append(this)
            if len(out) == 1:
                out = out[0]
            return out
        if count > 1:
            data = array_cast(data, count, ntype, use_numpy)
        return data

    def unpack_ctrltime(data, count, ntype, use_numpy):
        "ctrl and time data types"
        if count == 1 or ntype == dbr.STRING:
            data = data[0].value
            if ntype == dbr.STRING and NULLCHAR in data:
                data = data[:data.index(NULLCHAR)]
            return data
        # fix for CTRL / TIME array data:Thanks to Glen Wright !
        data = (count*dbr.Map[ntype]).from_address(ctypes.addressof(data) +
                                                  dbr.value_offset[ftype])
        if count > 1:
            data = array_cast(data, count, ntype, use_numpy)
        return data

    unpack = unpack_simple
    if ftype >= dbr.TIME_STRING:
        unpack = unpack_ctrltime

    if count is None and chid is not None:
        count = element_count(chid)
    if count is None:
        count = 1

    if ftype is None and chid is not None:
        ftype = field_type(chid)
    if ftype is None:
        ftype = dbr.INT
    ntype = native_type(ftype)
    use_numpy = (HAS_NUMPY and as_numpy and ntype != dbr.STRING and count > 1)
    return unpack(data, count, ntype, use_numpy)

@withConnectedCHID
def get(chid, ftype=None, count=None, wait=True, timeout=None,
        as_string=False, as_numpy=True):
    """return the current value for a Channel.  Options are
       ftype       field type to use (native type is default)
       count       explicitly limit count
       wait        flag(True/False) to wait to return value (default) or
                   return None immediately, with value to be fetched later
                   by ca.get_complete(chid, ...)
       timeout     time to wait (and sent to pend_io()) before unpacking
                   value (default =  0.5 + log10(count) )
       as_string   flag(True/False) to get a string representation
                   of the value returned.  This is not nearly as
                   featured as for a PV -- see pv.py for more details.
       as_numpy    flag(True/False) to use numpy array as the
                   return type for array data.

       get will return None under one of the following conditions:
         * Channel not connected
         * wait=False passed in
         * data is not available within timeout.
    """
    if ftype is None:
        ftype = field_type(chid)
    if ftype in (None, -1):
        return None
    if count is None:
        count = element_count(chid)
    else:
        count = min(count, element_count(chid))

    ncache = _cache[current_context()][name(chid)]
    # implementation note: cached value of
    #   None        implies no value, no expected callback
    #   GET_PENDING implies no value yet, callback expected.
    ncache['value'] = GET_PENDING

    uarg = ctypes.py_object(ctypes.POINTER(dbr.Map[ftype]))
    ret = libca.ca_array_get_callback(ftype, count, chid, _CB_GET, uarg)

    PySEVCHK('get', ret)
    if not wait:
        return None
    return get_complete(chid, count=count, ftype=ftype, timeout=timeout,
                        as_string=as_string, as_numpy=as_numpy)

@withConnectedCHID
def get_complete(chid, ftype=None, count=None, timeout=None,
                 as_string=False,  as_numpy=True):

    """returns the value for a channel, completing a previous 'inomplete get' on
    the channel. This assumes that the previous call to get(chid, ....)  either
    used 'wait=False' or timed out, and that the data has actually arrived by the
    time this function is called.

    Important Note: this function can be called only once, as on success, the
    cached value will be set back to None.

    Options are as for get (but without unpack, which is always True here):

       ftype       field type to use (native type is default)
       count       explicitly limit count
       as_string   flag(True/False) to get a string representation
                   of the value returned.  This is not nearly as
                   featured as for a PV -- see pv.py for more details.
       as_numpy    flag(True/False) to use numpy array as the
                   return type for array data.
       timeout     time to wait for value to be received
                   (default = 0.5 + log10(count) seconds)
   """
    if ftype is None:
        ftype = field_type(chid)
    if count is None:
        count = element_count(chid)
    else:
        count = min(count, element_count(chid))

    ncache = _cache[current_context()][name(chid)]
    if ncache['value'] is None:
        return None

    t0 = time.time()
    if timeout is None:
        timeout = 1.0 + log10(max(1, count))
    while ncache['value'] is GET_PENDING:
        pend_event(1.e-5)
        if time.time()-t0 > timeout:
            msg = "ca.get('%s') timed out after %.2f seconds."
            warnings.warn(msg % (name(chid), timeout))
            return None

    val = _unpack(chid, ncache['value'], count=count,
                  ftype=ftype, as_numpy=as_numpy)
    if as_string:
        val = _as_string(val, chid, count, ftype)
    elif isinstance(val, ctypes.Array) and HAS_NUMPY and as_numpy:
        val = numpy.array(val)

    # value retrieved, clear cached value
    ncache['value'] = None
    return val

def _as_string(val, chid, count, ftype):
    "primitive conversion of value to a string"
    try:
        if (ftype in (dbr.CHAR, dbr.TIME_CHAR, dbr.CTRL_CHAR) and
            count < AUTOMONITOR_MAXLENGTH):
            val = strjoin('',   [chr(i) for i in val if i>0]).strip()
        elif ftype == dbr.ENUM and count == 1:
            val = get_enum_strings(chid)[val]
        elif count > 1:
            val = '<array count=%d, type=%d>' % (count, ftype)
        val = str(val)
    except ValueError:
        pass
    return val

@withConnectedCHID
def put(chid, value, wait=False, timeout=30, callback=None,
        callback_data=None):
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
    if count > 1: #  and not (ftype == dbr.CHAR and isinstance(value, str)):
        count = min(len(value), count)
    data  = (count*dbr.Map[ftype])()

    if ftype == dbr.STRING:
        if count == 1:
            data[0].value = value
        else:
            for elem in range(min(count, len(value))):
                data[elem].value = value[elem]
    elif count == 1:
        try:
            data[0] = value
        except TypeError:
            data[0] = type(data[0])(value)
        except:
            errmsg = "cannot put value '%s' to PV of type '%s'"
            tname  = dbr.Name(ftype).lower()
            raise ChannelAccessException(errmsg % (repr(value), tname))

    else:
        if ftype == dbr.CHAR and isinstance(value, str):
            value = [ord(i) for i in ("%s%s" % (value, NULLCHAR))]
        try:
            ndata, nuser = len(data), len(value)
            if nuser > ndata:
                value = value[:ndata]
            data[:len(value)] = list(value)
        except (ValueError, IndexError):
            errmsg = "cannot put array data to PV of type '%s'"
            raise ChannelAccessException(errmsg % (repr(value)))

    # simple put, without wait or callback
    if not (wait or hasattr(callback, '__call__')):
        ret =  libca.ca_array_put(ftype, count, chid, data)
        PySEVCHK('put', ret)
        poll()
        return ret
    # wait with callback (or put_complete)
    pvname = name(chid)
    _put_done[pvname] = (False, callback, callback_data)
    start_time = time.time()
    # print "Put:  ", ftype, count
    ret = libca.ca_array_put_callback(ftype, count, chid,
                                      data, _CB_PUTWAIT, 0)
    PySEVCHK('put', ret)
    poll(evt=1.e-4, iot=0.05)
    if wait:
        while not (_put_done[pvname][0] or
                   (time.time()-start_time) > timeout):
            poll()
        if not _put_done[pvname][0]:
            ret = -ret
    return ret

@withConnectedCHID
def get_ctrlvars(chid):
    """return the CTRL fields for a Channel.  Depending on
    the native type, these fields may include
        status  severity precision  units  enum_strs
        upper_disp_limit     lower_disp_limit
        upper_alarm_limit    lower_alarm_limit
        upper_warning_limit  lower_warning_limit
        upper_ctrl_limit    lower_ctrl_limit

    note (difference with C lib): enum_strs will be a
    list of strings for the names of ENUM states.

    """
    ftype = promote_type(chid, use_ctrl=True)
    dat = (1*dbr.Map[ftype])()

    ret = libca.ca_array_get(ftype, 1, chid, dat)
    PySEVCHK('get_ctrlvars', ret)
    poll()
    out = {}
    tmpv = dat[0]
    for attr in ('precision', 'units', 'severity', 'status',
                 'upper_disp_limit', 'lower_disp_limit',
                 'upper_alarm_limit', 'upper_warning_limit',
                 'lower_warning_limit','lower_alarm_limit',
                 'upper_ctrl_limit', 'lower_ctrl_limit'):
        if hasattr(tmpv, attr):
            out[attr] = getattr(tmpv, attr, None)
    if (hasattr(tmpv, 'strs') and hasattr(tmpv, 'no_str') and
        tmpv.no_str > 0):
        out['enum_strs'] = tuple([BYTES2STR(tmpv.strs[i].value)
                                  for i in range(tmpv.no_str)])
    return out

@withConnectedCHID
def get_timevars(chid):
    """return the TIME fields for a Channel.  Depending on
    the native type, these fields may include
        status  severity timestamp
    """
    ftype = promote_type(chid, use_time=True)
    dat = (1*dbr.Map[ftype])()

    ret = libca.ca_array_get(ftype, 1, chid, dat)
    PySEVCHK('get_timevars', ret)
    poll()
    out = {}
    val = dat[0]
    for attr in ('status', 'severity', 'timestamp'):
        if hasattr(val, attr):
            out[attr] = getattr(val, attr)
    return out

def get_timestamp(chid):
    """return the timestamp of a Channel."""
    return get_timevars(chid).get('timestamp', 0)

def get_severity(chid):
    """return the severity of a Channel."""
    return get_timevars(chid).get('severity', 0)

def get_precision(chid):
    """return the precision of a Channel.  For Channels with
    native type other than FLOAT or DOUBLE, this will be 0"""
    if field_type(chid) in (dbr.FLOAT, dbr.DOUBLE):
        return get_ctrlvars(chid).get('precision', 0)
    return 0

def get_enum_strings(chid):
    """return list of names for ENUM states of a Channel.  Returns
    None for non-ENUM Channels"""
    if field_type(chid) == dbr.ENUM:
        return get_ctrlvars(chid).get('enum_strs', None)
    return None

##
# Default mask for subscriptions (means update on value changes
# exceeding MDEL, and on alarm level changes.) Other option is
# dbr.DBE_LOG for archive changes (ie exceeding ADEL)
DEFAULT_SUBSCRIPTION_MASK = dbr.DBE_VALUE|dbr.DBE_ALARM

@withConnectedCHID
def create_subscription(chid, use_time=False, use_ctrl=False,
                        mask=None, callback=None):
    """
    setup a callback function to be called when a PVs value or state changes.

    mask is some combination of dbr.DBE_VALUE, dbr.DBE_ALARM, or default as set above.

    Important Note:
        KEEP The returned tuple in named variable: if the return argument
        gets garbage collected, a coredump will occur.

    """
    mask = mask or DEFAULT_SUBSCRIPTION_MASK

    ftype = promote_type(chid, use_ctrl=use_ctrl, use_time=use_time)

    uarg  = ctypes.py_object(callback)
    evid  = ctypes.c_void_p()
    poll()
    ret = libca.ca_create_subscription(ftype, 0, chid, mask,
                                       _CB_EVENT, uarg, ctypes.byref(evid))
    PySEVCHK('create_subscription', ret)

    poll()
    return (_CB_EVENT, uarg, evid)

@withCA
@withSEVCHK
def clear_subscription(evid):
    "cancel subscription"
    return libca.ca_clear_subscription(evid)


@withCA
@withSEVCHK
def sg_block(gid, timeout=10.0):
    "sg block"
    return libca.ca_sg_block(gid, timeout)

@withCA
def sg_create():
    "sg create"
    gid  = ctypes.c_ulong()
    pgid = ctypes.pointer(gid)
    ret =  libca.ca_sg_create(pgid)
    PySEVCHK('sg_create', ret)
    return gid

@withCA
@withSEVCHK
def sg_delete(gid):
    "sg delete"
    return libca.ca_sg_delete(gid)

@withCA
def sg_test(gid):
    "sg test"
    ret = libca.ca_sg_test(gid)
    return PySEVCHK('sg_test', ret, dbr.ECA_IODONE)

@withCA
@withSEVCHK
def sg_reset(gid):
    "sg reset"
    return libca.ca_sg_reset(gid)

def sg_get(gid, chid, ftype=None, as_numpy=True, as_string=True):
    """synchronous-group get of the current value for a Channel.
    same options as get()

    Note that the returned tuple from a sg_get() will have to be
    unpacked with the '_unpack' method:

    >>> chid = epics.ca.create_channel(PV_Name)
    >>> epics.ca.connect_channel(chid1)
    >>> sg = epics.ca.sg_create()
    >>> data = epics.ca.sg_get(sg, chid)
    >>> epics.ca.sg_block(sg)
    >>> print epics.ca._unpack(data, chid=chid)
    """
    if not isinstance(chid, dbr.chid_t):
        raise ChannelAccessException("not a valid chid!")

    if ftype is None:
        ftype = field_type(chid)
    count = element_count(chid)

    data = (count*dbr.Map[ftype])()
    ret = libca.ca_sg_array_get(gid, ftype, count, chid, data)
    PySEVCHK('sg_get', ret)
    poll()

    val = _unpack(chid, data, count=count, ftype=ftype, as_numpy=as_numpy)
    if as_string:
        val = _as_string(val, chid, count, ftype)
    return val

def sg_put(gid, chid, value):
    "synchronous-group put: cannot wait or get callback!"
    if not isinstance(chid, dbr.chid_t):
        raise ChannelAccessException("not a valid chid!")

    ftype = field_type(chid)
    count = element_count(chid)
    data  = (count*dbr.Map[ftype])()

    if ftype == dbr.STRING:
        if count == 1:
            data[0].value = value
        else:
            for elem in range(min(count, len(value))):
                data[elem].value = value[elem]
    elif count == 1:
        try:
            data[0] = value
        except TypeError:
            data[0] = type(data[0])(value)
        except:
            errmsg = "Cannot put value '%s' to PV of type '%s'"
            tname   = dbr.Name(ftype).lower()
            raise ChannelAccessException(errmsg % (repr(value), tname))

    else:
        # auto-convert strings to arrays for character waveforms
        # could consider using
        # numpy.fromstring(("%s%s" % (s,NULLCHAR*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value, str):
            pad = NULLCHAR*(1+count-len(value))
            value = [ord(i) for i in ("%s%s" % (value, pad))[:count]]
        try:
            ndata = len(data)
            nuser = len(value)
            if nuser > ndata:
                value = value[:ndata]
            data[:len(value)] = list(value)
        except:
            errmsg = "Cannot put array data to PV of type '%s'"
            raise ChannelAccessException(errmsg % (repr(value)))

    ret =  libca.ca_sg_array_put(gid, ftype, count, chid, data)
    PySEVCHK('sg_put', ret)
    # poll()
    return ret

class CAThread(Thread):
    """
    Sub-class of threading.Thread to ensure that the
    initial CA context is used.
    """
    def run(self):
        use_initial_context()
        Thread.run(self)

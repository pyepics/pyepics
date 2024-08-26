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
from typing import Callable, Dict

import ctypes
from ctypes.util import find_library

import atexit
import functools
import os
import sys
import threading
import time
import warnings
from copy import deepcopy
from collections import defaultdict
from math import log10

try: # importlib.resources does not yet have files on python 3.8
    from importlib.resources import files as importlib_resources_files
except ImportError:
    from importlib_resources import files as importlib_resources_files

HAS_NUMPY = False
try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    pass

from .utils import (str2bytes, bytes2str, strjoin, IOENCODING,
                    clib_search_path)
from . import dbr


# ignore warning about item size...
warnings.filterwarnings('ignore', 'Item size computed from the PEP 3118*',
                        RuntimeWarning)


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
ca_printf = ''

## PREEMPTIVE_CALLBACK determines the CA context
PREEMPTIVE_CALLBACK = True

AUTO_CLEANUP = True

# set this to control whether messages from CA
# (about caRepeater or lost connections) are disabled at startup
WITH_CA_MESSAGES = False

# A sentinel to mark libca as going through the shutdown process
_LIBCA_FINALIZED = object()

##
# maximum element count for auto-monitoring of PVs in epics.pv
# and for automatic conversion of numerical array data to numpy arrays
AUTOMONITOR_MAXLENGTH = 65536 # 16384

## default timeout for connection
#   This should be kept fairly short --
#   as connection will be tried repeatedly
DEFAULT_CONNECTION_TIMEOUT = 2.0

## Cache of existing channel IDs:
# Keyed on context, then on pv name (e.g., _cache[ctx][pvname])
_cache = defaultdict(dict)
_chid_cache = {}

# Puts with completion in progress:
_put_completes = []

# logging.basicConfig(filename='ca.log',level=logging.DEBUG)

class _GetPending:
    """
    A unique python object that cannot be a value held by an actual PV to
    signal "Get is incomplete, awaiting callback"
    """
    def __repr__(self):
        return 'GET_PENDING'


Empty = _GetPending  # back-compat
GET_PENDING = _GetPending()


class _SentinelWithLock:
    """
    Used in create_channel, this sentinel ensures that two threads in the same
    CA context do not conflict if they call `create_channel` with the same
    pvname at the exact same time.
    """
    def __init__(self):
        self.lock = threading.Lock()


class ChannelAccessException(Exception):
    """Channel Access Exception: General Errors"""
    def __init__(self, *args):
        Exception.__init__(self, *args)
        type_, value, traceback = sys.exc_info()
        if type_ is not None:
            sys.excepthook(type_, value, traceback)

class ChannelAccessGetFailure(Exception):
    """Channel Access Exception: _onGetEvent != ECA_NORMAL"""
    def __init__(self, message, chid, status):
        super(ChannelAccessGetFailure, self).__init__(message)
        self.chid = chid
        self.status = status


class CASeverityException(Exception):
    """Channel Access Severity Check Exception:
    PySEVCHK got unexpected return value"""
    def __init__(self, fcn, msg):
        Exception.__init__(self)
        self.fcn = fcn
        self.msg = msg
    def __str__(self):
        return " %s returned '%s'" % (self.fcn, self.msg)


class _CacheItem:
    '''
    The cache state for a single chid in a context.

    This class itself is not thread-safe; it is expected that callers will use
    the lock appropriately when modifying the state.

    Attributes
    ----------
    lock : threading.RLock
        A lock for modifying the state
    conn : bool
        The connection status
    context : int
        The context in which this is CacheItem was created in
    chid : ctypes.c_long
        The channel ID
    pvname : str
        The PV name
    ts : float
        The connection timestamp (or last failed attempt)
    failures : int
        Number of failed connection attempts
    get_results : dict
        Keyed on the requested field type -> requested value
    callbacks : list
        One or more user functions to be called on change of connection status
    access_event_callbacks : list
        One or more user functions to be called on change of access rights
    '''

    def __init__(self, chid, pvname, callbacks=None, ts=0):
        self._chid = None
        self.context = current_context()
        self.lock = threading.RLock()
        self.conn = False
        self.pvname = pvname
        self.ts = ts
        self.failures = 0

        self.get_results = defaultdict(lambda: [None])

        if callbacks is None:
            callbacks = []

        self.callbacks = callbacks
        self.access_event_callback = []
        self.chid = chid

    @property
    def chid(self):
        return self._chid

    @chid.setter
    def chid(self, chid):
        if chid is not None and not isinstance(chid, dbr.chid_t):
            chid = dbr.chid_t(chid)

        self._chid = chid

    def __repr__(self):
        return (
            '<{} {!r} {} failures={} callbacks={} access_callbacks={} chid={}>'
            ''.format(self.__class__.__name__,
                      self.pvname,
                      'connected' if self.conn else 'disconnected',
                      self.failures,
                      len(self.callbacks),
                      len(self.access_event_callback),
                      self.chid_int,
                      )
        )

    def __getitem__(self, key):
        # back-compat
        return getattr(self, key)

    @property
    def chid_int(self):
        'The channel id, as an integer'
        return _chid_to_int(self.chid)

    def run_access_event_callbacks(self, ra, wa):
        '''
        Run all access event callbacks

        Parameters
        ----------
        ra : bool
            Read-access
        wa : bool
            Write-access
        '''
        for callback in list(self.access_event_callback):
            if callable(callback):
                callback(ra, wa)

    def run_connection_callbacks(self, conn, timestamp):
        '''
        Run all connection callbacks

        Parameters
        ----------
        conn : bool
            Connected (True) or disconnected
        timestamp : float
            The event timestamp
        '''
        # Lock here, as create_channel may be setting the chid
        with self.lock:
            self.conn = conn
            self.ts = timestamp
            self.failures = 0

        chid_int = self.chid_int
        for callback in list(self.callbacks):
            if callable(callback):
                # The following sleep is here only to allow other threads the
                # opportunity to grab the Python GIL. (see pyepics/pyepics#171)
                time.sleep(0)

                # print( ' ==> connection callback ', callback, conn)
                callback(pvname=self.pvname, chid=chid_int, conn=self.conn)


def find_lib(inp_lib_name='ca'):
    """
    find location of ca dynamic library
    """
    # Test 1: if PYEPICS_LIBCA env var is set, use it.
    dllpath = os.environ.get('PYEPICS_LIBCA', None)

    # find libCom.so *next to* libca.so if PYEPICS_LIBCA was set
    if dllpath is not None and inp_lib_name != 'ca':
        _parent, _name = os.path.split(dllpath)
        dllpath = os.path.join(_parent, _name.replace('ca', inp_lib_name))

    if (dllpath is not None and os.path.exists(dllpath) and
            os.path.isfile(dllpath)):
        return dllpath

    # Test 2: look in installed python location for dll
    dllpath = importlib_resources_files('epics.clibs') / clib_search_path(inp_lib_name)

    if (os.path.exists(dllpath) and os.path.isfile(dllpath)):
        return dllpath

    # Test 3: look through Python path and PATH env var for dll
    path_sep = ':'
    dylib = 'lib'
    # For windows, we assume the DLLs are installed with the library
    if os.name == 'nt':
        path_sep = ';'
        dylib = 'DLLs'

    basepath = os.path.split(os.path.abspath(__file__))[0]
    parent   = os.path.split(basepath)[0]
    _path = [basepath, parent,
             os.path.join(parent, dylib),
             os.path.split(os.path.dirname(os.__file__))[0],
             os.path.join(sys.prefix, dylib)]

    def envpath2list(envname, path_sep):
        plist = ['']
        try:
            plist = os.environ.get(envname, '').split(path_sep)
        except AttributeError:
            pass
        return plist

    env_path = envpath2list('PATH', path_sep)
    ldname = 'LD_LIBRARY_PATH'
    if sys.platform == 'darwin':
        ldname = 'DYLD_LIBRARY_PATH'
    env_ldpath = envpath2list(ldname, path_sep)

    search_path = []
    for adir in (_path + env_path + env_ldpath):
        if adir not in search_path and os.path.isdir(adir):
            search_path.append(adir)

    os.environ['PATH'] = path_sep.join(search_path)
    # with PATH set above, the ctypes utility, find_library *should*
    # find the dll....
    dllpath = find_library(inp_lib_name)
    if dllpath is not None:
        return dllpath

    raise ChannelAccessException('cannot find Epics CA DLL')


def find_libca():
    return str(find_lib('ca'))

def find_libCom():
    libname = 'Com' if os.name == 'nt' else 'ComPYEPICS'
    return str(find_lib(libname))

def initialize_libca():
    """Initialize the Channel Access library.

    This loads the shared object library (DLL) to establish Channel Access
    Connection. The value of :data:`PREEMPTIVE_CALLBACK` sets the pre-emptive
    callback model.

   This **must** be called prior to any actual use of the CA library, but
    will be called automatically by the the :func:`withCA` decorator, so
    you should not need to call this directly from most real programs.

    Returns
    -------
    libca : object
        ca library object, used for all subsequent ca calls

    Notes
    -----
    1. This function must be called prior to any real CA calls.
    2. This function will disable messages from CA.

    See the `withCA`  decorator to ensure CA is initialized
    """
    if 'EPICS_CA_MAX_ARRAY_BYTES' not in os.environ:
        os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = "%d" %  2**24

    global libca, initial_context

    if os.name == 'nt':
        load_dll = ctypes.windll.LoadLibrary
    else:
        load_dll = ctypes.cdll.LoadLibrary
    try:
        # force loading the chosen version of libCom
        if os.name == 'nt':
            load_dll(find_libCom())
        libca = load_dll(find_libca())
    except Exception as exc:
        raise ChannelAccessException('loading Epics CA DLL failed: ' + str(exc))

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
    # libca.ca_name.argstypes    = [dbr.chid_t]
    # libca.ca_state.argstypes   = [dbr.chid_t]
    libca.ca_message.restype   = ctypes.c_char_p
    libca.ca_attach_context.argtypes = [ctypes.c_void_p]

    # save value offests used for unpacking
    # TIME and CTRL data as an array in dbr module
    dbr.value_offset = (39*ctypes.c_short).in_dll(libca,'dbr_value_offset')

    initial_context = current_context()

    if not WITH_CA_MESSAGES:
        disable_ca_messages()

    if AUTO_CLEANUP:
        atexit.register(finalize_libca)
    return libca

def finalize_libca(maxtime=10.0):
    """shutdown channel access:

    run :func:`clear_channel` for all chids in :data:`_cache`,
    then calls :func:`flush_io` and :func:`poll` a few times.

    Parameters
    ----------
    maxtime : float
        maximimum time (in seconds) to wait for :func:`flush_io` and :func:`poll` to complete.

    """
    global libca
    if libca is None or libca is _LIBCA_FINALIZED:
        return
    try:
        start_time = time.time()
        flush_io()
        poll()
        for chid, entry in list(_chid_cache.items()):
            try:
                clear_channel(chid)
            except ChannelAccessException:
                pass

        _chid_cache.clear()
        _cache.clear()

        flush_count = 0
        while (flush_count < 5 and
               time.time()-start_time < maxtime):
            flush_io()
            poll()
            flush_count += 1
        context_destroy()
        libca = _LIBCA_FINALIZED
    except Exception:
        pass
    time.sleep(0.01)


def get_cache(pvname):
    "return _CacheItem for a given pvname in the current context"
    return _cache[current_context()].get(pvname, None)


def _get_cache_by_chid(chid):
    'return _CacheItem for a given channel id'
    try:
        return _chid_cache[chid]
    except KeyError:
        # It's possible that the channel id cache is not yet ready; check the
        # context cache before giving up. This branch should not happen often.
        context = current_context()
        if context is not None:
            pvname = bytes2str(libca.ca_name(dbr.chid_t(chid)))
            return _cache[context][pvname]
        raise


def show_cache(print_out=True):
    """print out a listing of PVs in the current session to
    standard output.  Use the *print_out=False* option to be
    returned the listing instead of having it printed out.
    """
    out = []
    out.append('#  PVName        ChannelID/Context Connected?')
    out.append('#--------------------------------------------')
    for context, context_chids in  list(_cache.items()):
        for vname, val in list(context_chids.items()):
            chid = val.chid
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


_clear_cache_callbacks: Dict[int, Callable[[], None]] = {}


def clear_cache():
    """
    Clears global caches of Epics CA connections, and fully
    detaches from the CA context.  This is important when doing
    multiprocessing (and is done internally by CAProcess),
    but can be useful to fully reset a Channel Access session.

    Any class `PV` created prior this call without using `get_pv()`
    have to be disconnected (use `PV.disconnect()`) explicitly
    because disconnection clears subscriptions to events of
    Epics CA connection which are to be cleared here.
    No instance of the class `PV` created prior this call should be
    used after because underlaying Epics CA connections are cleared here.
    Failing to follow these rules may cause your application to experience
    a random SIGSEGV from inside Epics binaries.

    Use `register_clear_cache()` to register a function which will be
    called before Epics CA connections are cleared.

    This function is not thread safe.
    """
    # Clear any cache of CA users so there are not references
    # to the Epics CA connections which are to be cleared next.
    for clear_other_cache in _clear_cache_callbacks.values():
        clear_other_cache()

    # Unregister callbacks (if any)
    for chid, entry in list(_chid_cache.items()):
        try:
            clear_channel(chid)
        except ChannelAccessException:
            pass

    # Clear global state variables
    _cache.clear()
    _chid_cache.clear()

    # The old context is copied directly from the old process
    # in systems with proper fork() implementations
    detach_context()
    create_context()


def register_clear_cache(callback: Callable[[], None]):
    """
    Register a function which is to be called right before
    the Epics CA connections are removed. The purpose of the callback
    is to disconnect from Epics CA connections created through `ca.py`
    before they are cleared. Im summary, the function should:
    * Remove any reference to any Epics CA connection created
      through `ca.py`.
    * Remove any subscription fom any Epics CA connection created
      through `ca.py`.

    Failing to do so may result into a random SIGSEGV after using
    `ca.clear_cache`.
    """
    global _clear_cache_callbacks
    if callable(callback):
        _clear_cache_callbacks[id(callback)] = callback
    elif callback is not None:
        raise RuntimeError(f"Cannot register type {type(callback)}. Callable required.")


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
    :func:`create_channel`.

    Note that CA functions that take a Channel ID (chid) as an
    argument are  NOT wrapped by this: to get a chid, the
    library must have been initialized already."""
    @functools.wraps(fcn)
    def wrapper(*args, **kwds):
        "withCA wrapper"
        global libca
        if libca is None:
            initialize_libca()
        elif libca is _LIBCA_FINALIZED:
            return  # Avoid raising exceptions when Python shutting down
        return fcn(*args, **kwds)
    return wrapper

def withCHID(fcn):
    """decorator to ensure that first argument to a function is a Channel
    ID, ``chid``.  The test performed is very weak, as any ctypes long or
    python int will pass, but it is useful enough to catch most accidental
    errors before they would cause a crash of the CA library.
    """
    # It may be worth making a chid class (which could hold connection
    # data of _cache) that could be tested here.  For now, that
    # seems slightly 'not low-level' for this module.
    @functools.wraps(fcn)
    def wrapper(*args, **kwds):
        "withCHID wrapper"
        global libca
        if libca is _LIBCA_FINALIZED:
            return  # Avoid raising exceptions when Python shutting down

        if len(args)>0:
            chid = args[0]
            args = list(args)
            if isinstance(chid, int):
                args[0] = chid = dbr.chid_t(args[0])
            if not isinstance(chid, dbr.chid_t):
                msg = "%s: not a valid chid %s %s args %s kwargs %s!" % (
                    (fcn.__name__, chid, type(chid), args, kwds))
                raise ChannelAccessException(msg)
            if chid.value not in _chid_cache:
                raise ChannelAccessException('Unexpected channel ID')
        return fcn(*args, **kwds)
    return wrapper


def withConnectedCHID(fcn):
    """decorator to ensure that the first argument of a function is a
    fully connected Channel ID, ``chid``.  This test is (intended to be)
    robust, and will try to make sure a ``chid`` is actually connected
    before calling the decorated function.
    """
    @functools.wraps(fcn)
    def wrapper(*args, **kwds):
        "withConnectedCHID wrapper"
        global libca
        if libca is _LIBCA_FINALIZED:
            return  # Avoid raising exceptions when Python shutting down

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
                connected =  connect_channel(chid, timeout=timeout)
                if not connected:
                    fmt ="%s() timed out waiting '%s' to connect (%d seconds)"
                    raise ChannelAccessException(fmt % (fcn.__name__,
                                                name(chid), timeout))

        return fcn(*args, **kwds)
    return wrapper

def withMaybeConnectedCHID(fcn):
    """decorator to **try** to ensure that the first argument of a function
    is a connected Channel ID, ``chid``.
    """
    @functools.wraps(fcn)
    def wrapper(*args, **kwds):
        "withMaybeConnectedCHID wrapper"
        global libca
        if libca is _LIBCA_FINALIZED:
            return  # Avoid raising exceptions when Python shutting down

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
    return wrapper

def withInitialContext(fcn):
    """decorator to ensure that the wrapped function uses the
    initial threading context created at initialization of CA
    """
    @functools.wraps(fcn)
    def wrapper(*args, **kwds):
        "withInitialContext wrapper"
        use_initial_context()
        return fcn(*args, **kwds)
    return wrapper

def PySEVCHK(func_name, status, expected=dbr.ECA_NORMAL):
    """This checks the return *status* returned from a `libca.ca_***` and
    raises a :exc:`ChannelAccessException` if the value does not match the
    *expected* value (which is nornmally ``dbr.ECA_NORMAL``.

    The message from the exception will include the *func_name* (name of
    the Python function) and the CA message from :func:`message`.
    """
    if status == expected:
        return status
    raise CASeverityException(func_name, message(status))

def withSEVCHK(fcn):
    """decorator to raise a ChannelAccessException if the wrapped
    ca function does not return status = dbr.ECA_NORMAL.  This
    handles the common case of running :func:`PySEVCHK` for a
    function whose return value is from a corresponding libca function
    and whose return value should be ``dbr.ECA_NORMAL``.
    """
    @functools.wraps(fcn)
    def wrapper(*args, **kwds):
        "withSEVCHK wrapper"
        status = fcn(*args, **kwds)
        return PySEVCHK( fcn.__name__, status)
    return wrapper

##
## Event Handler for monitor event callbacks
def _onMonitorEvent(args):
    """Event Handler for monitor events: not intended for use"""
    try:
        entry = _get_cache_by_chid(args.chid)
    except KeyError:
        # In case the chid is no longer in our cache, exit now.
        return

    # If read access to a process variable is lost, this callback is invoked
    # indicating the loss in the status argument. Users can use the connection
    # callback to get informed of connection loss, so we just ignore any
    # bad status codes.

    if args.status != dbr.ECA_NORMAL:
        return

    value = dbr.cast_args(args)
    if value[1] is None:
        # Cannot process the input becaue casting failed.
        return

    kwds = {'ftype':args.type, 'count':args.count,
            'chid': args.chid, 'pvname': entry.pvname}

    # add kwds arguments for CTRL and TIME variants
    # this is in a try/except clause to avoid problems
    # caused by uninitialized waveform arrays
    try:
        kwds.update(**_unpack_metadata(ftype=args.type, dbr_value=value[0]))
    except IndexError:
        pass
    value = _unpack(args.chid, value, count=args.count, ftype=args.type)
    if callable(args.usr):
        args.usr(value=value, **kwds)

## connection event handler:
def _onConnectionEvent(args):
    "Connection notification - run user callbacks"
    try:
        entry = _get_cache_by_chid(args.chid)
    except KeyError:
        return

    entry.run_connection_callbacks(conn=(args.op == dbr.OP_CONN_UP),
                                   timestamp=time.time())


## get event handler:
def _onGetEvent(args, **kws):
    """get_callback event: simply store data contents which
    will need conversion to python data with _unpack()."""
    # print("GET EVENT: chid, user ", args.chid, args.usr)
    # print("GET EVENT: type, count ", args.type, args.count)
    # print("GET EVENT: status ",  args.status, dbr.ECA_NORMAL)
    try:
        entry = _get_cache_by_chid(args.chid)
    except KeyError:
        return

    ftype = args.usr
    if args.status != dbr.ECA_NORMAL:
        result = ChannelAccessGetFailure(
            'Get failed; status code: %d' % args.status,
            chid=args.chid,
            status=args.status
        )
    else:
        result = deepcopy(dbr.cast_args(args))
        if result[1] is None:
            result = ChannelAccessGetFailure(
                'Get failed; unknown type: %d' % args.type,
                chid=args.chid,
                status=args.status
            )

    with entry.lock:
        entry.get_results[ftype][0] = result


## put event handler:
def _onPutEvent(args, **kwds):
    'Put completion notification - run specified callback'
    fcn = args.usr
    if callable(fcn):
        fcn()


def _onAccessRightsEvent(args):
    'Access rights callback'
    try:
        entry = _chid_cache[_chid_to_int(args.chid)]
    except KeyError:
        return
    read = bool(args.access & 1)
    write = bool((args.access >> 1) & 1)
    entry.run_access_event_callbacks(read, write)


# create global reference to these callbacks
_CB_CONNECT = dbr.make_callback(_onConnectionEvent, dbr.connection_args)
_CB_PUTWAIT = dbr.make_callback(_onPutEvent,        dbr.event_handler_args)
_CB_GET     = dbr.make_callback(_onGetEvent,        dbr.event_handler_args)
_CB_EVENT   = dbr.make_callback(_onMonitorEvent,    dbr.event_handler_args)
_CB_ACCESS  = dbr.make_callback(_onAccessRightsEvent,
                                dbr.access_rights_handler_args)

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


def create_context(ctx=None):
    """Create a new context, using the value of :data:`PREEMPTIVE_CALLBACK`
    to set the context type. Note that both *context_create* and
    *create_context* (which is more consistent with the Verb_Object of
    the rest of the CA library) are supported.

    Parameters
    ----------
    ctx : int
       0 -- No preemptive callbacks,
       1 -- use use preemptive callbacks,
       None -- use value of :data:`PREEMPTIVE_CALLBACK`

    """
    context_create(ctx=ctx)
    global initial_context
    if initial_context is None:
        initial_context = current_context()

@withCA
def context_destroy():
    "destroy current context"
    ctx = current_context()
    ret = libca.ca_context_destroy()
    ctx_cache = _cache.pop(ctx, None)
    if ctx_cache is not None:
        ctx_cache.clear()
    return ret

def destroy_context():
    "destroy current context"
    return context_destroy()

@withCA
# @withSEVCHK
def attach_context(context):
    "attach to the supplied context"
    return libca.ca_attach_context(context)

@withCA
@withSEVCHK
def use_initial_context():
    """
    Attaches to the context created when libca is initialized.
    Using this function is recommended when writing threaded programs that
    using CA.

    See the advanced section in doc for further discussion.
    """
    global initial_context
    ret = dbr.ECA_NORMAL
    if initial_context != current_context():
        ret = libca.ca_attach_context(initial_context)
    return ret

@withCA
def detach_context():
    "detach context"
    return libca.ca_detach_context()

@withCA
def replace_printf_handler(writer=None):
    """replace the normal printf() output handler with
    the supplied writer function

    Parameters
    ----------
    writer:  callable or None [default]
         function to use for handling messages

    Notes
    -----
    1. `writer=None` will suppress all CA messages.
    2. `writer` should have a signature of `writer(*args)`,
       as `sys.stderr.write` and `sys.stdout.write` do.
    3. Due to limitations in ctypes, this will not work as well
       as expected. Once disabled, re-enabling ca_messages will
       receive only the first string argument, not the list of
       strings to be formatted.
    """
    global ca_printf
    def swallow(*args):  pass
    if writer is None:
        writer = swallow
    if not callable(writer):
        msg = "argument to replace_printf_handler() must be callable"
        raise ChannelAccessException(msg)

    def m_handler(*args):
        writer(*[bytes2str(a) for a in args])

    ca_printf = ctypes.CFUNCTYPE(None, ctypes.c_char_p,)(m_handler)
    return libca.ca_replace_printf_handler(ca_printf)

@withCA
def disable_ca_messages():
    """disable messages rom CA: `replace_printf_handler(None)`
    """
    replace_printf_handler(None)

@withCA
def enable_ca_messages(writer='stderr'):
    """enable messages from CA using the supplier writer

    Parameters
    ----------
    writer:   callable, `stderr`, `stdout`, or `None`
         function to use for handling messages

    Notes
    -----
    1. `writer=None` will suppress all CA messages.
    2. `writer` should have a signature of `writer(*args)`,
       as `sys.stderr.write` and `sys.stdout.write` do,
       though only the first value will actually be use.
    3. Due to limitations in ctypes, this will not work as well
       as expected. Once disabled, re-enabling ca_messages will
       receive only the first string argument, not the list of
       strings to be formatted.
    """
    if writer == 'stderr':
        writer = sys.stderr.write
    elif writer == 'stdout':
        writer = sys.stdout.write
    replace_printf_handler(writer)

@withCA
def current_context():
    "return the current context"
    ctx = libca.ca_current_context()
    if isinstance(ctx, ctypes.c_long):
        ctx = ctx.value
    return ctx

@withCA
def client_status(context, level):
    """print (to stderr) information about Channel Access status,
    including status for each channel, and search and connection statistics."""
    return libca.ca_client_status(context, level)

@withCA
def flush_io():
    "flush i/o"
    return libca.ca_flush_io()

@withCA
def message(status):
    """Print a message corresponding to a Channel Access status return value.
    """
    return bytes2str(libca.ca_message(status))

@withCA
def version():
    """   Print Channel Access version string.
    Currently, this should report '4.13' """
    return bytes2str(libca.ca_version())

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
    """a convenience function which is equivalent to::
       pend_event(evt)
       pend_io_(iot)

    """
    pend_event(evt)
    return pend_io(iot)

@withCA
def test_io():
    """test if IO is complete: returns True if it is"""
    return dbr.ECA_IODONE == libca.ca_test_io()

## create channel
@withCA
def create_channel(pvname, connect=False, auto_cb=True, callback=None):
    """ create a Channel for a given pvname

    creates a channel, returning the Channel ID ``chid`` used by other
    functions to identify this channel.

    Parameters
    ----------
    pvname :  string
        the name of the PV for which a channel should be created.
    connect : bool
        whether to (try to) connect to PV as soon as possible.
    auto_cb : bool
        whether to automatically use an internal connection callback.
    callback : callable or ``None``
        user-defined Python function to be called when the connection
        state change s.

    Returns
    -------
    chid : ctypes.c_long
        channel ID.


    Notes
    -----
    1. The user-defined connection callback function should be prepared to accept
    keyword arguments of

         ===========  =============================
         keyword      meaning
         ===========  =============================
          `pvname`    name of PV
          `chid`      Channel ID
          `conn`      whether channel is connected
         ===========  =============================


    2. If `auto_cb` is ``True``, an internal connection callback is used so
    that you should not need to explicitly connect to a channel, unless you
    are having difficulty with dropped connections.

    3. If the channel is already connected for the PV name, the callback
    will be called immediately.


    """
    # Note that _CB_CONNECT (defined above) is a global variable, holding
    # a reference to _onConnectionEvent:  This is really the connection
    # callback that is run -- the callack here is stored in the _cache
    # and called by _onConnectionEvent.

    context_cache = _cache[current_context()]

    # {}.setdefault is an atomic operation, so we are guaranteed to never
    # create the same channel twice here:
    with context_cache.setdefault(pvname, _SentinelWithLock()).lock:
        # Grab the entry again from the cache. Between the time the lock was
        # attempted and acquired, the cache may have changed.
        entry = context_cache[pvname]
        is_new_channel = isinstance(entry, _SentinelWithLock)
        if is_new_channel:
            callbacks = [callback] if callable(callback) else None
            entry = _CacheItem(chid=None, pvname=pvname, callbacks=callbacks)
            context_cache[pvname] = entry

            chid = dbr.chid_t()
            with entry.lock:
                ret = libca.ca_create_channel(
                    ctypes.c_char_p(str2bytes(pvname)), _CB_CONNECT, 0, 0,
                    ctypes.byref(chid)
                )
                PySEVCHK('create_channel', ret)

                entry.chid = chid
                _chid_cache[chid.value] = entry

    if (not is_new_channel and callable(callback) and
            callback not in entry.callbacks):
        entry.callbacks.append(callback)
        if entry.chid is not None and entry.conn:
            # Run the connection callback if already connected:
            callback(chid=_chid_to_int(entry.chid), pvname=pvname,
                     conn=entry.conn)

    if connect:
        connect_channel(entry.chid)
    return entry.chid

@withCHID
def connect_channel(chid, timeout=None, verbose=False):
    """connect to a channel, waiting up to timeout for a
    channel to connect.  It returns the connection state,
    ``True`` or ``False``.

    This is usually not needed, as implicit connection will be done
    when needed in most cases.

    Parameters
    ----------
    chid : ctypes.c_long
        Channel ID
    timeout : float
        maximum time to wait for connection.
    verbose : bool
        whether to print out debugging information

    Returns
    -------
    connection_state : bool
         that is, whether the Channel is connected

    Notes
    -----
    1. If *timeout* is ``None``, the value of :data:`DEFAULT_CONNECTION_TIMEOUT`
       is used (defaults to 2.0 seconds).

    2. Normally, channels will connect in milliseconds, and the connection
    callback will succeed on the first attempt.

    3. For un-connected Channels (that are nevertheless queried), the 'ts'
    (timestamp of last connection attempt) and 'failures' (number of failed
    connection attempts) from the :data:`_cache` will be used to prevent
    spending too much time waiting for a connection that may never happen.

    """
    if verbose:
        write(' connect channel -> %s %s %s ' %
               (repr(chid), repr(state(chid)), repr(dbr.CS_CONN)))
    conn = state(chid) == dbr.CS_CONN
    if not conn:
        # not connected yet, either indicating a slow network
        # or a truly un-connnectable channel.
        start_time = time.time()
        ctx = current_context()
        pvname = name(chid)
        if timeout is None:
            timeout = DEFAULT_CONNECTION_TIMEOUT

        while (not conn and ((time.time()-start_time) < timeout)):
            poll()
            conn = state(chid) == dbr.CS_CONN
        if not conn:
            entry = _cache[ctx][pvname]
            with entry.lock:
                entry.ts = time.time()
                entry.failures += 1
    return conn

# functions with very light wrappings:
@withCHID
def replace_access_rights_event(chid, callback=None):
    ch = get_cache(name(chid))

    if ch and callback is not None:
        ch.access_event_callback.append(callback)

    ret = libca.ca_replace_access_rights_event(chid, _CB_ACCESS)
    PySEVCHK('replace_access_rights_event', ret)

def _chid_to_int(chid):
    '''
    Return the integer representation of a chid

    Parameters
    ----------
    chid : ctypes.c_long, int

    Returns
    -------
    chid : int
    '''
    if hasattr(chid, 'value'):
        return int(chid.value)
    return chid


@withCHID
def name(chid):
    "return PV name for channel name"
    return bytes2str(libca.ca_name(chid))

@withCHID
def host_name(chid):
    "return host name and port serving Channel"
    return bytes2str(libca.ca_host_name(chid))

@withCHID
def element_count(chid):
    """return number of elements in Channel's data.
    1 for most Channels, > 1 for waveform Channels"""

    return libca.ca_element_count(chid)

@withCHID
def read_access(chid):
    "return *read access* for a Channel: 1 for ``True``, 0 for ``False``."
    return libca.ca_read_access(chid)

@withCHID
def write_access(chid):
    "return *write access* for a channel: 1 for ``True``, 0 for ``False``."
    return libca.ca_write_access(chid)

@withCHID
def field_type(chid):
    "return the integer DBR field type."
    return libca.ca_field_type(chid)

@withCHID
def clear_channel(chid):
    "clear the channel"
    ret = libca.ca_clear_channel(chid)
    entry = _chid_cache.pop(chid.value, None)
    if entry is not None:
        context_cache = _cache[entry.context]
        context_cache.pop(entry.pvname, None)
        with entry.lock:
            entry.chid = None
    return ret


@withCHID
def state(chid):
    "return state (that is, attachment state) for channel"

    return libca.ca_state(chid)

def isConnected(chid):
    """return whether channel is connected:  `dbr.CS_CONN==state(chid)`

    This is ``True`` for a connected channel, ``False`` for an unconnected channel.
    """

    return dbr.CS_CONN == state(chid)

def access(chid):
    """returns a string describing read/write access: one of
    `no access`, `read-only`, `write-only`, or `read/write`
    """
    acc = read_access(chid) + 2 * write_access(chid)
    return ('no access', 'read-only', 'write-only', 'read/write')[acc]

@withCHID
def promote_type(chid, use_time=False, use_ctrl=False):
    """promotes the native field type of a ``chid`` to its TIME or CTRL variant.
    Returns the integer corresponding to the promoted field value."""
    return promote_fieldtype( field_type(chid), use_time=use_time, use_ctrl=use_ctrl)

def promote_fieldtype(ftype, use_time=False, use_ctrl=False):
    """promotes the native field type to its TIME or CTRL variant.
    Returns the integer corresponding to the promoted field value."""
    if use_ctrl:
        ftype += dbr.CTRL_STRING
    elif use_time:
        ftype += dbr.TIME_STRING
    if ftype == dbr.CTRL_STRING:
        ftype = dbr.TIME_STRING
    return ftype


def _unpack(chid, data, count=None, ftype=None, as_numpy=True):
    """unpacks raw data for a Channel ID `chid` returned by libca functions
    including `ca_array_get_callback` or subscription callback, and returns
    the corresponding Python data

    Normally, users are not expected to need to access this function, but
    it will be necessary why using :func:`sg_get`.

    Parameters
    ----------
    chid  :  ctypes.c_long or ``None``
        channel ID (if not None, used for determining count and ftype)
    data  :  object
        raw data as returned by internal libca functions.
    count :  integer
        number of elements to fetch (defaults to element count of chid  or 1)
    ftype :  integer
        data type of channel (defaults to native type of chid)
    as_numpy : bool
        whether to convert to numpy array.
    """

    def scan_string(data, count, elem_count):
        """ Scan a string, or an array of strings as a list, depending on content """
        out = []
        for elem in range(min(count, len(data))):
            this = strjoin('', bytes2str(data[elem].value)).rstrip()
            if '\x00' in this:
                this = this[:this.index('\x00')]
            out.append(this)
        if len(out) == 1 and elem_count==1:
            out = out[0]
        return out

    def array_cast(data, count, ntype, use_numpy):
        "cast ctypes array to numpy array (if using numpy)"
        if use_numpy:
            dtype = dbr.NP_Map.get(ntype, None)
            if dtype is not None:
                out = numpy.empty(shape=(count,), dtype=dbr.NP_Map[ntype])
                ctypes.memmove(out.ctypes.data, data, out.nbytes)
            else:
                out = numpy.ctypeslib.as_array(deepcopy(data))
        else:
            out = deepcopy(data)
        return out

    def unpack(data, count, ntype, use_numpy, elem_count):
        "simple, native data type"
        if data is None:
            return None
        if ntype == dbr.CHAR and elem_count > 1:
            return array_cast(data, count, ntype, use_numpy)
        if count == 1 and ntype != dbr.STRING:
            return data[0]
        if ntype == dbr.STRING:
            return scan_string(data, count, elem_count)
        if count != 1:
            return array_cast(data, count, ntype, use_numpy)
        return data

    # Grab the native-data-type data
    try:
        _, data = data
    except (TypeError, IndexError):
        return None
    except ValueError:
        pass

    if count == 0 or count is None:
        count = len(data)
    else:
        count = min(len(data), count)

    if ftype is None and chid is not None:
        ftype = field_type(chid)
    if ftype is None:
        ftype = dbr.INT

    ntype = dbr.native_type(ftype)
    elem_count = element_count(chid)
    use_numpy = (HAS_NUMPY and as_numpy and ntype != dbr.STRING and count != 1)
    return unpack(data, count, ntype, use_numpy, elem_count)


def _unpack_metadata(ftype, dbr_value):
    '''Unpack DBR metadata into a dictionary

    Parameters
    ----------
    ftype : int
        The field type for the respective DBR value
    dbr_value : ctype.Structure
        The structure holding the data to be unpacked

    Returns
    -------
    md : dict
        A dictionary containing zero or more of the following keys, depending
        on ftype::

           {'precision', 'units', 'status', 'severity', 'enum_strs', 'status',
           'severity', 'timestamp', 'posixseconds', 'nanoseconds',
           'upper_disp_limit', 'lower_disp_limit', 'upper_alarm_limit',
           'upper_warning_limit', 'lower_warning_limit','lower_alarm_limit',
           'upper_ctrl_limit', 'lower_ctrl_limit'}
    '''
    md = {}
    if ftype >= dbr.CTRL_STRING:
        for attr in dbr.ctrl_limits + ('precision', 'units', 'status',
                                       'severity'):
            if hasattr(dbr_value, attr):
                md[attr] = getattr(dbr_value, attr)
                if attr == 'units':
                    md[attr] = bytes2str(getattr(dbr_value, attr, None))

        if hasattr(dbr_value, 'strs') and getattr(dbr_value, 'no_str', 0) > 0:
            md['enum_strs'] = tuple(bytes2str(dbr_value.strs[i].value)
                                    for i in range(dbr_value.no_str))
    elif ftype >= dbr.TIME_STRING:
        md['status'] = dbr_value.status
        md['severity'] = dbr_value.severity
        md['timestamp'] = dbr.make_unixtime(dbr_value.stamp)
        md['posixseconds'] = dbr_value.stamp.secs + dbr.EPICS2UNIX_EPOCH
        md['nanoseconds'] = dbr_value.stamp.nsec

    return md


@withMaybeConnectedCHID
def get_with_metadata(chid, ftype=None, count=None, wait=True, timeout=None,
                      as_string=False, as_numpy=True):
    """Return the current value along with metadata for a Channel

    Parameters
    ----------
    chid :  ctypes.c_long
       Channel ID
    ftype : int
       field type to use (native type is default)
    count : int
       maximum element count to return (full data returned by default)
    as_string : bool
       whether to return the string representation of the value.  See notes.
    as_numpy : bool
       whether to return the Numerical Python representation for array /
       waveform data.
    wait : bool
        whether to wait for the data to be received, or return immediately.
    timeout : float
        maximum time to wait for data before returning ``None``.

    Returns
    -------
    data : dict or None
       The dictionary of data, guaranteed to at least have the 'value' key.
       Depending on ftype, other keys may also be present::

           {'precision', 'units', 'status', 'severity', 'enum_strs', 'status',
           'severity', 'timestamp', 'posixseconds', 'nanoseconds',
           'upper_disp_limit', 'lower_disp_limit', 'upper_alarm_limit',
           'upper_warning_limit', 'lower_warning_limit','lower_alarm_limit',
           'upper_ctrl_limit', 'lower_ctrl_limit'}

       Returns ``None`` if the channel is not connected, `wait=False` was used,
       or the data transfer timed out.

    See `get()` for additional usage notes.
    """
    if ftype is None:
        ftype = field_type(chid)
    if ftype in (None, -1):
        return None
    if count is None:
        count = 0
        # count = element_count(chid)
        # don't default to the element_count here - let EPICS tell us the size
        # in the _onGetEvent callback
    else:
        count = min(count, element_count(chid))

    entry = get_cache(name(chid))
    if not entry:
        return

    # implementation note: cached value of
    #   None        implies no value, no expected callback
    #   GET_PENDING implies no value yet, callback expected.
    with entry.lock:
        last_get, = entry.get_results[ftype]
        if last_get is not GET_PENDING:
            entry.get_results[ftype] = [GET_PENDING]
            ret = libca.ca_array_get_callback(
                ftype, count, chid, _CB_GET, ctypes.py_object(ftype))
            PySEVCHK('get', ret)

    if wait:
        return get_complete_with_metadata(chid, count=count, ftype=ftype,
                                          timeout=timeout, as_string=as_string,
                                          as_numpy=as_numpy)


@withMaybeConnectedCHID
def get(chid, ftype=None, count=None, wait=True, timeout=None,
        as_string=False, as_numpy=True):
    """return the current value for a Channel.
    Note that there is not a separate form for array data.

    Parameters
    ----------
    chid :  ctypes.c_long
       Channel ID
    ftype : int
       field type to use (native type is default)
    count : int
       maximum element count to return (full data returned by default)
    as_string : bool
       whether to return the string representation of the value.
       See notes below.
    as_numpy : bool
       whether to return the Numerical Python representation
       for array / waveform data.
    wait : bool
        whether to wait for the data to be received, or return immediately.
    timeout : float
        maximum time to wait for data before returning ``None``.

    Returns
    -------
    data : object
       Normally, the value of the data.  Will return ``None`` if the
       channel is not connected, `wait=False` was used, or the data
       transfer timed out.

    Notes
    -----
    1. Returning ``None`` indicates an *incomplete get*

    2. The *as_string* option is not as complete as the *as_string*
    argument for :meth:`PV.get`.  For Enum types, the name of the Enum
    state will be returned.  For waveforms of type CHAR, the string
    representation will be returned.  For other waveforms (with *count* >
    1), a string like `<array count=3, type=1>` will be returned.

    3. The *as_numpy* option will convert waveform data to be returned as a
    numpy array.  This is only applied if numpy can be imported.

    4. The *wait* option controls whether to wait for the data to be
    received over the network and actually return the value, or to return
    immediately after asking for it to be sent.  If `wait=False` (that is,
    immediate return), the *get* operation is said to be *incomplete*.  The
    data will be still be received (unless the channel is disconnected)
    eventually but stored internally, and can be read later with
    :func:`get_complete`.  Using `wait=False` can be useful in some
    circumstances.

    5. The *timeout* option sets the maximum time to wait for the data to
    be received over the network before returning ``None``.  Such a timeout
    could imply that the channel is disconnected or that the data size is
    larger or network slower than normal.  In that case, the *get*
    operation is said to be *incomplete*, and the data may become available
    later with :func:`get_complete`.

    """
    info = get_with_metadata(chid, ftype=ftype, count=count, wait=wait,
                             timeout=timeout, as_string=as_string,
                             as_numpy=as_numpy)
    return (info['value'] if info is not None else None)


@withMaybeConnectedCHID
def get_complete_with_metadata(chid, ftype=None, count=None, timeout=None,
                               as_string=False, as_numpy=True):
    """Returns the current value and associated metadata for a Channel

    This completes an earlier incomplete :func:`get` that returned ``None``,
    either because `wait=False` was used or because the data transfer did not
    complete before the timeout passed.

    Parameters
    ----------
    chid : ctypes.c_long
        Channel ID
    ftype :  int
        field type to use (native type is default)
    count : int
        maximum element count to return (full data returned by default)
    as_string : bool
        whether to return the string representation of the value.
    as_numpy :  bool
        whether to return the Numerical Python representation
        for array / waveform data.
    timeout : float
        maximum time to wait for data before returning ``None``.

    Returns
    -------
    data : dict or None
       This function will return ``None`` if the previous :func:`get` actually
       completed, or if this data transfer also times out.

    See `get_complete()` for additional usage notes.
    """
    if ftype is None:
        ftype = field_type(chid)
    if count is None:
        count = element_count(chid)
    else:
        count = min(count, element_count(chid))

    entry = get_cache(name(chid))
    if not entry:
        return

    get_result = entry.get_results[ftype]

    if get_result[0] is None:
        warnings.warn('get_complete without initial get() call')
        return None

    t0 = time.time()
    if timeout is None:
        timeout = 1.0 + log10(max(1, count))

    while get_result[0] is GET_PENDING:
        poll()

        if time.time()-t0 > timeout:
            msg = "ca.get('%s') timed out after %.2f seconds."
            warnings.warn(msg % (name(chid), timeout))
            return None

    full_value, = get_result

    # print("Get Complete> Unpack ", ncache['value'], count, ftype)

    if isinstance(full_value, Exception):
        get_failure_reason = full_value
        raise get_failure_reason

    # NOTE: unpacking happens for each requester; this could potentially be put
    # in the get callback itself. (different downside there...)
    extended_data, _ = full_value
    metadata = _unpack_metadata(ftype=ftype, dbr_value=extended_data)
    val = _unpack(chid, full_value, count=count,
                  ftype=ftype, as_numpy=as_numpy)
    # print("Get Complete unpacked to ", val)

    if as_string:
        val = _as_string(val, chid, count, ftype)
    elif isinstance(val, ctypes.Array) and HAS_NUMPY and as_numpy:
        val = numpy.ctypeslib.as_array(deepcopy(val))

    # value retrieved, clear cached value
    metadata['value'] = val
    return metadata

@withMaybeConnectedCHID
def get_complete(chid, ftype=None, count=None, timeout=None, as_string=False,
                 as_numpy=True):
    """returns the current value for a Channel, completing an
    earlier incomplete :func:`get` that returned ``None``, either
    because `wait=False` was used or because the data transfer
    did not complete before the timeout passed.

    Parameters
    ----------
    chid : ctypes.c_long
        Channel ID
    ftype :  int
        field type to use (native type is default)
    count : int
        maximum element count to return (full data returned by default)
    as_string : bool
        whether to return the string representation of the value.
    as_numpy :  bool
        whether to return the Numerical Python representation
        for array / waveform data.
    timeout : float
        maximum time to wait for data before returning ``None``.

    Returns
    -------
    data : object
       This function will return ``None`` if the previous :func:`get`
       actually completed, or if this data transfer also times out.


    Notes
    -----
    1. The default timeout is dependent on the element count::
    default_timout = 1.0 + log10(count)  (in seconds)

    2. Consult the doc for :func:`get` for more information.

    """
    info = get_complete_with_metadata(chid, ftype=ftype, count=count,
                                      timeout=timeout, as_string=as_string,
                                      as_numpy=as_numpy)
    return (info['value'] if info is not None
            else None)


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
        callback_data=None, ftype=None):
    """sets the Channel to a value, with options to either wait
    (block) for the processing to complete, or to execute a
    supplied callback function when the process has completed.


    Parameters
    ----------
    chid :  ctypes.c_long
        Channel ID
    wait : bool
        whether to wait for processing to complete (or time-out)
        before returning.
    timeout : float
        maximum time to wait for processing to complete before returning anyway.
    callback : ``None`` or callable
        user-supplied function to run when processing has completed.
    callback_data :  object
        extra data to pass on to a user-supplied callback function.
    ftype : ``None`` or int (valid dbr type)
        force field type to be a non-native form (None will use native form)

    Returns
    -------
    status : int
         1  for success, -1 on time-out

    Notes
    -----
    1. Specifying a callback will override setting `wait=True`.

    2. A put-callback function will be called with keyword arguments
        pvname=pvname, data=callback_data

    """
    if ftype is None:
        ftype = field_type(chid)
    count = nativecount = element_count(chid)
    if count > 1:
        # check that data for array PVS is a list, array, or string
        try:
            if ftype == dbr.STRING and isinstance(value, (str, bytes)):
                # len('abc') --> 3, however this is one element for dbr.STRING ftype
                count = 1
            else:
                count = min(len(value), count)

            if count == 0:
                count = nativecount
        except TypeError:
            write('''PyEpics Warning:
     value put() to array PV must be an array or sequence''')
    if ftype == dbr.CHAR and nativecount > 1 and isinstance(value, (str, bytes)):
        count += 1
        count = min(count, nativecount)

    # if needed convert to basic string/bytes git stform
    if isinstance(value, str):
        value = bytes(value, IOENCODING)

    data = (count*dbr.Map[ftype])()
    if ftype == dbr.STRING:
        if isinstance(value, (str, bytes)):
            data[0].value = value
        else:
            for elem in range(min(count, len(value))):
                data[elem].value = bytes(str(value[elem]), IOENCODING)
    elif nativecount == 1:
        if ftype == dbr.CHAR:
            if isinstance(value, (str, bytes)):
                if isinstance(value, bytes):
                    value = value.decode('ascii', 'replace')
                value = [ord(i) for i in value] + [0, ]
            else:
                data[0] = value
        else:
            # allow strings (even bits/hex) to be put to integer types
            if isinstance(value, (str, bytes)) and isinstance(data[0], (int, )):
                value = int(value, base=0)
            try:
                data[0] = value
            except TypeError:
                data[0] = type(data[0])(value)
            except:
                errmsg = "cannot put value '%s' to PV of type '%s'"
                tname  = dbr.Name(ftype).lower()
                raise ChannelAccessException(errmsg % (repr(value), tname))

    else:
        if ftype == dbr.CHAR and isinstance(value, (str, bytes)):
            if isinstance(value, bytes):
                value = value.decode('ascii', 'replace')
            value = [ord(i) for i in value] + [0, ]
        try:
            ndata, nuser = len(data), len(value)
            if nuser > ndata:
                value = value[:ndata]
            data[:nuser] = list(value)

        except (ValueError, IndexError):
            errmsg = "cannot put array data to PV of type '%s'"
            raise ChannelAccessException(errmsg % (repr(value)))

    # simple put, without wait or callback
    if not (wait or callable(callback)):
        ret = libca.ca_array_put(ftype, count, chid, data)
        PySEVCHK('put', ret)
        poll()
        return ret

    # wait with callback (or put_complete)
    pvname = name(chid)
    start_time = time.time()
    completed = {'status': False}

    def put_completed():
        completed['status'] = True
        _put_completes.remove(put_completed)
        if not callable(callback):
            return

        if isinstance(callback_data, dict):
            kwargs = callback_data
        else:
            kwargs = {'data': callback_data}

        callback(pvname=pvname, **kwargs)

    _put_completes.append(put_completed)

    ret = libca.ca_array_put_callback(ftype, count, chid, data, _CB_PUTWAIT,
                                      ctypes.py_object(put_completed))

    PySEVCHK('put', ret)
    poll(evt=1.e-4, iot=0.05)
    if wait:
        while not (completed['status'] or
                   (time.time()-start_time) > timeout):
            poll()
        if not completed['status']:
            ret = -ret
    return ret


@withMaybeConnectedCHID
def get_ctrlvars(chid, timeout=5.0, warn=True):
    """return the CTRL fields for a Channel.

    Depending on the native type, the keys may include
        *status*, *severity*, *precision*, *units*, enum_strs*,
        *upper_disp_limit*, *lower_disp_limit*, upper_alarm_limit*,
        *lower_alarm_limit*, upper_warning_limit*, *lower_warning_limit*,
        *upper_ctrl_limit*, *lower_ctrl_limit*

    Notes
    -----
    enum_strs will be a list of strings for the names of ENUM states.

    """
    ftype = promote_type(chid, use_ctrl=True)
    metadata = get_with_metadata(chid, ftype=ftype, count=1, timeout=timeout,
                                 wait=True)
    if metadata is not None:
        # Ignore the value returned:
        metadata.pop('value', None)
    return metadata


@withCHID
def get_timevars(chid, timeout=5.0, warn=True):
    """returns a dictionary of TIME fields for a Channel.
    This will contain keys of  *status*, *severity*, and *timestamp*.
    """
    ftype = promote_type(chid, use_time=True)
    metadata = get_with_metadata(chid, ftype=ftype, count=1, timeout=timeout,
                                 wait=True)
    if metadata is not None:
        # Ignore the value returned:
        metadata.pop('value', None)
    return metadata


def get_timestamp(chid):
    """return the timestamp of a Channel -- the time of last update."""
    return get_timevars(chid).get('timestamp', 0)

def get_severity(chid):
    """return the severity of a Channel."""
    return get_timevars(chid).get('severity', 0)

def get_precision(chid):
    """return the precision of a Channel.  For Channels with
    native type other than FLOAT or DOUBLE, this will be 0"""
    if field_type(chid) in (dbr.FLOAT, dbr.DOUBLE):
        return get_ctrlvars(chid).get('precision', None)
    return None

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

@withCHID
def create_subscription(chid, use_time=False, use_ctrl=False, ftype=None,
                        mask=None, callback=None, count=0, timeout=None):
    """create a *subscription to changes*. Sets up a user-supplied
    callback function to be called on any changes to the channel.

    Parameters
    ----------
    chid  : ctypes.c_long
        channel ID
    use_time : bool
        whether to use the TIME variant for the PV type
    use_ctrl : bool
        whether to use the CTRL variant for the PV type
    ftype : integer or None
       ftype to use, overriding native type, `use_time` or `use_ctrl`
       if ``None``, the native type is looked up, which requires a
       connected channel.
    mask : integer or None
       bitmask combination of :data:`dbr.DBE_ALARM`, :data:`dbr.DBE_LOG`, and
       :data:`dbr.DBE_VALUE`, to control which changes result in a callback.
       If ``None``, defaults to :data:`DEFAULT_SUBSCRIPTION_MASK`.

    callback : ``None`` or callable
        user-supplied callback function to be called on changes

    timeout : ``None`` or int
        connection timeout used for unconnected channels.

    Returns
    -------
    (callback_ref, user_arg_ref, event_id)

        The returned tuple contains *callback_ref* an *user_arg_ref* which
        are references that should be kept for as long as the subscription
        lives (otherwise they may be garbage collected, causing no end of
        trouble).  *event_id* is the id for the event (useful for clearing
        a subscription).

    Notes
    -----
    Keep the returned tuple in named variable!! if the return argument
    gets garbage collected, a coredump will occur.

    If the channel is not connected, the ftype must be specified for a
    successful subscription.
    """

    mask = mask or DEFAULT_SUBSCRIPTION_MASK
    if ftype is None:
        if not isConnected(chid):
            if timeout is None:
                timeout = DEFAULT_CONNECTION_TIMEOUT
            fmt ="%s() timed out waiting '%s' to connect (%d seconds)"
            if not connect_channel(chid, timeout=timeout):
                raise ChannelAccessException(fmt % ("create_subscription",
                                                    (chid), timeout))
        ftype = field_type(chid)

    ftype = promote_fieldtype(ftype, use_time=use_time, use_ctrl=use_ctrl)
    uarg  = ctypes.py_object(callback)
    evid  = ctypes.c_void_p()
    poll()
    ret = libca.ca_create_subscription(ftype, count, chid, mask,
                                       _CB_EVENT, uarg, ctypes.byref(evid))
    PySEVCHK('create_subscription', ret)

    poll()
    return (_CB_EVENT, uarg, evid)

@withCA
@withSEVCHK
def clear_subscription(event_id):
    "cancel subscription given its *event_id*"
    return libca.ca_clear_subscription(event_id)

@withCA
@withSEVCHK
def sg_block(gid, timeout=10.0):
    "block for a synchronous group to complete processing"
    return libca.ca_sg_block(gid, timeout)

@withCA
def sg_create():
    """create synchronous group.
    Returns a *group id*, `gid`, which is used to identify this group and
    to be passed to all other synchronous group commands.
    """
    gid  = ctypes.c_ulong()
    pgid = ctypes.pointer(gid)
    ret =  libca.ca_sg_create(pgid)
    PySEVCHK('sg_create', ret)
    return gid

@withCA
@withSEVCHK
def sg_delete(gid):
    "delete a synchronous group"
    return libca.ca_sg_delete(gid)

@withCA
def sg_test(gid):
    "test whether a synchronous group has completed."
    ret = libca.ca_sg_test(gid)
    return PySEVCHK('sg_test', ret, dbr.ECA_IODONE)

@withCA
@withSEVCHK
def sg_reset(gid):
    "resets a synchronous group"
    return libca.ca_sg_reset(gid)

def sg_get(gid, chid, ftype=None, as_numpy=True, as_string=True):
    """synchronous-group get of the current value for a Channel.
    same options as get()

    This function will not immediately return the value, of course, but the
    address of the underlying data.

    After the :func:`sg_block` has completed, you must use :func:`_unpack`
    to convert this data address to the actual value(s).

    Examples
    ========

    >>> chid = epics.ca.create_channel(PV_Name)
    >>> epics.ca.connect_channel(chid1)
    >>> sg = epics.ca.sg_create()
    >>> data = epics.ca.sg_get(sg, chid)
    >>> epics.ca.sg_block(sg)
    >>> print(epics.ca._unpack(data, chid=chid))

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
    """perform a `put` within a synchronous group.

    This `put` cannot wait for completion or for a a callback to complete.
    """
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
        # numpy.fromstring(("%s%s" % (s, pythonb'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value, (str, bytes)):
            pad = [0]*(1+count-len(value))
            if isinstance(value, bytes):
                value = value.decode('ascii', 'replace')
            value = ([ord(i) for i in value] + pad)[:count]

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

class CAThread(threading.Thread):
    """
    Sub-class of threading.Thread to ensure that the
    initial CA context is used.
    """
    def run(self):
        use_initial_context()
        threading.Thread.run(self)

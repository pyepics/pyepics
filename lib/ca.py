#!usr/bin/env python
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
import atexit

try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from . import dbr

EPICS_STR_ENCODING = 'ASCII'
PY_VERSION = sys.version_info[0]
def get_strconvertors():
    """create string wrappers to pass to C functions for both
    Python2 and Python3.  Note that the EPICS CA library uses
    char* to represent strings.  In Python3, char* maps to a
    sequence of bytes which must be explicitly converted to a
    Python string by specifying the encoding.  That is, ASCII
    encoding is not implicitly assumed.

    That is, for Python3 one sends and receives sequences of
    bytes to libca. This function returns the translators
    (str2bytes, bytes2str), assuming the encoding defined in
    EPICS_STR_ENCODING (which is 'ASCII' by default).  
    """
    if PY_VERSION >= 3:
        def s2b(st1):
            'string to byte'
            if isinstance(st1, bytes):
                return st1
            return bytes(st1, EPICS_STR_ENCODING)
        def b2s(st1):
            'byte to string'
            if isinstance(st1, str):
                return st1
            return str(st1, EPICS_STR_ENCODING)
        return s2b, b2s
    return str, str

str2bytes, bytes2str = get_strconvertors()

def strjoin(sep, seq):
    "join string sequence with a separator"
    if PY_VERSION < 3:
        return sep.join(seq)

    if isinstance(sep, bytes):
        sep = bytes2str(sep)
    if isinstance(seq[0], bytes): 
        seq = [bytes2str(i) for i in seq]
    return sep.join(seq)
    
## holder for shared library
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
        Exception.__init__(self)
        self.fcn = fcn
        self.msg = msg
    def __str__(self):
        return " %s returned '%s'" % (self.fcn, self.msg)

def find_libca():
    """
    find location of ca dynamic library
    """
    search_path = [os.path.split( os.path.abspath(__file__))[0]]
    search_path.extend(sys.path)
    path_sep = ':'
    if os.name == 'nt':
        path_sep = ';'
        search_path.append(os.path.join(sys.prefix, 'DLLs'))
    
    search_path.extend(os.environ['PATH'].split(path_sep))

    os.environ['PATH'] = path_sep.join(search_path)  

    dllpath  = ctypes.util.find_library('ca')
    if dllpath is not None:
        return dllpath

    ## OK, simplest version didn't work, look explicity through path
    known_hosts = {'Linux':   ('linux-x86', 'linux-x86_64') ,
                   'Darwin':  ('darwin-ppc', 'darwin-x86'),
                   'solaris': ('solaris-sparc',) }
    
    if os.name == 'posix':
        libname = 'libca.so'
        ldpath = os.environ.get('LD_LIBRARY_PATH', '').split(':')

        if sys.platform == 'darwin':
            ldpath = os.environ.get('DYLD_LIBRARY_PATH', '').split(':')
            libname = 'libca.dylib'

        epics_base = os.environ.get('EPICS_BASE', '.')
        host_arch = os.uname()[0]
        if host_arch in known_hosts:
            epicspath = []
            for adir in known_hosts[host_arch]:
                epicspath.append(os.path.join(epics_base, 'lib', adir))
        for adir in search_path + ldpath + epicspath + sys.path:
            if os.path.exists(adir) and os.path.isdir(adir):
                if libname in os.listdir(adir):
                    return os.path.join(adir, libname)

    raise ChannelAccessException('find_libca',
                                 'Cannot find Epics CA DLL')

        
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

    dllname = find_libca()
    
    load_dll = ctypes.cdll.LoadLibrary
    if os.name == 'nt':
        load_dll = ctypes.windll.LoadLibrary
    try:
        libca = load_dll(dllname)
    except:
        raise ChannelAccessException('initialize_libca',
                                     'Loading Epics CA DLL failed')
        
    ca_context = {False:0, True:1}[PREEMPTIVE_CALLBACK]
    ret = libca.ca_context_create(ca_context)
    if ret != dbr.ECA_NORMAL:
        raise ChannelAccessException('initialize_libca',
                                     'Cannot create Epics CA Context')

    if AUTO_CLEANUP:
        atexit.register(finalize_libca)
    return libca

def finalize_libca(maxtime=10.0):
    """shutdown channel access:
    run clear_channel(chid) for all chids in _cache
    then flush_io() and poll() a few times.
    """
    try:
        start_time = time.time()
        flush_io()
        poll()
        for context_chids in  list(_cache.values()):
            for key, val in list(context_chids.items()):
                clear_channel(val['chid'])
                context_chids[key] = {}
        _cache.clear()

        for i in range(10):
            flush_io()
            poll()
            if time.time()-start_time > maxtime:
                break
        context_destroy()
    except:
        pass

def show_cache(print_out=True):
    """Show list of cached PVs"""
    out = []
    out.append('#  PV name    Is Connected?   Channel ID  Context')
    out.append('#---------------------------------------')
    for context, context_chids in  list(_cache.items()):
        for vname, val in list(context_chids.items()):
            out.append(" %s   %s     %s  %i" % (vname,
                                                repr(val['conn']),
                                                repr(val['chid']), context))
    out = strjoin('\n', out)
    if print_out:
        sys.stdout.write("%s\n" % out)
    else:
        return out
    
## decorator functions for ca functionality:
#  decorator name      ensures before running decorated function:
#  --------------      -----------------------------------------------
#   withCA               libca is initialized 
#   withCHID             (crudely) that the 1st arg is a chid (c_long)
#   withConnectedCHID    1st arg is a connected chid.
##

def withCA(fcn):
    """decorator to ensure that libca and a context are created
    prior to function calls to the channel access library. This is
    intended for functions that at the startup of CA, such as
        create_channel

    Note that CA functions that take a Channel ID (chid) as an
    argument are  NOT wrapped by this: to get a chid, the
    library must have been initialized already."""
    def wrapper(*args, **kw):
        "withCA wraper"
        global libca
        if libca is None:
            libca = initialize_libca()
        return fcn(*args, **kw)
    return wrapper

def withCHID(fcn):
    """decorator to ensure that first argument to a function
    is a chid. This performs a very weak test, as any ctypes
    long or python int will pass.

    It may be worth making a chid class (which could hold connection
    data of _cache) that could be tested here.  For now, that
    seems slightly 'not low-level' for this module.
    """
    def wrapper(*args, **kw):
        "withCHID wrapper"
        if len(args)>0:
            if not isinstance(args[0], (ctypes.c_long, int)):
                raise ChannelAccessException(fcn.__name__,
                                             "not a valid chid!")
        return fcn(*args, **kw)
    return wrapper


def withConnectedCHID(fcn):
    """decorator to ensure that first argument to a function is a
    chid that is actually connected. This will attempt to connect
    if needed."""
    def wrapper(*args, **kw):
        "withConnectedCHID wrapper"
        if len(args)>0:
            if not isinstance(args[0], ctypes.c_long):
                raise ChannelAccessException(fcn.__name__,
                                             "not a valid chid!")
            try:
                mystate = state(args[0])
            except:
                mystate = None

            if mystate != dbr.CS_CONN:
                try:
                    timeout = kw.get('timeout', DEFAULT_CONNECTION_TIMEOUT)
                    connect_channel(args[0], timeout=timeout, force=False)
                    mystate = state(args[0])                    
                except StandardError:
                    mystate = None
            if mystate != dbr.CS_CONN:
                raise ChannelAccessException(fcn.__name__,
                                             "channel cannot connect")
        return fcn(*args, **kw)
    return wrapper

def PySEVCHK(func_name, status, expected=dbr.ECA_NORMAL):
    """raise a ChannelAccessException if the wrapped
    status != ECA_NORMAL
    """
    if status == expected:
        return status
    raise ChannelAccessException(func_name, message(status))

def withSEVCHK(fcn):
    """decorator to raise a ChannelAccessException if the wrapped
    ca function does not return status=ECA_NORMAL
    """
    def wrapper(*args, **kw):
        "withSEVCHK wrapper"
        status = fcn(*args, **kw)
        return PySEVCHK( fcn.__name__, status)
    return wrapper

###
#
# Now we're ready to wrap libca functions
#
###

# contexts
@withCA
@withSEVCHK
def context_create(context=None):
    if not PREEMPTIVE_CALLBACK:
        raise ChannelAccessException('context_create',
            'Cannot create new context with PREEMPTIVE_CALLBACK=False')
    if context is None:
        context = {False:0, True:1}[PREEMPTIVE_CALLBACK]
    return libca.ca_context_create(context)

@withCA
def context_destroy():
    ret = libca.ca_context_destroy()
    return PySEVCHK('context_destroy', ret, 0)
    
@withCA
def attach_context(context):
    ret = libca.ca_attach_context(context) 
    return PySEVCHK('attach_context', ret, dbr.ECA_ISATTACHED)
        
@withCA
def detach_context():
    return libca.ca_detach_context()

@withCA
def current_context():
    "return this context"
    fcn = libca.ca_current_context
    fcn.restype = ctypes.c_void_p
    return fcn()

@withCA
def client_status(context, level):
    "return status of client"
    fcn = libca.ca_client_status
    fcn.argtypes = (ctypes.c_void_p, ctypes.c_long)
    return fcn(context, level)

@withCA
def flush_io():
    "i/o flush"
    return libca.ca_flush_io()

@withCA
def message(status):
    "write message"
    fcn = libca.ca_message
    fcn.restype = ctypes.c_char_p
    return bytes2str(fcn(status))

@withCA
def version():
    """return CA version"""
    fcn = libca.ca_version
    fcn.restype = ctypes.c_char_p
    return bytes2str(fcn())

@withCA
@withSEVCHK
def pend_io(timeout=1.0):
    """polls CA for i/o. """    
    fcn   = libca.ca_pend_io
    fcn.argtypes = [ctypes.c_double]
    return fcn(timeout)

@withCA
def pend_event(timeout=1.e-5):
    """polls CA for events """    
    fcn = libca.ca_pend_event
    fcn.argtypes = [ctypes.c_double]
    ret = fcn(timeout)
    return PySEVCHK( 'pend_event', ret,  dbr.ECA_TIMEOUT)

@withCA
def poll(evt=1.e-4, iot=10.0):
    """polls CA for events and i/o. """
    pend_event(evt)
    return pend_io(iot)    

@withCA
def test_io():
    """test if IO is complete: returns True if it is"""
    return (dbr.ECA_IODONE ==  libca.ca_test_io())

## create channel

@withCA
def create_channel(pvname, connect=False, userfcn=None):
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
    pvn = str2bytes(pvname)    
    ret = libca.ca_create_channel(pvn, _CB_connect, 0, 0,
                                  ctypes.byref(chid))
    PySEVCHK('create_channel', ret)

    ctx = current_context()
    if ctx not in _cache:
        _cache[ctx] = {}
    
    _cache[ctx][pvname] = {'chid':chid, 'conn':False,
                           'ts':0, 'failures':0,
                           'userfcn': userfcn}

    if connect: connect_channel(chid)
    poll()
    time.sleep(1.e-5)
    return chid

@withCHID
def connect_channel(chid, timeout=None, verbose=False, force=True):
    """ wait (up to timeout) until a chid is connected

    Normally, channels will connect very fast, and the
    connection callback will succeed the first time.

    For un-connected Channels (that are nevertheless queried),
    the 'ts' (timestamp of last connecion attempt) and
    'failures' (number of failed connection attempts) from
    the _cache will be used to prevent spending too much time
    waiting for a connection that may never happen.
    
    """
    conn = (state(chid) == dbr.CS_CONN)
    if conn:
        return conn

    start_time = time.time()
    pvname = name(chid)
    ctx = current_context()
    if ctx not in _cache: _cache[ctx] = {}
    tdelta = start_time - _cache[ctx][name(chid)]['ts']
    # avoid repeatedly trying to connect to unavailable PV
    nfail = min(20,  1 + _cache[ctx][name(chid)]['failures'])
    if force:
        nfail = min(2, nfail)
    if tdelta < nfail * DEFAULT_CONNECTION_TIMEOUT:
        return conn

    if timeout is None:
        timeout = DEFAULT_CONNECTION_TIMEOUT
    while (not conn and (time.time()-start_time <= timeout)):
        poll()
        conn = (state(chid) == dbr.CS_CONN)
    if verbose:
        sys.stdout.write('connected in %.3f s\n' % ( time.time()-start_time))
    if not conn:
        _cache[ctx][name(chid)]['ts'] = time.time()
        _cache[ctx][name(chid)]['failures'] += 1
    return conn

# common functions with similar signatures
@withCHID
def _chid_f(chid, fcn_name, restype=int, arg=None):
    fcn = getattr(libca, fcn_name)
    if arg is not None:
        fcn.argtypes = arg
    fcn.restype = restype
    return fcn(chid)

def name(chid):
    "channel name"
    return bytes2str(_chid_f(chid, 'ca_name', restype=ctypes.c_char_p))

def host_name(chid):
    return bytes2str(_chid_f(chid, 'ca_host_name',
                             restype=ctypes.c_char_p))

def element_count(chid):
    return _chid_f(chid, 'ca_element_count')

def read_access(chid):
    return _chid_f(chid, 'ca_read_access')

def write_access(chid):
    return _chid_f(chid, 'ca_write_access')

def field_type(chid):
    return _chid_f(chid, 'ca_field_type')

def clear_channel(chid):
    return _chid_f(chid, 'ca_clear_channel')

@withCHID
def state(chid):
    return libca.ca_state(chid)

@withCHID
def isConnected(chid):
    "return whether channel is connected"
    return dbr.CS_CONN == state(chid)

@withCHID
def access(chid):
    "string description of access"
    acc = read_access(chid) + 2 * write_access(chid)
    return ('no access', 'read-only', 'write-only', 'read/write')[acc]

@withCHID
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

def _unpack(data, count, ftype=dbr.INT, as_numpy=True):
    """unpack raw data returned from an array get or
    subscription callback"""

    def unpack_simple(data, ntype):
        if count == 1 and ntype != dbr.STRING:
            return data[0]
        out = data
        if ntype == dbr.STRING:
            out = strjoin('', out).rstrip()
            if '\x00' in out:
                out = out[:out.index('\x00')]
        return out

    def unpack_ctrltime(data, ntype):
        if count == 1 or ntype == dbr.STRING:
            out = data[0].value
            if ntype == dbr.STRING and '\x00' in out:
                out = out[:out.index('\x00')]
            return out
        out = [i.value for i in data]
        return out

    ntype = ftype
    unpack = unpack_simple
    if ftype >= dbr.TIME_STRING:
        unpack = unpack_ctrltime
    if ftype == dbr.CTRL_STRING:
        ftype = dbr.TIME_STRING

    if ftype > dbr.CTRL_STRING:
        ntype -= dbr.CTRL_STRING
    elif ftype >= dbr.TIME_STRING:
        ntype -= dbr.TIME_STRING

    out = unpack(data, ntype)
    if (HAS_NUMPY and as_numpy and
        count > 1 and ntype != dbr.STRING):
        out = numpy.array(out)
    return out

@withConnectedCHID
def get(chid, ftype=None, as_string=False, as_numpy=True):
    """return the current value for a Channel.  Options are
       ftype       field type to use (native type is default)
       as_string   flag(True/False) to get a string representation
                   of the value returned.  This is not nearly as
                   featured as for a PV -- see pv.py for more details.
       as_numpy    flag(True/False) to use numpy array as the
                   return type for array data.       
    
    """
    if ftype is None:
        ftype = field_type(chid)
    count = element_count(chid)

    nelem = count
    if ftype == dbr.STRING:
        nelem = dbr.MAX_STRING_SIZE
       
    data = (nelem*dbr.Map[ftype])()
    
    ret = libca.ca_array_get(ftype, count, chid, data)
    PySEVCHK('get', ret)
    poll()
    val = _unpack(data, nelem, ftype=ftype, as_numpy=as_numpy)
    if as_string:
        val = __as_string(val, chid, count, ftype)
    return val

def __as_string(val, chid, count, ftype):
    "primitive conversion of value to a string"
    try:
        if ftype == dbr.CHAR:
            val = strjoin('',   [chr(i) for i in val if i>0]).strip()
        elif ftype == dbr.ENUM and count == 1:
            val = get_enum_strings(chid)[val]
        elif count > 1:
            val = '<array count=%d, type=%d>' % (count, ftype)
        val = str(val)
    except StandardError:
        pass            
    return val
                    
@withConnectedCHID
def put(chid, value, wait=False, timeout=20, callback=None,
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
            tname  = dbr.Name(ftype).lower()
            raise ChannelAccessException('put', \
                                         errmsg % (repr(value),tname))
    else:
        # auto-convert strings to arrays for character waveforms
        # could consider using
        # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value, str):
            pad = '\x00'*(1+count-len(value))
            value = [ord(i) for i in ("%s%s" % (value, pad))[:count]]
        try:
            ndata, nuser = len(data), len(value)
            if nuser > ndata:
                value = value[:ndata]
            data[:len(value)] = list(value)
        except (ValueError, IndexError):
            errmsg = "Cannot put array data to PV of type '%s'"            
            raise ChannelAccessException('put', errmsg % (repr(value)))
      
    # simple put, without wait or callback
    if not (wait or hasattr(callback, '__call__')):
        ret =  libca.ca_array_put(ftype, count, chid, data)
        PySEVCHK('put', ret)
        poll()
        return ret
    # wait with wait or callback    # wait with wait or callback
    pvname = name(chid)
    _put_done[pvname] = (False, callback, callback_data)
    ret = libca.ca_array_put_callback(ftype, count, chid,
                                      data, _CB_putwait, 0)
    PySEVCHK('put', ret)
    if wait:
        time0, finished = time.time(), False
        while not finished:
            poll()
            finished = (_put_done[pvname][0] or
                        (time.time()-time0) > timeout)
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
            out[attr] = getattr(tmpv, attr)
    if (hasattr(tmpv, 'strs') and hasattr(tmpv, 'no_str') and
        tmpv.no_str > 0):
        out['enum_strs'] = tuple([bytes2str(tmpv.strs[i].value)
                                  for i in range(tmpv.no_str)])
    return out

@withConnectedCHID
def get_timevars(chid):
    """return the TIME fields for a Channel.  Depending on 
    the native type, these fields may include
        status  severity timestamp
    """
    ftype = promote_type(chid, use_time=True)
    d = (1*dbr.Map[ftype])()
    ret = libca.ca_array_get(ftype, 1, chid, d)
    PySEVCHK('get_timevars', ret)
    poll()
    kw = {}
    v = d[0]
    for attr in ('status', 'severity', 'timestamp'):
        if hasattr(v, attr):
            kw[attr] = getattr(v, attr)
    return kw

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

@withConnectedCHID
def create_subscription(chid, use_time=False, use_ctrl=False,
                        mask=7, userfcn=None):
    """
    setup a callback function to be called when a PVs value or state changes.

    Important Note:
        KEEP The returned tuple in named variable: if the return argument
        gets garbage collected, a coredump will occur.
    
    """
    ftype = promote_type(chid, use_ctrl=use_ctrl, use_time=use_time)
    count = element_count(chid)

    cb    = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onGetEvent)   
    uarg  = ctypes.py_object(userfcn)
    evid  = ctypes.c_void_p()
    poll()
    ret = libca.ca_create_subscription(ftype, count, chid, mask,
                                       cb, uarg, ctypes.byref(evid))
    PySEVCHK('create_subscription', ret)
    
    poll()
    return (cb, uarg, evid)

@withCA
@withSEVCHK
def clear_subscription(evid):
    "cancel subscription"
    return libca.ca_clear_subscription(evid)

##
## Event Handlers for get() event callbacks
def _onGetEvent(args):
    """Internal Event Handler for get events: not intended for use"""
    value = dbr.Cast(args).contents
    kwd = {'ftype':args.type, 'count':args.count,
           'chid':args.chid, 'pvname': name(args.chid),
           'status':args.status}

    # add kwd arguments for CTRL and TIME variants
    if args.type >= dbr.CTRL_STRING:
        tmpv = value[0]
        for attr in dbr.ctrl_limits + ('precision', 'units', 'severity'):
            if hasattr(tmpv, attr):        
                kwd[attr] = getattr(tmpv, attr)
        if (hasattr(tmpv, 'strs') and hasattr(tmpv, 'no_str') and
            tmpv.no_str > 0):
            kwd['enum_strs'] = tuple([tmpv.strs[i].value for 
                                      i in range(tmpv.no_str)])

    elif args.type >= dbr.TIME_STRING:
        tmpv = value[0]
        kwd['status']    = tmpv.status
        kwd['severity']  = tmpv.severity
        kwd['timestamp'] = (dbr.EPICS2UNIX_EPOCH + tmpv.stamp.secs + 
                            1.e-6*int(tmpv.stamp.nsec/1000.00))
    nelem = args.count
    if args.type in (dbr.STRING, dbr.TIME_STRING, dbr.CTRL_STRING):
        nelem = dbr.MAX_STRING_SIZE

    value = _unpack(value, nelem, ftype=args.type)
    if hasattr(args.usr, '__call__'):
        args.usr(value=value, **kwd)

## connection event handler: 
def _onConnectionEvent(args):
    """set flag in cache holding whteher channel is
    connected. if provided, run a user-function"""
    pvname = name(args.chid)
    if args.op != dbr.OP_CONN_UP:
        return
    try:
        ctx = current_context()
        if ctx not in _cache:
            _cache[ctx] = {}
        entry  = _cache[ctx][pvname]
    except KeyError:
        return
    # print 'Conn Event ', pvname, entry
    entry['conn'] = (args.op == dbr.OP_CONN_UP)
    entry['ts']   = time.time()
    entry['failures'] = 0
    try:
        if hasattr(entry['userfcn'], '__call__'):
            entry['userfcn'](pvname=pvname,
                             chid=entry['chid'],
                             conn=entry['conn'])
    except:
        errmsg = "Error Setting User Callback for '%s'"  % pvname
        raise ChannelAccessException('Connect', errmsg)

    return 

## put event handler:
def _onPutEvent(args, *varargs):
    """set put-has-completed for this channel,
    call optional user-supplied callback"""
    pvname  = name(args.chid)
    userfcn = _put_done[pvname][1]
    userdata = _put_done[pvname][2]
    _put_done[pvname] = (True, None, None)
    if hasattr(userfcn, '__call__'):
        userfcn(pvname=pvname, data=userdata)

# create global reference to these two callbacks
_CB_connect = ctypes.CFUNCTYPE(None, dbr.connection_args)(_onConnectionEvent)
_CB_putwait = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onPutEvent)  


## Synchronous groups
@withCA
@withSEVCHK
def sg_block(gid, timeout=10.0):
    "sg block"
    fcn   = libca.ca_sg_block
    fcn.argtypes = [ctypes.c_ulong, ctypes.c_double]
    return fcn(gid, timeout)

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

def sg_get(gid, chid, ftype=None, as_string=False, as_numpy=True):
    """synchronous-group get of the current value for a Channel.
    same options as get()
    """
    if not isinstance(chid, ctypes.c_long):
        raise ChannelAccessException('sg_get', "not a valid chid!")

    if ftype is None:
        ftype = field_type(chid)
    count = element_count(chid)

    nelem = count
    if ftype == dbr.STRING:
        nelem = dbr.MAX_STRING_SIZE
    
    data = (nelem*dbr.Map[ftype])()
   
    ret = libca.ca_sg_array_get(gid, ftype, count, chid, data)
    PySEVCHK('sg_get', ret)

    poll()
    val = _unpack(data, nelem, ftype=ftype, as_numpy=as_numpy)
    if as_string:
        val = __as_string(val, chid, count, ftype)
    return val

def sg_put(gid, chid, value):
    """synchronous-group put: cannot wait or get callback!"""
    if not isinstance(chid, ctypes.c_long):
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
            tname   = dbr.Name(ftype).lower()
            raise ChannelAccessException('put', \
                                         errmsg % (repr(value),tname))
    else:
        # auto-convert strings to arrays for character waveforms
        # could consider using
        # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value, str):
            pad = '\x00'*(1+count-len(value))
            value = [ord(i) for i in ("%s%s" % (value, pad))[:count]]
        try:
            ndata = len(data)
            nuser = len(value)
            if nuser > ndata:
                value = value[:ndata]
            data[:len(value)] = list(value)
        except:
            errmsg = "Cannot put array data to PV of type '%s'"            
            raise ChannelAccessException('put', errmsg % (repr(value)))
      
    ret =  libca.ca_sg_put(gid, ftype, count, chid, data)
    PySEVCHK('sg_put', ret)
    poll()
    return ret

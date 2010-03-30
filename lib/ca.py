#!usr/bin/env python
#
# low level support for Epics Channel Access
#
"""
EPICS Channel Access Interface

See doc/ for documentation
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
except ImportError:
    has_numpy = False

from . import dbr

def get_strwrapper():
    """create string wrapper to pass to C functions  for both Python2 and Python3"""
    if sys.version_info[0] == 3:
        return lambda x:  bytes(x,'ASCII')
    return str
strwrapper = get_strwrapper()

def strjoin(sep, seq):
   return strwrapper(sep).join(seq)
    
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
        self.fcn = fcn
        self.msg = msg
    def __str__(self):
        return " %s returned '%s'" % (self.fcn,self.msg)

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
        raise ChannelAccessException('initialize_libca',
                                     'Cannot create Epics CA Context')

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
        for key,val in list(_cache.items()):
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


def show_cache(print_out=True):
    """Show list of cached PVs"""
    o = []
    o.append('#  PV name    Is Connected?   Channel ID')
    o.append('#---------------------------------------')
    for name,val in list(_cache.items()):
        o.append(" %s   %s     %s " % (name,
                                       repr(val['conn']),
                                       repr(val['chid'])))
    o = strjoin('\n', o)
    if print_out:
        sys.stdout.write("%s\n" % o)
    else:
        return o

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
                raise ChannelAccessException(fcn.__name__,
                                             "not a valid chid!")
        return fcn(*args,**kw)
    return wrapper


def withConnectedCHID(fcn):
    """decorator to ensure that first argument to a function is a
    chid that is actually connected. This will attempt to connect
    if needed."""
    def wrapper(*args,**kw):
        if len(args)>0:
            if not isinstance(args[0],ctypes.c_long):
                raise ChannelAccessException(fcn.__name__, "not a valid chid!")
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
                raise ChannelAccessException(fcn.__name__, "channel cannot connect")
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
    pvn = strwrapper(pvname)    
    ret = libca.ca_create_channel(pvn, _CB_connect,0,0,ctypes.byref(chid))
    PySEVCHK('create_channel',ret)
    
    _cache[pvn] = {'chid':chid, 'conn':False, 'ts':0, 'failures':0,
                      'userfcn': userfcn}
    if connect: connect_channel(chid)
    poll()
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
        sys.stdout.write('connected in %.3f s\n' % ( time.time()-t0))
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
            out = strjoin('', out).rstrip()
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
            val = strjoin('',   [chr(i) for i in val if i>0]).strip()
        elif ftype==dbr.ENUM and count==1:
            val = get_enum_strings(chid)[val]
        elif count > 1:
            val = '<array count=%d, type=%d>' % (count,ftype)
        val = str(val)
    except:
        pass            
    return val
                    
@withConnectedCHID
def put(chid,value, wait=False, timeout=20, callback=None,
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
            tname   = dbr.Name(ftype).lower()
            raise ChannelAccessException('put',\
                                         errmsg % (repr(value),tname))
    else:
        # auto-convert strings to arrays for character waveforms
        # could consider using
        # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value,str):
            pad = '\x00'*(1+count-len(value))
            value = [ord(i) for i in ("%s%s" % (value,pad))[:count]]
        try:
            ndata = len(data)
            nuser = len(value)
            if nuser > ndata: value = value[:ndata]
            data[:len(value)] = list(value)
        except (ValueError,IndexError):
            errmsg = "Cannot put array data to PV of type '%s'"            
            raise ChannelAccessException('put',errmsg % (repr(value)))
      
    # simple put, without wait or callback
    if not (wait or hasattr(callback,'__call__')):
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
        status  severity precision  units  enum_strs
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
    for attr in ('precision','units', 'severity', 'status',
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
    """
    setup a callback function to be called when a PVs value or state changes.

    Important Note:
        KEEP The returned tuple in named variable: if the return argument
        gets garbage collected, a coredump will occur.
    
    """
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
    if hasattr(args.usr,'__call__'):
        args.usr(value=value, **kw)

## connection event handler: 
def _onConnectionEvent(args):
    """set flag in cache holding whteher channel is
    connected. if provided, run a user-function"""
    pvname = name(args.chid)

    if args.op != dbr.OP_CONN_UP:  return
    try:
        entry  = _cache[pvname]
    except KeyError:
        return
    entry['conn'] = (args.op == dbr.OP_CONN_UP)
    entry['ts']   = time.time()
    entry['failures'] = 0
    try:
        if hasattr(entry['userfcn'],'__call__'):
            entry['userfcn'](pvname=pvname,
                             chid=entry['chid'],
                             conn=entry['conn'])
    except:
        errmsg = "Error Setting User Callback for '%s'"  % pvname
        raise ChannelAccessException('Connect',errmsg)
    return 

## put event handler:
def _onPutEvent(args,*varargs):
    """set put-has-completed for this channel,
    call optional user-supplied callback"""
    pvname = name(args.chid)
    userfcn   = _put_done[pvname][1]
    userdata = _put_done[pvname][2]
    _put_done[pvname] = (True,None,None)
    if hasattr(userfcn,'__call__'):
        userfcn(pvname=pvname, data=userdata)

# create global reference to these two callbacks
_CB_connect = ctypes.CFUNCTYPE(None, dbr.connection_args)(_onConnectionEvent)
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
            name   = dbr.Name(ftype).lower()
            raise ChannelAccessException('put',\
                                         errmsg % (repr(value),name))
    else:
        # auto-convert strings to arrays for character waveforms
        # could consider using
        # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value,str):
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



#!/usr/bin/env python
#
# low level support for Epics Channel Access
#
""" EPICS Channel Access Interface

Overview
========

This provides a ctypes-based wrapping of EPICS Channel Access.

The

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

# holder for DLL
libca = None

# PREEMPTIVE_CALLBACK determines how
PREEMPTIVE_CALLBACK = True
# PREEMPTIVE_CALLBACK = False

## default timeout for connection
#  This should be kept fairly short --
#  connection will be tried repeatedly
DEFAULT_CONNECTION_TIMEOUT = 5.0

## Cache of existing channel IDs:
##  pvname: {'chid':chid, 'conn': isConnected,
##           'ts': ts_conn, 'userfcn': user_callback)
##  isConnected   = True/False: if connected.
##  ts_conn       = ts of last connection event or failed attempt.
##  user_callback = user function to be called on change
_cache  = {}

## Cache of pvs waiting for put to be done.
_put_done =  {}
        
class ChannelAccessException(Exception):
    """Channel Access Exception"""
    def __init__(self, fcn, message):
        self.fcn = fcn
        self.msg = message
    def __str__(self):
        return " %s returned '%s'" % (self.fcn,self.msg)

def initialize_libca():
    """ load DLL (shared object library) to establish Channel Access Connection.
 the value of PREEMPTIVE_CALLBACK sets the pre-emptive callback  model:
    False   no preemptive callbacks. pend_io/pend_event must be used.
    True    preemptive callbaks will be done.
 Returns libca where 
   libca        = ca library object, used for all subsequent ca calls

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
        raise ChannelAccessException('initialize_libca', 'Cannot create Epics CA Context')
    return libca

# 
def finalize_libca(maxtime=10.0):
    """shutdown channel access:
    run clear_channel(chid) for all chids in _cache
    then flush_io() and poll() a few times.
    """
    t0 = time.time()
    flush_io()
    poll()

    for val in _cache.values():  clear_channel(val['chid'])
    _cache.clear()

    for i in range(10):
        flush_io()
        poll(1.e-5,10.0)
        if time.time()-t0 > maxtime: break

    context_destroy()
    libca = None
    gc.collect()
    # print 'shutdown in %.3fs' % (time.time()-t0)

# now register this function to be run on normal exits
atexit.register(finalize_libca)

# connection events: 
def _onConnectionEvent(args):
    """set flag in cache holding whteher channel is connected.
    if provided, run a user-function"""
    pvname = name(args.chid)
    entry = _cache[pvname]
    entry['conn'] = (args.op == dbr.OP_CONN_UP)
    entry['ts']   = time.time()
    entry['failures'] = 0
    if callable(entry['userfcn']):
        entry['userfcn'](pvname=pvname,
                         chid=entry['chid'],
                         conn=entry['conn'])
    return 

# hold global reference to this callback
_CB_connect = ctypes.CFUNCTYPE(None,dbr.ca_connection_args)(_onConnectionEvent)

# put events
def _onPutEvent(args,*varargs):
    """set put-has-completed for this channel,
    call optional user-supplied callback
    """
    pvname = name(args.chid)
    userfcn = _put_done[pvname][1]
    if callable(userfcn): userfcn()
    _put_done[pvname] = (True,None)

# hold global reference to this callback
_CB_putwait  = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onPutEvent)   


def show_cache():
    """Show list of cached PVs
    """
    print '  PV name    Is Connected?   Channel ID'
    print '---------------------------------------'
    for name,val in _cache.items():
        print " %s   %s     %s " % (name,
                                    repr(val['conn']),
                                    repr(val['chid']))

###
# 3 decorator functions for ca functionality:
#    decorator name     ensures before running decorated function:
#    --------------     -----------------------------------------------
#    withCA               libca is initialized 
#    withCHID             (crudely) that the 1st arg is a chid (c_long)
#    withConnectedCHID    1st arg is a connected chid.
###

def withCA(fcn):
    """decorator to ensure that libca and a context are created prior to
    any function calls to the channel access library.

    Note that C functions that take a Channel ID (chid) are not wrapped, as
    the library must have beeni nitialized to produce the chid in the first
    place. """
    def wrapper(*args,**kw):
        global libca
        if libca is None:   libca = initialize_libca()
        return fcn(*args,**kw)
    return wrapper

def withCHID(fcn):
    """decorator to ensure that first argument to a function is a chid"""
    def wrapper(*args,**kw):
        if len(args)>0:
            if not isinstance(args[0],(ctypes.c_long,int)):
                raise ChannelAccessException(fcn.func_name, "not a valid chid!")
        return fcn(*args,**kw)
    return wrapper


def withConnectedCHID(fcn):
    """decorator to ensure that first argument to a function is a
    chid that is actually connected"""
    def wrapper(*args,**kw):
        if len(args)>0:
            if not isinstance(args[0],ctypes.c_long):
                raise ChannelAccessException(fcn.func_name, "not a valid chid!")
            if (state(args[0]) != dbr.CS_CONN):
                t = kw.get('timeout',DEFAULT_CONNECTION_TIMEOUT)
                connect_channel(args[0],timeout=t,force=False)
            if (state(args[0]) != dbr.CS_CONN):
                raise ChannelAccessException(fcn.func_name, "channel cannot connect")
        return fcn(*args,**kw)
    return wrapper

def raise_on_ca_error(fcn):
    """decorator to raise a ChannelAccessException if the wrapped
    ca function does not return status=ECA_NORMAL
    """
    def wrapper(*args,**kw):
        status = fcn(*args,**kw)
        if status != dbr.ECA_NORMAL:
            raise ChannelAccessException(fcn.func_name,message(status))
        return 
    return wrapper


# contexts
@withCA
def context_create(context=0): return libca.ca_context_create(context)

@withCA
def context_destroy():         return libca.ca_context_destroy()
    
@withCA
def attach_context(context):   return  libca.ca_attach_context(context)

@withCA
def detach_context():          return libca.ca_detach_context()

@withCA
def current_context():
    f = libca.ca_current_context
    f.restype = ctypes.c_void_p
    return f()


@withCA
def client_status(context,level):
    f = libca.ca_client_status
    f.argtypes = (ctypes.c_void_p,ctypes.c_long)
    return libca.ca_client_status(context,level)

@withCA
def flush_io():    return libca.ca_flush_io()

def pend_io(t=1.0):
    f   = libca.ca_pend_io
    f.argtypes = [ctypes.c_double]
    return f(t)

def pend_event(t=1.e-5):
    f   = libca.ca_pend_event
    f.argtypes = [ctypes.c_double]
    return f(t)

def poll(ev=1.e-4,io=1.0):
    """polls CA for events and i/o.

    Note that this also does a very short time.sleep()
    The GIL is thus released several times here.
    """
    pend_event(ev)
    pend_io(io)    
    time.sleep(1.e-6)


@withCA
def create_channel(pvname,connect=False,userfcn=None):
    """ create a channel for a pvname
    connect=True will try to wait until connection is complete
    before returning

    a user function (userfcn) can be provided as a connection callback,
      called with (chid=chid) argument when connection state changes.
    """
    chid = ctypes.c_long()

    libca.ca_create_channel(pvname,_CB_connect,0,0,ctypes.byref(chid))
    _cache[pvname] = {'chid':chid, 'conn':False,
                      'ts':0, 'failures':0,
                      'userfcn': userfcn}
    if connect: connect_channel(chid)
    return chid

@withCHID
def _chid_f(chid,fcn_name,restype=int,arg=None):
    f = getattr(libca,fcn_name)
    if arg is not None:   f.argtypes = arg
    f.restype = restype
    return f(chid)

def name(chid):          return _chid_f(chid,'ca_name',      restype=ctypes.c_char_p)
def host_name(chid):     return _chid_f(chid,'ca_host_name', restype=ctypes.c_char_p)
def element_count(chid): return _chid_f(chid,'ca_element_count')
def read_access(chid):   return _chid_f(chid,'ca_read_access')
def write_access(chid):  return _chid_f(chid,'ca_write_access')
def field_type(chid):    return _chid_f(chid,'ca_field_type')
def clear_channel(chid): return _chid_f(chid,'ca_clear_channel')

@withCHID
def state(chid):         return libca.ca_state(chid)

@withCHID
def isConnected(chid):   return dbr.CS_CONN==state(chid)

@withCA
def message(status):
    f = libca.ca_message
    f.restype = ctypes.c_char_p
    return f(status)

def dbrName(t): return dbr.Name(t)

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

def _unpack(data, count, ftype=dbr.INT,as_numpy=True):
    """ unpack raw data returned from an array get or
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
    if ftype is None: ftype = field_type(chid)
    count = element_count(chid)

    nelem = count
    if ftype == dbr.STRING:  nelem = dbr.MAX_STRING_SIZE
       
    rawdata = (nelem*dbr.Map[ftype])()
    
    ret = libca.ca_array_get(ftype, count, chid, rawdata)
    poll()
    val = _unpack(rawdata,nelem,ftype=ftype,as_numpy=as_numpy)
    if as_string and ftype==dbr.CHAR:
        val = ''.join([chr(i) for i in s if i>0]).strip().rstrip()

    return val
    
@withConnectedCHID
def put(chid,value, wait=False, timeout=20, callback=None):
    """put,with optional wait and user-defined callback
    returns 1 on sucess and -1 on timed-out
    """
    ftype = field_type(chid)
    count = element_count(chid)
    data  = (count*dbr.Map[ftype])()    

    if count == 1:
        data[0] = value
    else:
        # auto-convert strings to data arrays for character waveforms
        # could consider using???
        # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],
        #                  dtype=numpy.uint8)
        if ftype == dbr.CHAR and isinstance(value,(str,unicode)):
            pad = '\x00'*(1+count-len(value))
            value = [ord(i) for i in ("%s%s" % (value,pad))[:count]]
        data[:]  = list(value)
      
    if wait or callable(callback):
        pvname= name(chid)
        _put_done[pvname] = (False,callback)
        poll()
        ret = libca.ca_array_put_callback(ftype,count,chid,
                                          data, _CB_putwait, 0)
        if wait:
            t0 = time.time()
            ret = -1
            while time.time()-t0 <timeout:
                time.sleep(1.e-4)
                poll()
                if _put_done[pvname][0]:
                    ret = 1
                    break
    else:
        ret =  libca.ca_array_put(ftype,count,chid, rawdata)
    poll()
    return ret

@withConnectedCHID
def get_ctrlvars(chid):
    """return the CTRL fields for a PV """
    ftype = promote_type(chid, use_ctrl=True)
    d = (1*dbr.Map[ftype])()
    ret = libca.ca_array_get(ftype, 1, chid, d)
    d = d[0]
    poll(5.e-3,1.0)
    kw = {}
    if ret == dbr.ECA_NORMAL: 
        for attr in ('severity', 'timestamp', 'precision','units', 
                     'upper_disp_limit', 'lower_disp_limit',
                     'upper_alarm_limit', 'upper_warning_limit',
                     'lower_warning_limit','lower_alarm_limit',
                     'upper_ctrl_limit', 'lower_ctrl_limit'):
            if hasattr(d,attr): kw[attr] = getattr(d,attr)
        if hasattr(d,'strs') and hasattr(d,'no_str'):
            if d.no_str > 0:
                kw['enum_strs'] = [d.strs[i].value for i in range(d.no_str)]
    return kw

def get_precision(chid):
    if field_type(chid) in (dbr.FLOAT,dbr.DOUBLE):
        k = get_ctrlvars(chid)
        return k.get('precision',None)
    return 0

def get_enum_strings(chid):
    if field_type(chid) == dbr.ENUM:
        kw = get_ctrlvars(chid)
        return kw.get('enum_strs',None)
    return None

##
## Event Handlers for get() event callbacks
def _onGetEvent(args):
    value = dbr.Cast(args).contents

    kw = {'ftype':args.type,'count':args.count,
          'chid':args.chid, 'status':args.status}

    # add kw arguments for CTRL and TIME variants
    if args.type >= dbr.CTRL_STRING:
        v0 = value[0]
        for attr in dbr.ctrl_limits + ('no_str','precision','units'):
            if hasattr(v0,attr):        
                kw[attr] = getattr(v0,attr)
        if hasattr(v0,'strs'):
            s = [v0.strs[i].value for i in range(v0.no_str)]
            kw['enum_strs'] = tuple(s)

    elif args.type >= dbr.TIME_STRING:
        v0 = value[0]
        kw['status']    = v0.status
        kw['severity']  = v0.severity
        kw['timestamp'] = (dbr.EPICS2UNIX_EPOCH +
                           v0.stamp.nsec*1.e-9* +
                           v0.stamp.secs)

    nelem = args.count
    if args.type in (dbr.STRING,dbr.TIME_STRING,dbr.CTRL_STRING):
        nelem = dbr.MAX_STRING_SIZE

    value = _unpack(value, nelem, ftype=args.type)

    if callable(args.usr):
        args.usr(value=value, **kw)

@withConnectedCHID
def create_subscription(chid, use_time=False,use_ctrl=False,
                        callback=None, mask=7, userfcn=None):

    ftype = promote_type(chid, use_ctrl=use_ctrl,use_time=use_time)
    count = element_count(chid)

    cb    = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onGetEvent)   
    uarg  = ctypes.py_object(userfcn)

    evid  = ctypes.c_void_p()
    poll()
    ret = libca.ca_create_subscription(ftype, count, chid, mask,
                                       cb, uarg, ctypes.byref(evid))
    poll(1.e-3,1.0)
    return (cb, uarg, evid, ret)

subscribe = create_subscription
def clear_subscription(evid): return libca.ca_clear_subscription(evid)

##
## several methods are not yet implemented:

def dump_dbr(type,count,data):
    return libca.ca_dump_dbr(type,count, data)

def add_exception_event(): return libca.ca_add_exception_event()

def add_fd_registration(): return libca.ca_add_fd_registration()


def client_status(): return libca.ca_client_status()

def replace_access_rights_event(): return libca.ca_replace_access_rights_event()
def replace_printf_handler(): return libca.ca_replace_printf_handler()

def puser(): return libca.ca_puser()
def set_puser(): return libca.ca_set_puser()
def signal(): return libca.ca_signal()
def sg_block(): return libca.ca_sg_block()
def sg_create(): return libca.ca_sg_create()
def sg_delete(): return libca.ca_sg_delete()
def sg_array_get(): return libca.ca_sg_array_get()
def sg_array_put(): return libca.ca_sg_array_put()
def sg_reset(): return libca.ca_sg_reset()
def sg_test(): return libca.ca_sg_test()

def test_event(): return libca.ca_test_event()
def test_io(): return libca.ca_test_io()
def dbr_size(): return libca.dbr_size()
def dbr_value_size(): return libca.dbr_value_size()

def size_n(): raise NotImplementedError
def channel_state(): raise NotImplementedError

def SEVCHK(): raise NotImplementedError


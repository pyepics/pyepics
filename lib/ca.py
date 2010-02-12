#!/usr/bin/env python
#
# low level support for Epics Channel Access
import ctypes
import sys
import os
import time
try:
    import numpy
    has_numpy = True
except:
    has_numpy = False


import dbr

libca = None
preemptive_callback = True
# preemptive_callback = False

## Cache of existing channel IDs:
##  pvname: {chid, isConnected, connection_callback)
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
 Returns libca

 where 
   libca        = ca library object, used as class for all
                  subsequent ca calls

 Note that this function must be called prior to any real ca calls.
    """
    load_dll = ctypes.cdll.LoadLibrary
    dllname  = 'libca.so'
    path_sep = ':'
    os_path  = os.environ['PATH']
    if os.name == 'nt':
        load_dll = ctypes.windll.LoadLibrary
        dllname  = 'ca.dll'
        path_sep = ';'
        path_dirs = os.environ['PATH'].split(path_sep)
        for p in (sys.prefix,
                  os.path.join(sys.prefix,'DLLs')):
            path_dirs.insert(0,p)
        os.environ['PATH'] = ';'.join(path_dirs)


    libca = load_dll(dllname)
    ca_context = {False:0, True:1}[preemptive_callback]
    ret = libca.ca_context_create(ca_context)
    if ret != dbr.ECA_NORMAL:
        raise ChannelAccessException('initialize_libca', 'Cannot create Epics CA Context')
    return libca

#
# 3 decorator functions for ca functionality:
#  decorator name     ensures before running decorated function:
#  --------------     -----------------------------------------------
#  withCA               libca is initialized 
#  withCHID             (crudely) that the 1st arg is a chid (c_long)
#  withConnectedCHID    1st arg is a connected chid.
#############

def withCA(fcn):
    """decorator to ensure that libca and a context are created prior to
    any function calls to the channel access library.

    Note that C functions that take a Channel ID (chid) are not wrapped, as
    the library must have beeni nitialized to produce the chid in the first
    place. """
    def wrapper(*args,**kw):
        global libca
        if libca is None:
            libca = initialize_libca()
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
    """decorator to ensure that first argument to a function is a chid that is connected"""
    def wrapper(*args,**kw):
        if len(args)>0:
            if not isinstance(args[0],ctypes.c_long):
                raise ChannelAccessException(fcn.func_name, "not a valid chid!")
            if (state(args[0]) != dbr.CS_CONN):
                t = kw.get('timeout',30)
                connect_channel(args[0],timeout=t)
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

# 
def shutdown(maxtime=10.0):
    """ carefully shutdown channel access:
    run clear_channel(chid) for all chids in _cache
    then flush_io() and poll() a few times.
    """
    t0 = time.time()
    flush_io()
    poll()

    for val in _cache.values():
        clear_channel(val[0])
    _cache.clear()
    
    for i in range(10):
        time.sleep(1.e-3)
        flush_io()
        poll(1.e-5,10.0)
        if time.time()-t0 > maxtime: break
    
    # print 'shutdown in %.3fs' % (time.time()-t0)

# contexts
@withCA
def context_create(context=0):
    return libca.ca_context_create(context)

@withCA
def context_destroy():
    return libca.ca_context_destroy()

@withCA
def pend_io(t=1.0):
    f   = libca.ca_pend_io
    f.argtypes = [ctypes.c_double]
    return f(t)

@withCA
def pend_event(t=1.e-5):
    f   = libca.ca_pend_event
    f.argtypes = [ctypes.c_double]
    return f(t)

@withCA
def flush_io():
    return libca.ca_flush_io()

@withCA
def poll(ev=1.e-4,io=1.0):
    pend_event(ev)
    pend_io(io)    
    time.sleep(ev)
    
@withCA
def current_context():
    f = libca.ca_current_context
    f.restype = ctypes.c_void_p
    return f()

@withCA
def attach_context(context):
    return  libca.ca_attach_context(context)

@withCA
def detach_context():
    return libca.ca_detach_context()

@withCA
def client_status(context,level):
    f = libca.ca_client_status
    f.argtypes = (ctypes.c_void_p,ctypes.c_long)
    return libca.ca_client_status(context,level)


# connection events: 
def _onConnectionEvent(args):
    """set flag in cache holding whteher channel is connected.
    if provided, run a user-function"""
    entry = _cache[name(args.chid)]
    entry[1] = (args.op == dbr.OP_CONN_UP)
    if callable(entry[2]):  entry[2](chid=args.chid)
    return 

# hold global reference to this callback
_CB_connect = ctypes.CFUNCTYPE(None, dbr.ca_connection_args)(_onConnectionEvent)

# put events
def _onPutEvent(args,*varargs):
    """ set put-is-done for this channel"""
    _put_done[name(args.chid)] = True

# hold global reference to this callback
_CB_putwait  = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(_onPutEvent)   


def show_cache():
    print '  PV name    Is Connected?   Channel ID'
    print '---------------------------------------'
    for name,val in _cache.items():
        print " %s   %s     %s " % (name, repr(val[1]), val[0])


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
    _cache[pvname] = [chid,False,userfcn]
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
    if use_ctrl:
        ftype += (dbr.CTRL_STRING - dbr.STRING)
    elif use_time:
        ftype += (dbr.TIME_STRING - dbr.STRING)

    if ftype == dbr.CTRL_STRING: ftype = dbr.TIME_STRING
    return ftype


@withCHID
def connect_channel(chid,timeout=10.0,verbose=False):
    """ wait (up to timeout) until a chid is connected"""
    conn = (state(chid)==dbr.CS_CONN)
    t0 = time.time()
    while (not conn and (time.time()-t0 <= timeout)):
        poll()
        conn = (state(chid)==dbr.CS_CONN)
    if verbose:
        print 'connected in %.3f s' % ( time.time()-t0 )
    return conn

def _unpack_val(data, count, ftype=dbr.INT,as_numpy=True):
    """ unpack raw data returned from an array get or subscription callback"""

    def unpack_simple(data):
        if count == 1:    return data[0]
        out = [i for i in data]
        if ntype == dbr.STRING:
            out = ''.join(out).rstrip()
        elif has_numpy and as_numpy:
            out = numpy.array(out)
        return out

    def unpack_ctrltime(data):
        if count == 1 or ntype == dbr.STRING:
            return data[0].value
        out = [i.value for i in data]
        if has_numpy and as_numpy:  out = numpy.array(out)
        return out

    ntype = ftype
    unpack = unpack_simple
    if ftype >= dbr.TIME_STRING: unpack = unpack_ctrltime

    if ftype == dbr.CTRL_STRING: ftype = dbr.TIME_STRING

    if ftype > dbr.CTRL_STRING:
        ntype -= (dbr.CTRL_STRING - dbr.STRING)
    elif ftype >= dbr.TIME_STRING:
        ntype -= (dbr.TIME_STRING - dbr.STRING)

    return unpack(data)
    
@withConnectedCHID
def get(chid,ftype=None,as_string=False, as_numpy=True):
    if ftype is None: ftype = field_type(chid)
    count = element_count(chid)

    nelem = count
    if ftype == dbr.STRING:  nelem = dbr.MAX_STRING_SIZE
       
    rawdata = (nelem*dbr.Map[ftype])()
    
    ret = libca.ca_array_get(ftype, count, chid, rawdata)
    poll()
    v = _unpack_val(rawdata,count,ftype=ftype,as_numpy=as_numpy)
    if as_string and ftype==dbr.CHAR:
        v = ''.join([chr(i) for i in s if i>0]).strip().rstrip()

    return v

def _str_to_bytearray(s,maxlen=1):
    # could consider using
    # numpy.fromstring(("%s%s" % (s,'\x00'*maxlen))[:maxlen],dtype=numpy.uint8)
    return [ord(i) for i in ("%s%s" % (s,'\x00'*maxlen))[:maxlen] ]
    
@withConnectedCHID
def put(chid,value, wait=False, timeout=20, callback=None):
    ftype = field_type(chid)
    count = element_count(chid)
    rawdata = (count*dbr.Map[ftype])()    

    if count == 1:
        rawdata[0] = value
    else:
        # automatically convert strings to data arrays for character waveforms
        if ftype == dbr.CHAR and isinstance(value,(str,unicode)):
            value = _str_to_bytearray(value,maxlen=count)
        rawdata[:]  = list(value)
      
    if wait:
        pvname= name(chid)
        _put_done[pvname] = False
        poll()
        r = libca.ca_array_put_callback(ftype,count,chid,
                                        rawdata, _CB_putwait, 0)

        t0 = time.time()
        while time.time()-t0 <timeout:
            time.sleep(1.e-4)
            poll()
            if _put_done[pvname]: break
        return r
    
    elif callback is not None:
        _cb = ctypes.CFUNCTYPE(None, dbr.event_handler_args)(callback)   
        poll()
        r = libca.ca_array_put_callback(ftype,count,chid, rawdata, _cb, 0)
    else:
        r =  libca.ca_array_put(ftype,count,chid, rawdata)
    poll()
    return r

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

    value = _unpack_val(value, nelem, ftype=args.type)
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


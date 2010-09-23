#!/usr/bin/python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License

"""
  Epics Process Variable
"""
import time
import copy
from sys import stdout
from math import log10

from . import ca
from . import dbr

def fmt_time(tstamp=None):
    "simple formatter for time values"
    if tstamp is None:
        tstamp = time.time()
    tstamp, frac = divmod(tstamp, 1)
    return "%s.%6.6i" % (time.strftime("%Y-%m-%d %H:%M:%S",
                                       time.localtime(tstamp)), 1.e6*frac)

class PV(object):
    """== Epics Process Variable
    
    A PV encapsulates an Epics Process Variable.
   
    The primary interface methods for a pv are to get() and put() is value:
      >>>p = PV(pv_name)  # create a pv object given a pv name
      >>>p.get()          # get pv value
      >>>p.put(val)       # set pv to specified value. 

    Additional important attributes include:
      >>>p.pvname         # name of pv
      >>>p.value          # pv value (can be set or get)
      >>>p.char_value     # string representation of pv value
      >>>p.count          # number of elements in array pvs
      >>>p.type           # EPICS data type: 'string','double','enum','long',..
"""

    _fmt = "<PV '%(pvname)s', count=%(count)i, type=%(typefull)s, access=%(access)s>"
    _fields = ('pvname',  'value',  'char_value',  'status',  'ftype',  'chid',
               'host', 'count', 'access', 'write_access', 'read_access',
               'severity', 'timestamp', 'precision', 'units', 'enum_strs',
               'upper_disp_limit', 'lower_disp_limit', 'upper_alarm_limit',
               'lower_alarm_limit', 'lower_warning_limit',
               'upper_warning_limit', 'upper_ctrl_limit', 'lower_ctrl_limit')

    def __init__(self, pvname, callback=None, form='native',
                 verbose=False, auto_monitor=None,
                 connection_callback=None,
                 connection_timeout=2.0):
        self.pvname     = pvname.strip()
        self.form       = form.lower()
        self.verbose    = verbose
        self.auto_monitor = auto_monitor
        self.ftype      = None
        self.connected  = False
        self._args      = {}.fromkeys(self._fields)
        self._args['pvname'] = self.pvname
        self._args['count'] = -1
        self._args['type'] = 'unknown'
        self._args['typefull'] = 'unknown'
        self._args['access'] = 'unknown'
        self.connection_callback = connection_callback
        self.connection_timeout = connection_timeout
        self.callbacks  = {}
        self._monref = None  # holder of data returned from create_subscription
        self._conn_started = False
        self.chid = None

        # get current thread context to use for ca._cache
        ctx = ca.current_context()
        if ctx not in ca._cache:
            ca._cache[ctx] = {}
        if self.pvname in ca._cache[ctx]:
            entry = ca._cache[ctx][pvname]
            self.chid = entry['chid']
            self.on_connect(chid=self.chid, conn=entry['conn'])
        if self.chid is None:
            self.chid = ca.create_channel(self.pvname,
                                          userfcn=self.on_connect)
        self._args['chid'] = self.chid
        self.ftype  = ca.promote_type(self.chid,
                                      use_ctrl= self.form == 'ctrl',
                                      use_time= self.form == 'time')
        
        self._args['type'] = dbr.Name(self.ftype).lower()
        if callback is not None:
            self.add_callback(callback)

    def _write(self, msg):
        "write message"
        stdout.write("%s\n" % msg)
    
    def on_connect(self, chid=None, conn=True, **kwd):
        "callback for connection events"
        # occassionally chid is still None (threading issue???)
        # just return here, and connection will be forced later
        if self.chid is None and chid is None:
            return
        if conn:
            self.poll()
            self._args['host']   = ca.host_name(self.chid)
            self._args['count']  = ca.element_count(self.chid)
            self._args['access'] = ca.access(self.chid)
            self._args['read_access'] = (1 == ca.read_access(self.chid))
            self._args['write_access'] = (1 == ca.write_access(self.chid))
            self.ftype  = ca.promote_type(self.chid,
                                          use_ctrl= self.form == 'ctrl',
                                          use_time= self.form == 'time')
            _ftype_ = dbr.Name(self.ftype).lower()
            self._args['type'] = _ftype_
            self._args['typefull'] = _ftype_
            self._args['ftype'] = dbr.Name(_ftype_, reverse=True)
            
            if self.auto_monitor is None:
                self.auto_monitor = self._args['count'] < ca.AUTOMONITOR_MAXLENGTH
            if self._monref is None and self.auto_monitor:
                self._monref = ca.create_subscription(self.chid,
                                                      userfcn=self.on_changes,
                                                      use_ctrl=(self.form == 'ctrl'),
                                                      use_time=(self.form == 'time'))

        if hasattr(self.connection_callback, '__call__'):
            self.connection_callback(pvname=self.pvname, conn=conn, pv=self)
        # waiting until the very end until to set self.connected prevents
        # threads from thinking a connection is complete when it is actually
        # still in progress.
        self.connected = conn
        return

    def wait_for_connection(self, force=True, timeout=None):
        """wait for a connection that started with connect() to finish"""
        if not self._conn_started:
            self.connect(force=force)
        if not self.connected:
            if timeout is None:
                timeout = self.connection_timeout
            t0 = time.time()
            while (not self.connected and
                   time.time()-t0 < timeout):
                self.poll()
        return self.connected
        
    def connect(self, timeout=None, force=True):
        "check that a PV is connected, forcing a connection if needed"
        if not self.connected:
            if timeout is not None:
                self.connion_timeout = timeout
            ca.connect_channel(self.chid,
                               timeout=self.connection_timeout,
                               force=force)
            self.poll()
        self._conn_started = True
        return self.connected and self.ftype is not None

    def reconnect(self):
        self.automonitor = None
        self._monref = None
        self.connected = False
        self._conn_started = False
        return self.wait_for_connection(force=True)
    
    def poll(self, evt=1.e-4, iot=1.0):
        "poll for changes"
        ca.poll(evt=evt, iot=iot)

    def get(self, as_string=False, as_numpy=True):
        """returns current value of PV.  Use the options:
         as_string to return string representation
         as_numpy  to (try to) return a numpy array

        >>> p.get('13BMD:m1.DIR')
        0
        >>> p.get('13BMD:m1.DIR',as_string=True)
        'Pos'
        """
        if not self.wait_for_connection():
            return None
        
        self._args['value'] = ca.get(self.chid,
                                     ftype=self.ftype,
                                     as_numpy=as_numpy)
        self.poll() 
        field = 'value'
        if as_string:
            self._set_charval(self._args['value'])
            field = 'char_value'
        return self._args[field]

    def put(self, value, wait=False, timeout=30.0,
            callback=None, callback_data=None):
        """set value for PV, optionally waiting until the processing is
        complete, and optionally specifying a callback function to be run
        when the processing is complete.        
        """
        if not self.wait_for_connection():
            return None
        if (self.ftype in (dbr.ENUM, dbr.TIME_ENUM, dbr.CTRL_ENUM) and
            isinstance(value, str) and value in self._args['enum_strs']):
            value = self._args['enum_strs'].index(value)

        return ca.put(self.chid, value,
                      wait=wait, timeout=timeout,
                      callback=callback, callback_data=callback_data)

    def _set_charval(self, val, call_ca=True):
        """ sets the character representation of the value.
        intended only for internal use"""
        ftype = self._args['ftype']
        if ftype == dbr.STRING:
            self._args['char_value'] = val
            return val
        cval  = repr(val)       
        if self._args['count'] > 1:
            if ftype in (dbr.CHAR, dbr.TIME_CHAR, dbr.CTRL_CHAR):
                val = list(val)
                firstnull  = val.index(0)
                if firstnull < 0:
                    firstnull = len(val)
                cval = ''.join([chr(i) for i in val[:firstnull]]).rstrip()
            else:
                cval = '<array size=%d, type=%s>' % (len(val),
                                                     dbr.Name(ftype))
        elif ftype in (dbr.FLOAT, dbr.DOUBLE):
            if call_ca and self._args['precision'] is None:
                self.get_ctrlvars()
            try:
                prec = getattr(self, 'precision') # self._args.get('precision', None)
                fmt  = "%%.%if"
                if 4 < abs(int(log10(abs(val + 1.e-9)))):
                    fmt = "%%.%ig"
                cval = (fmt %  prec) % val
            except (ValueError, TypeError, ArithmeticError):
                self._args['char_value'] = str(val)
                return self._args['char_value']

        elif ftype == dbr.ENUM:
            if call_ca and self._args['enum_strs'] in ([], None):
                self.get_ctrlvars()
            try:
                cval = self._args['enum_strs'][val]
            except (TypeError, KeyError,  IndexError):
                pass
        self._args['char_value'] = cval
        return cval
    
    def get_ctrlvars(self):
        "get control values for variable"
        if not self.wait_for_connection():
            return None
        kwds = ca.get_ctrlvars(self.chid)
        ca.poll()
        self._args.update(kwds)
        return kwds

    def on_changes(self, value=None, **kwd):
        """internal callback function: do not overwrite!!
        To have user-defined code run when the PV value changes,
        use add_callback()
        """
        self._args.update(kwd)
        self._args['value']  = value
        self._args['timestamp'] = kwd.get('timestamp', time.time())
        self._set_charval(self._args['value'], call_ca=False)

        if self.verbose:
            now = fmt_time(self._args['timestamp'])
            self._write('%s: %s (%s)'% (self.pvname,
                                        self._args['char_value'],
                                        now))
        self.run_callbacks()
        
    def run_callbacks(self):
        """run all user-defined callbacks with the current data

        Normally, this is to be run automatically on event, but
        it is provided here as a separate function for testing
        purposes.

        Note that callback functions are called with keyword/val
        arguments including:
             self._args  (all PV data available, keys = __fields)
             keyword args included in add_callback()
             keyword 'cb_info' = (index, self)
        where the 'cb_info' is provided as a hook so that a callback
        function  that fails may de-register itself (for example, if
        a GUI resource is no longer available).
             
        """
        for index in sorted(self.callbacks.keys()):
            fcn, kwargs = self.callbacks[index]
            # print 'Run Callback %i %s:' % (index, self.pvname)
            kwd = copy.copy(self._args)
            kwd.update(kwargs)
            kwd['cb_info'] = (index, self)
            if hasattr(fcn, '__call__'):
                fcn(**kwd)
            
    def add_callback(self, callback=None, index=None, **kw):
        """add a callback to a PV.  Optional keyword arguments
        set here will be preserved and passed on to the callback
        at runtime.

        Note that a PV may have multiple callbacks, so that each
        has a unique index (small integer) that is returned by
        add_callback.  This index is needed to remove a callback."""
        if not self.wait_for_connection():
            return None
        if hasattr(callback, '__call__'):
            if index is None:
                index = 1
                if len(self.callbacks) > 0:
                    index = 1 + max(self.callbacks.keys())
            self.callbacks[index] = (callback, kw)
        return index
    
    def remove_callback(self, index=None):
        """remove a callback by index"""
        if len(self.callbacks)==1:
            self.callbacks.pop()
        if index in self.callbacks:
            self.callbacks.pop(index)
            self.poll()

    def clear_callbacks(self):
        "clear all callbacks"
        self.callbacks = {}

    def _getinfo(self):
        "get information paragraph"
        if not self.wait_for_connection():
            return None
        
        self.get_ctrlvars()
        # list basic attributes
        out = []
        mod = 'native'
        xtype = self._args['typefull']
        if '_' in xtype:
            mod, xtype = xtype.split('_')

        self._set_charval(self._args['value'], call_ca=False)        

        out.append("== %s  (%s_%s) ==" % (self.pvname, mod, xtype))
        if self.count == 1:
            val = self._args['value']
            fmt = '%i'
            if   xtype in ('float','double'):
                fmt = '%g'
            elif xtype in ('string','char'):
                fmt = '%s'
            out.append('   value      = %s' % fmt % val)
        else:
            aval, ext, fmt = [], '', "%i,"
            if self.count > 5:
                ext = '...'
            if xtype in  ('float','double'):
                fmt = "%g,"
            for i in range(min(5, self.count)):
                aval.append(fmt % self._args['value'][i])
            out.append("   value      = array  [%s%s]" % ("".join(aval),
                                                          ext))

        for i in ('char_value', 'count', 'type', 'units',
                  'precision', 'host', 'access',
                  'status', 'severity', 'timestamp',
                  'upper_ctrl_limit', 'lower_ctrl_limit',
                  'upper_disp_limit', 'lower_disp_limit',
                  'upper_alarm_limit', 'lower_alarm_limit',
                  'upper_warning_limit', 'lower_warning_limit'):
            if hasattr(self, i):
                att = getattr(self, i)
                if att is not None:
                    if i == 'timestamp':
                        att = "%.3f (%s)" % (att, fmt_time(att))
                    elif i == 'char_value':
                        att = "'%s'" % att
                    if len(i) < 12:
                        out.append('   %.11s= %s' % (i+' '*12, str(att)))
                    else:
                        out.append('   %.20s= %s' % (i+' '*20, str(att)))

        if xtype == 'enum':  # list enum strings
            out.append('   enum strings: ')
            for index, estr in enumerate(self.enum_strs):
                out.append("       %i = %s " % (index, estr))

        if self._monref is not None:
            msg = 'PV is internally monitored'
            out.append('   %s, with %i user-defined callbacks:' % (msg,
                                                         len(self.callbacks)))

            if len(self.callbacks) > 0:
                cblist = list(self.callbacks.keys())
                cblist.sort()
                for i in cblist:
                    cback = self.callbacks[i][0]
                    out.append('      %s in file %s' % (cback.func_name,
                                        cback.func_code.co_filename))
        else:
            out.append('   PV is NOT internally monitored')
        out.append('=============================')
        return '\n'.join(out)
        
    def _getarg(self, arg):
        "wrapper for property retrieval"
        if self._args['value'] is None:
            self.get()
        return self._args.get(arg, None)
        
    def __getval__(self):
        "get value"
        return self._getarg('value')

    def __setval__(self, val):
        "put-value"
        return self.put(val)

    value = property(__getval__, __setval__, None, "value property")

    @property
    def char_value(self):
        "character string representation of value"
        return self._getarg('char_value')

    @property
    def status(self):
        "pv status"
        return self._getarg('status')

    @property
    def type(self):
        "pv type"
        return self._args['type']

    @property
    def typefull(self):
        "pv type"
        return self._args['typefull']

    @property
    def host(self):
        "pv host"
        return self._getarg('host')

    @property
    def count(self):
        "count (number of elements)"
        return self._getarg('count')

    @property
    def read_access(self):
        "read access"
        return self._getarg('read_access')

    @property
    def write_access(self):
        "write access"
        return self._getarg('write_access')

    @property
    def access(self):
        "read/write access as string"
        return self._getarg('access')

    @property
    def severity(self):
        "pv severity"
        return self._getarg('severity')

    @property
    def timestamp(self):
        "timestamp of last pv action"
        return self._getarg('timestamp')

    @property
    def precision(self):
        "number of digits after decimal point"
        return self._getarg('precision')

    @property
    def units(self):
        "engineering units for pv"
        return self._getarg('units')

    @property
    def enum_strs(self):
        "list of enumeration strings"
        return self._getarg('enum_strs')

    @property
    def upper_disp_limit(self):
        "limit"
        return self._getarg('upper_disp_limit')

    @property
    def lower_disp_limit(self):
        "limit"
        return self._getarg('lower_disp_limit')

    @property
    def upper_alarm_limit(self):
        "limit"
        return self._getarg('upper_alarm_limit')

    @property
    def lower_alarm_limit(self):
        "limit"
        return self._getarg('lower_alarm_limit')

    @property
    def lower_warning_limit(self):
        "limit"
        return self._getarg('lower_warning_limit')

    @property
    def upper_warning_limit(self):
        "limit"
        return self._getarg('upper_warning_limit')

    @property
    def upper_ctrl_limit(self):
        "limit"
        return self._getarg('upper_ctrl_limit')

    @property
    def lower_ctrl_limit(self):
        "limit"
        return self._getarg('lower_ctrl_limit')

    @property
    def info(self):
        "info string"
        return self._getinfo()

    def __repr__(self):
        "string representation"

        if self.connected:
            return self._fmt % self._args
        else:
            return "<PV '%s': not connected>" % self.pvname
    
    def __eq__(self, other):
        "test for equality"
        try:
            return (self.chid  == other.chid)
        except AttributeError:
            return False

    def disconnect(self):
        "disconnect PV"
        self.connected = False
        self.callbacks = {}
        if self._monref is not None:
            cback, uarg, evid = self._monref
            ca.clear_subscription(evid)
            del cback
            del uarg
            del evid
        ca.poll()
        
    def __del__(self):
        self.disconnect()

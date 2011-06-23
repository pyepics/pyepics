#!/usr/bin/python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License

"""
  Epics Process Variable
"""
import time
import copy
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
    """Epics Process Variable

    A PV encapsulates an Epics Process Variable.

    The primary interface methods for a pv are to get() and put() is value::

      >>> p = PV(pv_name)  # create a pv object given a pv name
      >>> p.get()          # get pv value
      >>> p.put(val)       # set pv to specified value.

    Additional important attributes include::

      >>> p.pvname         # name of pv
      >>> p.value          # pv value (can be set or get)
      >>> p.char_value     # string representation of pv value
      >>> p.count          # number of elements in array pvs
      >>> p.type           # EPICS data type: 'string','double','enum','long',..
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
                 connection_timeout=None):

        self.pvname     = pvname.strip()
        self.form       = form.lower()
        self.verbose    = verbose
        self.auto_monitor = auto_monitor
        self.ftype      = None
        self.connected  = False
        self.connection_timeout = connection_timeout
        self._args      = {}.fromkeys(self._fields)
        self._args['pvname'] = self.pvname
        self._args['count'] = -1
        self._args['type'] = 'unknown'
        self._args['typefull'] = 'unknown'
        self._args['access'] = 'unknown'
        self.connection_callbacks = []
        if connection_callback is not None:
            self.connection_callbacks = [connection_callback]
        self.callbacks  = {}
        self._monref = None  # holder of data returned from create_subscription
        self._conn_started = False
        self.chid = None
        
        if ca.current_context() is None:
            ca.use_initial_context() 
        self.context = ca.current_context()

        self._args['chid'] = self.chid = ca.create_channel(self.pvname,
                                                           callback=self.__on_connect)

        self.ftype  = ca.promote_type(self.chid,
                                      use_ctrl= self.form == 'ctrl',
                                      use_time= self.form == 'time')

        self._args['type'] = dbr.Name(self.ftype).lower()
        

        if callback is not None:
            self.add_callback(callback)

    def __on_connect(self, pvname=None, chid=None, conn=True):
        "callback for connection events"
        # occassionally chid is still None (ie if a second PV is created while
        # __on_connect is still pending for the first one.)
        # Just return here, and connection will happen later
        if self.chid is None and chid is None:
            time.sleep(0.001)
            return
        if conn:
            self.poll()
            self.chid = self._args['chid'] = dbr.chid_t(chid)
            try:
                count = ca.element_count(self.chid)
            except ca.ChannelAccessException:
                time.sleep(0.025)
                count = ca.element_count(self.chid)
            self._args['count']  = count
            self._args['host']   = ca.host_name(self.chid)
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
                self.auto_monitor = count < ca.AUTOMONITOR_MAXLENGTH
            if self._monref is None and self.auto_monitor:
                self._monref = ca.create_subscription(self.chid,
                                         use_ctrl=(self.form == 'ctrl'),
                                         use_time=(self.form == 'time'),
                                         callback=self.__on_changes)

        for conn_cb in self.connection_callbacks:
            if hasattr(conn_cb, '__call__'):
                conn_cb(pvname=self.pvname, conn=conn, pv=self)
            elif not conn and self.verbose:
                ca.write("PV '%s' disconnected." % pvname)

        # waiting until the very end until to set self.connected prevents
        # threads from thinking a connection is complete when it is actually
        # still in progress.
        self.connected = conn
        return

    def wait_for_connection(self, timeout=None):
        """wait for a connection that started with connect() to finish"""

        # make sure we're in the CA context used to create this PV
        if self.context != ca.current_context():
            ca.attach_context(self.context)

        if not self._conn_started:
            self.connect()
        if not self.connected:
            if timeout is None:
                timeout = self.connection_timeout
                if timeout is None:
                    timeout = ca.DEFAULT_CONNECTION_TIMEOUT
            start_time = time.time()
            while (not self.connected and
                   time.time()-start_time < timeout):
                self.poll()
        return self.connected

    def connect(self, timeout=None):
        "check that a PV is connected, forcing a connection if needed"
        if not self.connected:
            if timeout is None:
                timeout = self.connection_timeout
            ca.connect_channel(self.chid, timeout=timeout)
        self._conn_started = True
        return self.connected and self.ftype is not None

    def reconnect(self):
        "try to reconnect PV"
        self.auto_monitor = None
        self._monref = None
        self.connected = False
        self._conn_started = False
        return self.wait_for_connection()

    def poll(self, evt=1.e-4, iot=1.0):
        "poll for changes"
        ca.poll(evt=evt, iot=iot)

    def get(self, count=None, as_string=False, as_numpy=True):
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

        if not self.auto_monitor or self._args['value'] is None:
            self._args['value'] = ca.get(self.chid,
                                         count=count,
                                         ftype=self.ftype,
                                         as_numpy=as_numpy)

        if as_string:
            self._set_charval(self._args['value'])
            return self._args['char_value']

        # this emulates asking for less data than actually exists in the
        # cached value
        if count is not None and len(self._args['value']) > 1:
            count = max(0, min(count, len(self._args['value'])))
            return self._args['value'][:count]
        return self._args['value']

    def put(self, value, wait=False, timeout=30.0,
            use_complete=False, callback=None, callback_data=None):
        """set value for PV, optionally waiting until the processing is
        complete, and optionally specifying a callback function to be run
        when the processing is complete.
        """
        if not self.wait_for_connection():
            return None
        if (self.ftype in (dbr.ENUM, dbr.TIME_ENUM, dbr.CTRL_ENUM) and
            isinstance(value, str)):
            if self._args['enum_strs'] is None:
                self.get_ctrlvars()
            if value in self._args['enum_strs']:
                value = self._args['enum_strs'].index(value)
        if use_complete and callback is None:
            callback = self.__putCallbackStub
        return ca.put(self.chid, value,
                      wait=wait, timeout=timeout,
                      callback=callback,
                      callback_data=callback_data)

    def __putCallbackStub(self, pvname=None, **kws):
        "null put-calback, so that the put_complete attribute is valid"
        pass

    def _set_charval(self, val, call_ca=True):
        """ sets the character representation of the value.
        intended only for internal use"""
        ftype = self._args['ftype']
        ntype = ca.native_type(ftype)
        if ntype == dbr.STRING:
            self._args['char_value'] = val
            return val
        cval  = repr(val)
        if self.count > 1:
            if ntype == dbr.CHAR and self.count < ca.AUTOMONITOR_MAXLENGTH:
                val = list(val)
                if 0 in val:
                    firstnull  = val.index(0)
                else:
                    firstnull = len(val)
                try:
                    cval = ''.join([chr(i) for i in val[:firstnull]]).rstrip()
                except ValueError:
                    pass
            else:
                cval = '<array size=%d, type=%s>' % (len(val),
                                                     dbr.Name(ftype).lower())
        elif ntype in (dbr.FLOAT, dbr.DOUBLE):
            if call_ca and self._args['precision'] is None:
                self.get_ctrlvars()
            try:
                prec = getattr(self, 'precision')
                fmt  = "%%.%if"
                if 4 < abs(int(log10(abs(val + 1.e-9)))):
                    fmt = "%%.%ig"
                cval = (fmt %  prec) % val
            except (ValueError, TypeError, ArithmeticError):
                self._args['char_value'] = str(val)
                return self._args['char_value']

        elif ntype == dbr.ENUM:
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
        return self._get_vars(ca.get_ctrlvars)

    def get_timevars(self):
        "get time values for variable"
        return self._get_vars(ca.get_timevars)

    def _get_vars(self, var_fn):
        "internal, common functionality for retreiving control/times values"
        if not self.wait_for_connection():
            return None
        kwds = var_fn(self.chid)
        ca.poll()
        self._args.update(kwds)
        return kwds


    def __on_changes(self, value=None, **kwd):
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
            ca.write('%s: %s (%s)'% (self.pvname,
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
        for index in sorted(list(self.callbacks.keys())):
            fcn, kwargs = self.callbacks[index]
            kwd = copy.copy(self._args)
            kwd.update(kwargs)
            kwd['cb_info'] = (index, self)
            if hasattr(fcn, '__call__'):
                fcn(**kwd)

    def add_callback(self, callback=None, index=None,
                     with_ctrlvars=True, **kw):
        """add a callback to a PV.  Optional keyword arguments
        set here will be preserved and passed on to the callback
        at runtime.

        Note that a PV may have multiple callbacks, so that each
        has a unique index (small integer) that is returned by
        add_callback.  This index is needed to remove a callback."""
        if not self.wait_for_connection():
            return None
        if with_ctrlvars:
            self.get_ctrlvars()
        if hasattr(callback, '__call__'):
            if index is None:
                index = 1
                if len(self.callbacks) > 0:
                    index = 1 + max(self.callbacks.keys())
            self.callbacks[index] = (callback, kw)
        return index

    def remove_callback(self, index=None):
        """remove a callback by index"""
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
        out = []
        mod = 'native'
        xtype = self._args['typefull']
        if '_' in xtype:
            mod, xtype = xtype.split('_')

        fmt = '%i'
        if   xtype in ('float','double'):
            fmt = '%g'
        elif xtype in ('string','char'):
            fmt = '%s'

        self._set_charval(self._args['value'], call_ca=False)
        out.append("== %s  (%s_%s) ==" % (self.pvname, mod, xtype))
        if self.count == 1:
            val = self._args['value']
            out.append('   value      = %s' % fmt % val)
        else:
            ext  = {True:'...', False:''}[self.count > 10]
            elems = range(min(5, self.count))
            aval = [fmt % self._args['value'][i] for i in elems]
            out.append("   value      = array  [%s%s]" % (",".join(aval), ext))
        for nam in ('char_value', 'count', 'type', 'units', 'precision',
                    'host', 'access', 'status', 'severity', 'timestamp',
                    'upper_ctrl_limit', 'lower_ctrl_limit',
                    'upper_disp_limit', 'lower_disp_limit',
                    'upper_alarm_limit', 'lower_alarm_limit',
                    'upper_warning_limit', 'lower_warning_limit'):
            if hasattr(self, nam):
                att = getattr(self, nam)
                if att is not None:
                    if nam == 'timestamp':
                        att = "%.3f (%s)" % (att, fmt_time(att))
                    elif nam == 'char_value':
                        att = "'%s'" % att
                    if len(nam) < 12:
                        out.append('   %.11s= %s' % (nam+' '*12, str(att)))
                    else:
                        out.append('   %.20s= %s' % (nam+' '*20, str(att)))
        if xtype == 'enum':  # list enum strings
            out.append('   enum strings: ')
            for index, nam in enumerate(self.enum_strs):
                out.append("       %i = %s " % (index, nam))

        if self._monref is not None:
            msg = 'PV is internally monitored'
            out.append('   %s, with %i user-defined callbacks:' % (msg,
                                                         len(self.callbacks)))
            if len(self.callbacks) > 0:
                for nam in sorted(self.callbacks.keys()):
                    cback = self.callbacks[nam][0]
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

    @property
    def put_complete(self):
        "returns True if a put-with-wait has completed"
        putdone_data = ca._put_done.get(self.pvname, None)
        if putdone_data is not None:
            return putdone_data[0]
        return True

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
        if self._monref is not None:
            cback, uarg, evid = self._monref
            ca.clear_subscription(evid)
            ctx = ca.current_context()
            if self.pvname in ca._cache[ctx]:
                ca._cache[ctx].pop(self.pvname)

            del cback
            del uarg
            del evid
        ca.poll(evt=1.e-3, iot=1.0)
        self.callbacks = {}

    def __del__(self):
        try:
            self.disconnect()
        except:
            pass

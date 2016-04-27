#!/usr/bin/env python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License

"""
  Epics Process Variable
"""
import time
import ctypes
import copy
from math import log10

from . import ca
from . import dbr
from .utils import is_string

_PVcache_ = {}

def get_pv(pvname, form='time',  connect=False,
           context=None, timeout=5.0, **kws):
    """get PV from PV cache or create one if needed.

    Arguments
    =========
    form      PV form: one of 'native' (default), 'time', 'ctrl'
    connect   whether to wait for connection (default False)
    context   PV threading context (default None)
    timeout   connection timeout, in seconds (default 5.0)
    """

    if form not in ('native', 'time', 'ctrl'):
        form = 'native'

    thispv = None
    if context is None:
        context = ca.initial_context
        if context is None:
            context = ca.current_context()
        if (pvname, form, context) in _PVcache_:
            thispv = _PVcache_[(pvname, form, context)]

    start_time = time.time()
    # not cached -- create pv (automaticall saved to cache)
    if thispv is None:
        thispv = PV(pvname, form=form, **kws)

    if connect:
        thispv.wait_for_connection()
        while not thispv.connected:
            ca.poll()
            if time.time()-start_time > timeout:
                break
        if not thispv.connected:
            ca.write('cannot connect to %s' % pvname)
    return thispv

def fmt_time(tstamp=None):
    "simple formatter for time values"
    if tstamp is None:
        tstamp = time.time()
    tstamp, frac = divmod(tstamp, 1)
    return "%s.%5.5i" % (time.strftime("%Y-%m-%d %H:%M:%S",
                                       time.localtime(tstamp)),
                         round(1.e5*frac))


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

    _fmtsca = "<PV '%(pvname)s', count=%(count)i, type=%(typefull)s, access=%(access)s>"
    _fmtarr = "<PV '%(pvname)s', count=%(count)i/%(nelm)i, type=%(typefull)s, access=%(access)s>"
    _fields = ('pvname',  'value',  'char_value',  'status',  'ftype',  'chid',
               'host', 'count', 'access', 'write_access', 'read_access',
               'severity', 'timestamp', 'precision', 'units', 'enum_strs',
               'upper_disp_limit', 'lower_disp_limit', 'upper_alarm_limit',
               'lower_alarm_limit', 'lower_warning_limit',
               'upper_warning_limit', 'upper_ctrl_limit', 'lower_ctrl_limit')

    def __init__(self, pvname, callback=None, form='time',
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
        self._args['nelm']  = -1
        self._args['type'] = 'unknown'
        self._args['typefull'] = 'unknown'
        self._args['access'] = 'unknown'
        self.connection_callbacks = []

        if connection_callback is not None:
            self.connection_callbacks = [connection_callback]

        self.callbacks  = {}
        self._monref = None  # holder of data returned from create_subscription
        self._conn_started = False
        if isinstance(callback, (tuple, list)):
            for i, thiscb in enumerate(callback):
                if hasattr(thiscb, '__call__'):
                    self.callbacks[i] = (thiscb, {})
        elif hasattr(callback, '__call__'):
            self.callbacks[0] = (callback, {})

        self.chid = None
        if ca.current_context() is None:
            ca.use_initial_context()
        self.context = ca.current_context()

        self._args['chid'] = ca.create_channel(self.pvname,
                                               callback=self.__on_connect)
        self.chid = self._args['chid']
        self.ftype  = ca.promote_type(self.chid,
                                      use_ctrl= self.form == 'ctrl',
                                      use_time= self.form == 'time')
        self._args['type'] = dbr.Name(self.ftype).lower()

        pvid = (self.pvname, self.form, self.context)
        if pvid not in _PVcache_:
            _PVcache_[pvid] = self

    def force_connect(self, pvname=None, chid=None, conn=True, **kws):
        if chid is None: chid = self.chid
        if isinstance(chid, ctypes.c_long):
            chid = chid.value
        self._args['chid'] = self.chid = chid
        self.__on_connect(pvname=pvname, chid=chid, conn=conn, **kws)

    def __on_connect(self, pvname=None, chid=None, conn=True):
        "callback for connection events"
        # occassionally chid is still None (ie if a second PV is created
        # while __on_connect is still pending for the first one.)
        # Just return here, and connection will happen later
        t0 = time.time()
        if self.chid is None and chid is None:
            ca.poll(5.e-4)
            return
        if conn:
            ca.poll()
            self.chid = self._args['chid'] = dbr.chid_t(chid)
            try:
                count = ca.element_count(self.chid)
            except ca.ChannelAccessException:
                time.sleep(0.025)
                count = ca.element_count(self.chid)
            self._args['count']  = count
            self._args['nelm']  = count
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
                # you can explicitly request a subscription mask
                # (ie dbr.DBE_ALARM|dbr.DBE_LOG) by passing it as the
                # auto_monitor arg, otherwise if you specify 'True' you'll
                # just get the default set in ca.DEFAULT_SUBSCRIPTION_MASK
                mask = None
                if isinstance(self.auto_monitor, int):
                    mask = self.auto_monitor
                self._monref = ca.create_subscription(self.chid,
                                         use_ctrl=(self.form == 'ctrl'),
                                         use_time=(self.form == 'time'),
                                         callback=self.__on_changes,
                                         mask=mask)

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
                ca.poll()
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

    def get(self, count=None, as_string=False, as_numpy=True,
            timeout=None, with_ctrlvars=False, use_monitor=True):
        """returns current value of PV.  Use the options:
        count       explicitly limit count for array data
        as_string   flag(True/False) to get a string representation
                    of the value.
        as_numpy    flag(True/False) to use numpy array as the
                    return type for array data.
        timeout     maximum time to wait for value to be received.
                    (default = 0.5 + log10(count) seconds)
        use_monitor flag(True/False) to use value from latest
                    monitor callback (True, default) or to make an
                    explicit CA call for the value.

        >>> p.get('13BMD:m1.DIR')
        0
        >>> p.get('13BMD:m1.DIR', as_string=True)
        'Pos'
        """
        if not self.wait_for_connection():
            return None
        if with_ctrlvars and getattr(self, 'units', None) is None:
            self.get_ctrlvars()

        if ((not use_monitor) or
            (not self.auto_monitor) or
            (self._args['value'] is None) or
            (count is not None and count > len(self._args['value']))):
            ca_get = ca.get
            if ca.get_cache(self.pvname)['value'] is not None:
                ca_get = ca.get_complete
            self._args['value'] = ca_get(self.chid, ftype=self.ftype,
                                         count=count, timeout=timeout,
                                         as_numpy=as_numpy)
        val = self._args['value']
        if as_string:
            return self._set_charval(val)
        if self.count <= 1 or val is None:
            return val

        # After this point:
        #   * self.count is > 1
        #   * val should be set and a sequence
        try:
            len(val)
        except TypeError:
            # Edge case where a scalar value leaks through ca.unpack()
            val = [val]

        if count is None:
            count = len(val)

        if (as_numpy and ca.HAS_NUMPY and
                not isinstance(val, ca.numpy.ndarray)):
            val = ca.numpy.asarray(val)
        elif (not as_numpy and ca.HAS_NUMPY and
                isinstance(val, ca.numpy.ndarray)):
            val = val.tolist()
        # allow asking for less data than actually exists in the cached value
        if count < len(val):
            val = val[:count]
        return val

    def put(self, value, wait=False, timeout=30.0,
            use_complete=False, callback=None, callback_data=None):
        """set value for PV, optionally waiting until the processing is
        complete, and optionally specifying a callback function to be run
        when the processing is complete.
        """
        if not self.wait_for_connection():
            return None

        if (self.ftype in (dbr.ENUM, dbr.TIME_ENUM, dbr.CTRL_ENUM) and
            is_string(value)):
            if self._args['enum_strs'] is None:
                self.get_ctrlvars()
            if value in self._args['enum_strs']:
                # tuple.index() not supported in python2.5
                # value = self._args['enum_strs'].index(value)
                for ival, val in enumerate(self._args['enum_strs']):
                    if val == value:
                        value = ival
                        break
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
        if val is None:
            self._args['char_value'] = 'None'
            return 'None'
        ftype = self._args['ftype']
        ntype = ca.native_type(ftype)
        if ntype == dbr.STRING:
            self._args['char_value'] = val
            return val
        # char waveform as string
        if ntype == dbr.CHAR and self.count < ca.AUTOMONITOR_MAXLENGTH:
            if ca.HAS_NUMPY and isinstance(val, ca.numpy.ndarray):
                # a numpy array
                val = val.tolist()

                if not isinstance(val, list):
                    # a scalar value from numpy, tolist() turns it into a
                    # native python integer
                    val = [val.tolist()]
            else:
                try:
                    # otherwise, try forcing it into a list. this will fail for
                    # scalar types
                    val = list(val)
                except TypeError:
                    # and when it fails, make it a list of one scalar value
                    val = [val]

            if 0 in val:
                firstnull  = val.index(0)
            else:
                firstnull = len(val)
            try:
                cval = ''.join([chr(i) for i in val[:firstnull]]).rstrip()
            except ValueError:
                cval = ''
            self._args['char_value'] = cval
            return cval

        cval  = repr(val)
        if self.count > 1:
            try:
                length = len(val)
            except TypeError:
                length = 1
            cval = '<array size=%d, type=%s>' % (length,
                                                 dbr.Name(ftype).lower())
        elif ntype in (dbr.FLOAT, dbr.DOUBLE):
            if call_ca and self._args['precision'] is None:
                self.get_ctrlvars()
            try:
                prec = self._args['precision']
                fmt  = "%%.%if"
                if 4 < abs(int(log10(abs(val + 1.e-9)))):
                    fmt = "%%.%ig"
                cval = (fmt %  prec) % val
            except (ValueError, TypeError, ArithmeticError):
                cval = str(val)
        elif ntype == dbr.ENUM:
            if call_ca and self._args['enum_strs'] in ([], None):
                self.get_ctrlvars()
            try:
                cval = self._args['enum_strs'][val]
            except (TypeError, KeyError,  IndexError):
                cval = str(val)

        self._args['char_value'] = cval
        return cval

    def get_ctrlvars(self, timeout=5, warn=True):
        "get control values for variable"
        if not self.wait_for_connection():
            return None
        kwds = ca.get_ctrlvars(self.chid, timeout=timeout, warn=warn)
        self._args.update(kwds)
        return kwds

    def get_timevars(self, timeout=5, warn=True):
        "get time values for variable"
        if not self.wait_for_connection():
            return None
        kwds = ca.get_timevars(self.chid, timeout=timeout, warn=warn)
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
                                     self._args['char_value'], now))
        self.run_callbacks()

    def run_callbacks(self):
        """run all user-defined callbacks with the current data

        Normally, this is to be run automatically on event, but
        it is provided here as a separate function for testing
        purposes.
        """
        for index in sorted(list(self.callbacks.keys())):
            self.run_callback(index)

    def run_callback(self, index):
        """run a specific user-defined callback, specified by index,
        with the current data
        Note that callback functions are called with keyword/val
        arguments including:
             self._args  (all PV data available, keys = __fields)
             keyword args included in add_callback()
             keyword 'cb_info' = (index, self)
        where the 'cb_info' is provided as a hook so that a callback
        function  that fails may de-register itself (for example, if
        a GUI resource is no longer available).
        """
        try:
            fcn, kwargs = self.callbacks[index]
        except KeyError:
            return
        kwd = copy.copy(self._args)
        kwd.update(kwargs)
        kwd['cb_info'] = (index, self)
        if hasattr(fcn, '__call__'):
            fcn(**kwd)

    def add_callback(self, callback=None, index=None, run_now=False,
                     with_ctrlvars=True, **kw):
        """add a callback to a PV.  Optional keyword arguments
        set here will be preserved and passed on to the callback
        at runtime.

        Note that a PV may have multiple callbacks, so that each
        has a unique index (small integer) that is returned by
        add_callback.  This index is needed to remove a callback."""
        if hasattr(callback, '__call__'):
            if index is None:
                index = 1
                if len(self.callbacks) > 0:
                    index = 1 + max(self.callbacks.keys())
            self.callbacks[index] = (callback, kw)

        if with_ctrlvars and self.connected:
            self.get_ctrlvars()
        if run_now:
            self.get(as_string=True)
            if self.connected:
                self.run_callback(index)
        return index

    def remove_callback(self, index=None):
        """remove a callback by index"""
        if index in self.callbacks:
            self.callbacks.pop(index)
            ca.poll()

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
            try:
                aval = [fmt % self._args['value'][i] for i in elems]
            except TypeError:
                aval = ('unknown',)
            out.append("   value      = array  [%s%s]" % (",".join(aval), ext))
        for nam in ('char_value', 'count', 'nelm', 'type', 'units',
                    'precision', 'host', 'access',
                    'status', 'severity', 'timestamp',
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
        if self._args[arg] is None:
            if arg in ('status', 'severity', 'timestamp'):
                self.get_timevars(timeout=1, warn=False)
            else:
                self.get_ctrlvars(timeout=1, warn=False)
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
        """count (number of elements). For array data and later EPICS versions,
        this is equivalent to the .NORD field.  See also 'nelm' property"""
        if self._args['count'] >=0:
            return self._args['count']
        else:
            return self._getarg('count')

    @property
    def nelm(self):
        """native count (number of elements).
        For array data this will return the full array size (ie, the
        .NELM field).  See also 'count' property"""
        if self._getarg('count') == 1:
            return 1
        return ca.element_count(self.chid)

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
            if self.count == 1:
                return self._fmtsca % self._args
            else:
                return self._fmtarr % self._args
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

        ctx = ca.current_context()
        pvid = (self.pvname, self.form, ctx)
        if pvid in _PVcache_:
            _PVcache_.pop(pvid)

        if self._monref is not None:
            cback, uarg, evid = self._monref
            ctx = ca.current_context()
            if self.pvname in ca._cache[ctx]:
                # atexit may have already cleared the subscription
                ca.clear_subscription(evid)
                ca._cache[ctx].pop(self.pvname)
            del cback
            del uarg
            del evid
            try:
                self._monref = None
                self._args   = {}.fromkeys(self._fields)
            except:
                pass

        ca.poll(evt=1.e-3, iot=1.0)
        self.callbacks = {}

    def __del__(self):
        try:
            self.disconnect()
        except:
            pass

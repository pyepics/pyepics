#!/usr/bin/python
"""
  Epics Process Variable
"""
import time
import math
import copy
import ca
import dbr

def fmt_time(t=None):
    if t is None: t = time.time()
    t,frac=divmod(t,1)
    return "%s.%6.6i" %(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(t)),1.e6*frac)

_fields = ('pvname', 'value', 'char_value', 'status', 'ftype', 'chid',
           'host', 'count', 'access', 'write_access', 'read_access', 'severity',
           'timestamp', 'precision', 'units', 'enum_strs', 'no_str',
           'upper_disp_limit', 'lower_disp_limit', 'upper_alarm_limit',
           'lower_alarm_limit', 'lower_warning_limit',
           'upper_warning_limit', 'upper_ctrl_limit', 'lower_ctrl_limit')

# cache of PVs
PV_cache = {}

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

    def __init__(self,pvname, callback=None, form='native',
                 verbose=False, auto_monitor=True):
        self.pvname  = pvname.strip()
        self.form = form.lower()
        self.verbose = verbose
        self.auto_monitor = auto_monitor
        self.callbacks = {}
        if callable(callback): self.callbacks[0] = (callback,{})
        self.ftype = None
        self.connected  = False
        self._args      = {}.fromkeys(_fields)

        self._args['pvname'] = self.pvname
        self.__mondata = None
        if self.pvname in ca._cache:
            self.chid = ca._cache[pvname]['chid']
        else:
            self.chid = ca.create_channel(self.pvname,
                                          userfcn=self._onConnect)
        self._args['chid'] = self.chid
        try:
            self._args['type'] = dbr.Name(ca.field_type(self.chid)).lower()
        except:
            self._args['type'] = 'unknown'

        PV_cache[(pvname,self.form)] = self
        
    def _onConnect(self,chid=0,conn=True,**kw):
        self.connected = conn
        # print '_onConnect!!  ', chid, self.pvname, self.form, ' ::'
        if self.connected:
            self._args['host']   = ca.host_name(self.chid)
            self._args['count']  = ca.element_count(self.chid)
            self._args['access'] = ca.access(self.chid)
            self._args['read_access'] = 1==ca.read_access(self.chid)
            self._args['write_access'] = 1==ca.write_access(self.chid)
            self.ftype  = ca.promote_type(self.chid,
                                     use_ctrl= self.form=='ctrl',
                                     use_time= self.form=='time')
            self._args['type'] = dbr.Name(self.ftype).lower()
            # print 'onConnect ', self.ftype, self._args['type']            
        return

    def connect(self,timeout=5.0,force=True):
        if not self.connected:
            ca.connect_channel(self.chid, timeout=timeout,force=force)
            self.poll()
        if (self.connected and
            self.auto_monitor and
            self.__mondata is None):
            self.__mondata = ca.subscribe(self.chid,
                                          userfcn=self._onChanges,
                                          use_ctrl= self.form=='ctrl',
                                          use_time= self.form=='time')
        return (self.connected and self.ftype is not None)

    def poll(self,ev=1.e-4, io=1.0):
        ca.poll(ev=ev, io=io)

    def get(self, as_string=False):
        """returns current value of PV
        use argument 'as_string=True' to
        return string representation

        >>> p.get('13BMD:m1.DIR')
        0
        >>> p.get('13BMD:m1.DIR',as_string=True)
        'Pos'
        """
        if not self.connect(force=False):  return None
        self._args['value'] = ca.get(self.chid,
                                    ftype=self.ftype)
        self.poll() 
        self._set_charval(self._args['value'])

        field = 'value'
        if as_string: field = 'char_value'
        return self._args[field]

    def put(self,value,wait=False,timeout=30.0,callback=None,callback_data=None):
        """set value for PV, optionally waiting until the processing is
        complete, and optionally specifying a callback function to be run
        when the processing is complete.        
        """
        if not self.connect(force=False):  return None
        if (self.ftype in (dbr.ENUM,dbr.TIME_ENUM,dbr.CTRL_ENUM) and
            isinstance(value,str) and
            value in self._args['enum_strs']):
            value = self._args['enum_strs'].index(value)
        
        return ca.put(self.chid, value,
                      wait=wait,    timeout=timeout,
                      callback=callback, callback_data=callback_data)

    def _set_charval(self,val,ca_calls=True):
        """ sets the character representation of the value. intended for internal use"""

        ftype = self._args['ftype']
        cval  = repr(val)       
        if ftype == dbr.STRING: cval = val
        
        if self._args['count'] > 1:
            if ftype == dbr.CHAR:
                val = list(val)
                n0  = val.index(0)
                if n0 == -1: n0 = len(val)
                cval = ''.join([chr(i) for i in val[:n0]]).rstrip()
            else:
                cval = '<array size=%d, type=%s>' % (len(val),
                                                     dbr.Name(ftype))
        elif ftype in (dbr.FLOAT, dbr.DOUBLE):
            if ca_calls and self._args['precision'] is None:
                self.get_ctrlvars()
            try: 
                fmt  = "%%.%if"
                if 4 < abs(int(math.log10(abs(val + 1.e-9)))):
                    fmt = "%%.%ig"
                cval = (fmt % self._args['precision']) % val
            except:
                pass 
        elif ftype == dbr.ENUM:
            if ca_calls and self._args['enum_strs'] in ([], None):
                self.get_ctrlvars()
            try:
                cval = self._args['enum_strs'][val]
            except:
                pass

        self._args['char_value'] =cval
        return cval

    
    def get_ctrlvars(self):
        if not self.connect(force=False):  return None
        kw = ca.get_ctrlvars(self.chid)
        self._args.update(kw)
        return kw

    def _onChanges(self, value=None, **kw):
        """built-in, internal callback function:
        This should not be overwritten!!
        
        To have user-defined code run when the PV value changes,
        use add_callback()
        """
        self._args.update(kw)
        self._args['value']  = value
        self._args['timestamp'] = kw.get('timestamp',time.time())

        self._set_charval(self._args['value'],ca_calls=False)

        if self.verbose:
            print '  %s: %s (%s)'% (self.pvname,self._args['char_value'],
                                    fmt_time(self._args['timestamp']))
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
             keyword 'cb_info' = (index, remove_callback)
        where the 'cb_info' is provided as a hook so that a callback
        function  that fails may de-register itself (for example, if
        a GUI resource is no longer available).
             
        """
        # Note
        for index in sorted(self.callbacks.keys()):
            fcn,kwargs = self.callbacks[index]
            kw = copy.copy(self._args)
            kw.update(kwargs)
            kw['cb_info'] = (index, self.remove_callback)
            if callable(fcn):
                fcn(**kw)
            
    def add_callback(self,callback=None,**kw):
        """add a callback to a PV.  Optional keyword arguments
        set here will be preserved and passed on to the callback
        at runtime.

        Note that a PV may have multiple callbacks, so that each
        has a unique index (small integer) that is returned by
        add_callback.  This index is needed to remove a callback."""
        if callable(callback):
            n_cb = len(self.callbacks)
            index = 1
            if n_cb > 1:  index = 1 + max(self.callbacks.keys())
            self.callbacks[index] = (callback,kw)
        return index
    
    def remove_callback(self,index=None):
        """remove a callback.
        """
        if index is None and len(self.callbacks)==1:
            index = self.callbacks.keys()[0]
        if index in self.callbacks:
            x = self.callbacks.pop(index)
            self.poll()

    def clear_callbacks(self,**kw):
        self.callbacks = {}

    def _getinfo(self):
        if not self.connect(force=False):  return None
        if self._args['precision'] is None: self.get_ctrlvars()

        out = []
        # list basic attributes
        mod   = 'native'
        xtype = self._args['type']
        if '_' in xtype: mod,xtype = xtype.split('_')

        out.append("== %s  (%s) ==" % (self.pvname,xtype))

        if self.count==1:
            val = self._args['value']
            fmt = '%i'
            if   xtype in ('float','double'): fmt = '%g'
            elif xtype in ('string','char'):  fmt = '%s'
            out.append('   value      = %s' % fmt % val)

        else:
            aval,ext,fmt = [],'',"%i,"
            if self.count>5: ext = '...'
            if xtype in  ('float','double'): fmt = "%g,"
            for i in range(min(5,self.count)):
                aval.append(fmt % self._args['value'][i])
            out.append("   value      = array  [%s%s]" % ("".join(aval),ext))

        for i in ('char_value','count','type','units',
                  'precision','host','access',
                  'status','severity','timestamp',
                  'upper_ctrl_limit', 'lower_ctrl_limit',
                  'upper_disp_limit', 'lower_disp_limit',
                  'upper_alarm_limit', 'lower_alarm_limit',
                  'upper_warning_limit','lower_warning_limit'):
            if hasattr(self,i):
                att = getattr(self,i)
                if i == 'timestamp': att = "%.3f (%s)" % (att,fmt_time(att))
                if att is not None:
                    if len(i) < 12:
                        out.append('   %.11s= %s' % (i+' '*12, str(att)))
                    else:
                        out.append('   %.20s= %s' % (i+' '*20, str(att)))

        if xtype == 'enum':  # list enum strings
            out.append('   enum strings: ')
            for i,s in enumerate(self.enum_strs):
                out.append("       %i = %s " % (i,s))

        if self.__mondata is not None:
            out.append('   PV is monitored internally')
            if len(self.callbacks) > 0:
                out.append("   user-defined callbacks:")
                cblist = self.callbacks.keys()
                cblist.sort()
                for i in cblist:
                    cb = self.callbacks[i]
                    out.append('      %s' % repr(cb))
            else:
                out.append("   no user callbacks are defined.")
        else:
            out.append('   PV is not monitored internally')
        out.append('=============================')
        return '\n'.join(out)
        
    def _getarg(self,arg):
        if self._args['value'] is None:  self.get()
        return self._args.get(arg,None)
        
    def __getval__(self):    return self._getarg('value')
    def __setval__(self,v):  return self.put(v)
    value = property(__getval__, __setval__, None, "value property")

    @property
    def char_value(self): return self._getarg('char_value')

    @property
    def status(self): return self._getarg('status')

    @property
    def type(self): return self._args['type']

    @property
    def host(self): return self._getarg('host')

    @property
    def count(self): return self._getarg('count')

    @property
    def read_access(self): return self._getarg('read_access')

    @property
    def write_access(self): return self._getarg('write_access')

    @property
    def access(self): return self._getarg('access')

    @property
    def severity(self): return self._getarg('severity')

    @property
    def timestamp(self): return self._getarg('timestamp')

    @property
    def precision(self): return self._getarg('precision')

    @property
    def units(self): return self._getarg('units')

    @property
    def enum_strs(self): return self._getarg('enum_strs')

    @property
    def no_str(self): return self._getarg('no_str')

    @property
    def upper_disp_limit(self): return self._getarg('upper_disp_limit')

    @property
    def lower_disp_limit(self): return self._getarg('lower_disp_limit')

    @property
    def upper_alarm_limit(self): return self._getarg('upper_alarm_limit')

    @property
    def lower_alarm_limit(self): return self._getarg('lower_alarm_limit')

    @property
    def lower_warning_limit(self): return self._getarg('lower_warning_limit')

    @property
    def upper_warning_limit(self): return self._getarg('upper_warning_limit')

    @property
    def upper_ctrl_limit(self): return self._getarg('upper_ctrl_limit')

    @property
    def lower_ctrl_limit(self): return self._getarg('lower_ctrl_limit')

    @property
    def info(self): return self._getinfo()

    def __repr__(self):
        if not self.connected:  return "<PV '%s': not connected>" % self.pvname
        fmt="<PV '%(pvname)s', count=%(count)i, type=%(type)s, access=%(access)s>"
        return  fmt % self._args
    
    def __str__(self): return self.__repr__()

    def __eq__(self,other):
        try:
            return (self.chid  == other.chid)
        except:
            return False
        

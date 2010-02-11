import ca
import dbr
import time
import math

def fmt_time(t=None):
    if t is None: t = time.time()
    t,frac=divmod(t,1)
    return "%s.%3.3i" %(time.strftime("%Y-%h-%d %H:%M:%S"),1000.0*frac)

class PV(object):
    """== Epics Process Variable
    
    A PV encapsulates an Epics Process Variable (aka a 'channel').
   
    The primary interface methods for a pv are to get() and put() is value:
      >>>p = PV(pv_name)    # create a pv object given a pv name
      >>>p.get()            # get pv value
      >>>p.put(val)         # set pv to specified value. 

    Additional important attributes include:
      >>>p.pvname           # name of pv
      >>>p.value            # pv value (can be set or get)
      >>>p.char_value       # string representation of pv value
      >>>p.count            # number of elements in array pvs
      >>>p.type             # EPICS data type: 'string','double','enum','long',....
"""
    connect_ErrorMsg   = "cannot connect to %s -- may need a connection timeout longer than %f seconds"
    enumrange_ErrorMsg = "value %i out of range for enum PV %s"
    callback_ErrorMsg  = "severe error with get callback for %s"
    setattr_ErrorMsg   = "cannot set %s for %s"
    
    repr_Normal        = "<PV: '%s', count=%i, type=%s, access=%s>"
    repr_unnamed       = "<PV: unnamed>"
    repr_unconnected   = "<PV '%s': unconnectd>" 

    def __init__(self,pvname, callback=None, form='native',
                 use_cache=True, auto_monitor=True, **kw):

        self.pvname = pvname.strip()

        self.connected  = False
        self.auto_monitor = auto_monitor

        self._val      = None
        self._charval  = None
        self.__mondata = None
        self.callbacks = []
        self.precision = None
        self.enum_strs = None

        self.chid = ca.create_channel(self.pvname,
                                      userfcn=self._onConnect)

        self.ftype = 0
        self._form = {'ctrl': (form.lower() =='ctrl'),
                      'time': (form.lower() =='time')}


    def _onConnect(self,chid=0):
        self.connected = ca._cache[self.pvname][1]        
        if self.connected:
            self.host   = ca.host_name(self.chid)
            self.count  = ca.element_count(self.chid)
            self.access = ca.access(self.chid)
            self.write_access = ca.write_access(self.chid)
            self.ftype  = ca.promote_type(self.chid,
                                          use_ctrl=self._form['ctrl'],
                                          use_time=self._form['time'])
        # print 'onConnect done ', self.pvname, self.connected
        return
            

    def connect(self,timeout=10.0):
        if not self.connected:
            ca.connect_channel(self.chid, timeout=timeout)
            self.poll()
            # print self.pvname, self.connected
        if self.auto_monitor and self.__mondata is None:
            self.__mondata = ca.subscribe(self.chid,
                                          userfcn=self._onChanges,
                                          use_ctrl=self._form['ctrl'],
                                          use_time=self._form['time'])
        return self.connected

    def get(self,**kw):
        if not self.connect():  return None
        val = ca.get(self.chid,ftype=self.ftype, **kw)
        self.poll() 
        self.set_charval(val)
        return val

    def put(self,value,**kw):
        if not self.connect():  return None
        return ca.put(self.chid,value,**kw)

    def set_charval(self,val,ca_calls=True):
        """ set the character representation of the value"""
        cval = repr(val)       
        ftype = self.ftype 
        if self.count > 1:
            if ftype == dbr.CHAR:
                cval = ''.join([chr(i) for i in val]).rstrip()
            else:
                cval = '<array size=%d, type=%s>' % (len(val),
                                                     dbr.Name(ftype))
        elif ftype in (dbr.FLOAT, dbr.DOUBLE):
            fmt  = "%%.%if"
            if ca_calls and self.precision is None:
                self.get_ctrlvars()
            try: 
                if 4 < abs(int(math.log10(abs(val + 1.e-9)))):
                    fmt = "%%.%ig"
                cval = (fmt % self.precision) % val                    
            except:
                cval = repr(val)
        elif ftype == dbr.ENUM:
            if ca_calls and self.enum_strs in ([], None):
                self.get_ctrlvars()
            try:
                cval = self.enum_strs[val]
            except:
                pass
            
        self._charval =cval
        return self._charval


    def _getval(self):      return self._val
    def _putval(self,val):  return self.put(val)
    def _getchar(self):
        """ fetch the string representation of the value"""
        return self._charval

    value       = property(_getval,_putval,None,'value property')
    char_value  = property(_getchar,None,None,'value property')

    def get_ctrlvars(self):
        if not self.connect():  return None
        kw = ca.get_ctrlvars(self.chid)
        self.__set_ctrl_attrs(kw)
        return kw
    
    def __set_ctrl_attrs(self,kw):
        for attr in ('severity', 'timestamp', 'precision',
                     'units', 'enum_strs','no_str',
                     'upper_disp_limit', 'lower_disp_limit',
                     'upper_alarm_limit', 'upper_warning_limit',
                     'lower_warning_limit','lower_alarm_limit',
                     'upper_ctrl_limit', 'lower_ctrl_limit'):
            if attr in kw: setattr(self,attr,kw[attr])        

        
    def _onChanges(self, value=None, chid=None,
                   ftype=None, count=1, status=1, **kw):
        
        self.__set_ctrl_attrs(kw)
        self.timestamp = kw.get('timestamp',time.time())
        self.count  = count
        self.status = status
        self._val   = value
        self.set_charval(value,ca_calls=False)
        
        for fcn in self.callbacks:
            if callable(fcn):  fcn(pv=self)
            
    def poll(self,t1=1.e-3,t2=1.0):
        ca.poll(t1,t2)
            
    def add_callback(self,callback=None):
        if callable(callback):
            self.callbacks.append(callback)

    def __repr__(self):
        if self.pvname is None: return self.repr_unnamed
        if not self.connected:   return self.repr_unconnected % self.pvname
        return self.repr_Normal % (self.pvname, self.count,
                                   dbr.Name(self.ftype).lower(),
                                   self.access)
    
    def __str__(self):
        return self.__repr__()

    def __eq__(self,other):
        try:
            return (self._chid  == other._chid)
        except:
            return False

    def get_info(self):
        if not self.connect():  return None
        kw = ca.get_ctrlvars(self.chid)
        self.__set_ctrl_attrs(kw)

        out = []

        # list basic attributes
        ftype = vtype = dbr.Name(self.ftype).lower()
        mod   = 'native'

        if '_' in ftype: mod,vtype = ftype.split('_')

        out.append("== %s  (%s)" % (self.pvname,ftype))

        if self.count==1:
            if vtype in  ('int','short','long','enum'):
                out.append('   value        = %i' % self._val)
            elif vtype in ('float','double'):
                out.append('   value        = %g' % self._val)
            elif vtype in ('string','char'):
                out.append('   value        = %s' % self._val)
        else:
            aval,ext,fmt = [],'',"%i,"
            if self._count>5: ext = '...'
            if vtype in  ('float','double'): fmt = "%g,"
            for i in range(min(5,self._count)):
                aval.append(fmt % self._val[i])
            out.append("   value        = array  [%s%s]" % ("".join(aval),ext))

        for i in ('char_value','count','type','units',
                  'precision','host','access',
                  'status','severity','timestamp',
                  'upper_ctrl_limit', 'lower_ctrl_limit',
                  'upper_disp_limit', 'lower_disp_limit',
                  'upper_alarm_limit', 'lower_alarm_limit',
                  'upper_warning_limit','lower_warning_limit',
                  ):
            if hasattr(self,i):
                att = getattr(self,i)
                if i == 'timestamp': att = "%.3f (%s)" % (att,fmt_time(att))
                if att is not None:
                    out.append('   %.13s= %s' % (i+' '*16, str(att)))

        # list enum strings
        if vtype == 'enum':
            out.append('   enum strings: ')
            for i,s in enumerate(self.enum_strs):
                out.append("       %i = %s " % (i,s))

        if self.__mondata is not None:
            out.append('   PV is monitored internally')
            # list callbacks
            if len(self.callbacks) > 0:
                out.append("   user-defined callbacks:")
                for i in cbs:  out.append('      %s' % (i.func_name))
            else:
                out.append("   no user callbacks defined.")
        else:
            out.append('   PV is not monitored internally')
        out.append('==')
        return '\n'.join(out)
        

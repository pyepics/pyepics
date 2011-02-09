#!/usr/bin/python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License
"""
basic device object defined
"""
from . import ca
from . import pv

class Device(object):
    """A simple collection of related PVs, sharing a common prefix
    string for their names, but having many 'attributes'.

    Many groups of PVs will have names made up of
         Prefix+Delimeter+Attribute
    with common Prefix and Delimeter, but a range of Attribute names.
    Many Epics Records follow this model, but a Device is only about
    PV names, and so is not exactly a mapping to an Epics Record.

    This class allows a collection of PVs to be represented simply.

      >>> dev = epics.Device('XX:m1', delim='.')
      >>> dev.put('OFF',0 )
      >>> dev.put('VAL', 0.25)
      >>> dev.get('RBV')
      >>> print dev.FOFF
      >>> print dev.get('FOFF', as_string=True)

    This will put a 0 to XX:m1.OFF, a 0.25 to XX:m1.VAL, and then
    get XX:m1.RBV and XX.m1.FOFF.

    Note access to the underlying PVs can either be with get()/put()
    methods or with attributes derived from the Attribute (Suffix) for
    that PV.  Thus
      >>> print dev.FOFF
      >>> print dev.get('FOFF')

    are equivalent, as are:
      >>> dev.VAL = 1
      >>> dev.put('VAL', 1)
    
    The methods do provide more options.  For example, to get the PV
    value as a string,
       Device.get(Attribute, as_string=True)
    must be used.   To put-with-wait, use
       Device.put(Attribute, value, wait=True)
        
    The list of attributes can be pre-loaded at initialization time.


    The attribute PVs are built as needed and held in an internal
    buffer (self._pvs).  This class is kept intentionally simple
    so that it may be subclassed.

    To pre-load attribute names on initialization, provide a
    list or tuple of attributes:

      >>> struck = epics.Device('13IDC:str:',
      ...                       attrs=('ChannelAdvance',
      ...                              'EraseStart','StopAll'))
      >>> print struck.PV('ChannelAdvance').char_value
      'External'

    The prefix is optional, and when left off, this class can
    be used as an arbitrary container of PVs, or to turn
    any subclass into an epics Device:

      >>> class MyClass(epics.Device):
      ...     def __init__(self,**kw):
      ...         epics.Device.__init__() # no Prefix!!
      ...
      >>> x = MyClass()
      >>> pv_m1 = x.PV('13IDC:m1.VAL')
      >>> x.put('13IDC:m3.VAL', 2)
      >>> print x.PV('13IDC:m3.DIR').get(as_string=True)

    you can all get
    """

    _prefix = None
    _delim = ''
    _pvs = {}
    _init = False
    _nonpvs = ('_prefix', '_pvs', '_delim', '_init')
    def __init__(self, prefix='', attrs=None,
                 nonpvs=None, delim='', timeout=None):
        self._nonpvs = list(self._nonpvs)[:]
        self._delim = delim
        self._prefix = prefix + delim
        self._pvs = {}
        if nonpvs is not None:
            for npv in nonpvs:
                if npv not in self._nonpvs:
                    self._nonpvs.append(npv)

        if attrs is not None:
            for attr in attrs:
                self.PV(attr, connect=False,
                        connection_timeout=timeout)
        ca.poll()
        self._init = True
        
    def PV(self, attr, connect=True, **kw):
        """return epics.PV for a device attribute"""
        if attr not in self._pvs:
            pvname = attr
            if self._prefix is not None: 
                pvname = "%s%s" % (self._prefix, attr)
            self._pvs[attr] = pv.PV(pvname, **kw)
        if connect and not self._pvs[attr].connected:
            self._pvs[attr].wait_for_connection()
        return self._pvs[attr]

    def add_pv(self, pvname, attr=None, **kw):
        """add a PV with an optional attribute name that may not exactly
        correspond to the mapping of Attribute -> Prefix + Delim + Attribute
        That is, with a device defined as
        >>> dev = Device('XXX', delim='.')

        getting the VAL attribute
        >>> dev.get('VAL')   # or dev.VAL

        becomes   'caget(XXX.VAL)'.  With add_pv(), one can add a
        non-conforming PV to the collection:
        >>> dev.add_pv('XXX_status.VAL', attr='status')

        and then use as
        >>> dev.get('status')  # or dev.status

        If attr is not specified, the full pvname will be used.
        """
        if attr is None:
            attr = pvname
        self._pvs[attr] = pv.PV(pvname, **kw)
        return self._pvs[attr]
    
    def put(self, attr, value, wait=False, timeout=10.0):
        """put an attribute value, 
        optionally wait for completion or
        up to a supplied timeout value"""
        thispv  =self.PV(attr)
        thispv.wait_for_connection()
        return thispv.put(value, wait=wait, timeout=timeout)
        
    def get(self, attr, as_string=False):
        """get an attribute value, 
        option as_string returns a string representation"""
        return self.PV(attr).get(as_string=as_string)
    
    def get_all(self):
        """return a dictionary of the values of all
        current attributes"""
        out = {}
        for key in self._pvs:
            out[key] = self._pvs[key].get()
        return out

    def add_callback(self, attr, callback, **kws):
        """add a callback function to an attribute PV,
        so that the callback function will be run when
        the attribute's value changes"""
        self.PV(attr).get()
        return self.PV(attr).add_callback(callback, **kws)
        
    def remove_callbacks(self, attr, index=None):
        """remove a callback function to an attribute PV"""
        self.PV(attr).remove_callback(index=index)
        
            
    def __getattr__(self, attr):
        if attr in self._pvs:
            return self.get(attr)
        elif attr == '_Device__init':
            return False
        elif attr in self.__dict__:
            return self.__dict__[attr]
        elif self._init and not attr.startswith('__'):
            try:
                self.PV(attr)
                return self.get(attr)
            except:
                msg = "Device '%s' has no attribute '%s'"
                raise AttributeError(msg % (self._prefix, attr))
    
    def __setattr__(self, attr, val):
        if attr in self._nonpvs:
            self.__dict__[attr] = val
        elif attr in self._pvs:
            self.put(attr, val)
        elif self._init:
            try:
                self.PV(attr)
                return self.put(attr, val)
            except:
                msg = "Device '%s' has no attribute '%s'"
                raise AttributeError(msg % (self._prefix, attr))
        else:
            self.__dict__[attr] = val            
    def __repr__(self):
        "string representation"
        return "<Device '%s' %i attributes>" % (self._prefix,
                                                len(self._pvs))
    

    def pv_property(attr, as_string=False, wait=False, timeout=10.0):
        return property(lambda self:     \
                        self.get(attr, as_string=as_string),
                        lambda self,val: \
                        self.put(attr, val, wait=wait, timeout=timeout),
                        None, None)

#!/usr/bin/python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License

from . import ca
from . import pv

class Device(object):
    """A simple collection of related PVs, all sharing a prefix,
    but having many 'attributes'. This almost describes an
    Epics Record, but as it is concerned only with PV names,
    the mapping to an Epics Record is not exact.

    Many PVs will have names made up of prefix+attribute, with
    a common prefix for several related PVs.  This class allows
    this case to be represented simply such as with:

      >>> struck = epics.Device('13IDC:str:')
      >>> struck.put('EraseStart',1)
      >>> time.sleep(1)
      >>> struck.put('StopAll',1)
      >>> struck.get('mca1')

    This will put a 1 to 13IDC:str:EraseStart, wait, put a 1
    to 13IDC:str:StopAll, then read 13IDC:str:mca1

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
    """
    def __init__(self,prefix=None,attrs=None):
        self.__prefix__ = prefix 
        self._pvs = {}
        if attrs is not None:
            for p in attrs: self.PV(p)
        ca.poll()
        
    def PV(self,attr):
        """return epics.PV for a device attribute"""
        pvname = attr        
        if self.__prefix__ is not None: 
            pvname = "%s%s" % (self.__prefix__, attr)
        if pvname not in self._pvs:
            self._pvs[pvname] = pv.PV(pvname)
            ca.poll()
        return self._pvs[pvname]
    
    def put(self,attr,value,wait=False,timeout=10.0):
        """put an attribute value, 
        optionally wait for completion or
        up to a supplied timeout value"""
        return self.PV(attr).put(value,wait=wait,timeout=timeout)
        
    def get(self,attr,as_string=False):
        """get an attribute value, 
        option as_string returns a string representation"""
        return self.PV(attr).get(as_string=as_string)

    def add_callback(self,attr,callback):
        """add a callback function to an attribute PV,
        so that the callback function will be run when
        the attribute's value changes"""
        self.PV(attr).get()
        self.PV(attr).add_callback(callback)
        
    def pv_property(attr, as_string=False,wait=False,timeout=10.0):
        """function to turn a device attribute PV into a property:

        use in your subclass as:
        
        >>> class MyDevice(epics.device):
        >>>     def __init__(self,prefix):
        >>>         epics.Device.__init__(self)
        >>>         self.PV('something')
        >>>     field = pv_property('something', as_string=True)

        then use in code as

        >>> m = MyDevice()
        >>> print m.field
        >>> m.field = new_value
        
        """
        return property(lambda self:     self.get(attr,as_string=as_string),
                        lambda self,val: self.put(attr,val,wait=wait,timeout=timeout),
                        None, None)

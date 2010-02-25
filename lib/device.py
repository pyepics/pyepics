#!/usr/bin/python

import epics

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
    """
    def __init__(self,prefix):
        self.prefix=prefix
        self._pvs = {}
        
    def PV(self,attr):
        """return epics.PV for a device attribute"""
        pvname = "%s%s" % (self.prefix, attr)
        if pvname not in self._pvs: 
            self._pvs[pvname] = epics.PV(pvname)
            self._pvs[pvname].get()
        return self._pvs[pvname]
    
    def put(self,attr,value,wait=False,timeout=10.0):
        """put an attribute value, 
        optionally wait for up to a supplied timeout"""
        return self.PV(attr).put(value,wait=wait,timeout=timeout)
        
    def get(self,attr,as_string=False):
        """get an attribute value, 
        option as_string returns a string representation"""
        return self.PV(attr).get(as_string=as_string)


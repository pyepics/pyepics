#!/usr/bin/python

import epics
import time

class Record(object):
    """keeps a collection of PVs for an Epics record,
    All PVs share a prefix, and can be retrieved by 'attribute',

    the real PV will have a name of prefix+attribute, so that

      >>> struck = epics.Record('13IDC:str:')
      >>> struck.put('EraseStart',1)
      
    will put a 1 to 13IDC:str:EraseStart

    The attribute PVs are held in an internal buffer.
    """
    def __init__(self,prefix):
        self.prefix=prefix
        self._pvs = {}
        
    def PV(self,attr):
        """return epics.PV for a record attribute"""
        pvname = "%s%s" % (self.prefix, attr)
        if pvname not in self._pvs: 
            self._pvs[pvname] = epics.PV(pvname)
            self._pvs[pvname].get()
        return self._pvs[pvname]
    
    def put(self,attr,value,wait=False,timeout=10.0):
        """put an attributes value, 
            optionally wait for up to a supplied timeout"""
        return self.PV(attr).put(value,wait=wait,timeout=timeout)
        
    def get(self,attr,as_string=False):
        """get an attributes value, 
           option as_string returns a string representation"""
        return self.PV(attr).get(as_string=as_string)


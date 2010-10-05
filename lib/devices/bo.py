#!/usr/bin/python 
import epics

class bo(epics.Device):
    """ 
    Simple binary output device
    """

    _fields = ('DOL', 'OMSL', 'RVAL', 'HIGH', 'ZNAM', 'ONAM', 'VAL', 'EGU',
               'HOPR', 'LOPR', 'PREC', 'NAME', 'DESC', 'DTYP')
    
    def __init__(self, prefix):
        if not prefix.endswith('.'):
            prefix = "%s." % prefix
        epics.Device.__init__(self, prefix, self._fields)

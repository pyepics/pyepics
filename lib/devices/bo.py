#!/usr/bin/python 
import epics

class bo(epics.Device):
    """ 
    Simple binary output device
    """

    attrs = ('DOL', 'OMSL', 'RVAL', 'HIGH', 'ZNAM', 'ONAM', 'VAL', 'EGU',
               'HOPR', 'LOPR', 'PREC', 'NAME', 'DESC', 'DTYP')
    
    def __init__(self, prefix):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        epics.Device.__init__(self, prefix, delim='.',
                              attrs=self.attrs)

#!/usr/bin/python 
import epics

class bi(epics.Device):
    """ 
    Simple binary input device
    """

    attrs = ('INP', 'ZNAM', 'ONAM', 'RVAL', 'VAL', 'EGU', 'HOPR', 'LOPR',
               'PREC', 'NAME', 'DESC', 'DTYP')

    def __init__(self, prefix):
        if not prefix.endswith('.'):
            prefix = "%s." % prefix
        epics.Device.__init__(self, prefix, attrs=self.attrs)



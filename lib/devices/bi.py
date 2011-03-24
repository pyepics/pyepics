#!/usr/bin/python 
import epics

class bi(epics.Device):
    """ 
    Simple binary input device
    """

    attrs = ('INP', 'ZNAM', 'ONAM', 'RVAL', 'VAL', 'EGU', 'HOPR', 'LOPR',
               'PREC', 'NAME', 'DESC', 'DTYP')

    def __init__(self, prefix):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        epics.Device.__init__(self, prefix, delim='.',
                              attrs=self.attrs)



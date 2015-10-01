#!/usr/bin/ao python
from .. import Device

class ao(Device):
    "Simple analog output device"

    attrs = ('OUT', 'LINR', 'RVAL', 'ROFF', 'EGUF', 'EGUL', 'AOFF',
               'ASLO', 'ESLO', 'EOFF', 'VAL', 'EGU', 'HOPR', 'LOPR',
               'PREC', 'NAME', 'DESC', 'DTYP', 'HIHI', 'LOLO', 'HIGH',
               'LOW', 'HHSV', 'LLSV', 'HSV', 'LSV', 'HYST', 'OMSL', 'DOL',
               'OIF', 'DRVH', 'DRVL', 'OROC', 'OVAL')

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Device.__init__(self, prefix, delim='.', attrs=self.attrs, **kwargs)

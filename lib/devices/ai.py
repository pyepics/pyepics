#!/usr/bin/python
import epics  

class ai(epics.Device):
    "Simple analog input device"
    _fields = ('VAL','EGU','HOPR','LOPR','PREC','NAME',
               'DESC','DTYP','INP','LINR','RVAL','ROFF',
               'EGUF','EGUL','AOFF','ASLO','ESLO','EOFF',
               'SMOO', 'HIHI','LOLO','HIGH','LOW','HHSV',
               'LLSV','HSV','LSV','HYST')
    def __init__(self, prefix):
        if not prefix.endswith('.'):
            prefix = "%s." % prefix
        epics.Device.__init__(self, prefix, self._fields)

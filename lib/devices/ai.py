#!/usr/bin/python
"""Epics analog input record"""
import epics  

class ai(epics.Device):
    "Simple analog input device"

    attrs = ('VAL', 'EGU', 'HOPR', 'LOPR', 'PREC', 'NAME', 'DESC',
             'DTYP', 'INP', 'LINR', 'RVAL', 'ROFF', 'EGUF', 'EGUL',
             'AOFF', 'ASLO', 'ESLO', 'EOFF', 'SMOO', 'HIHI', 'LOLO',
             'HIGH', 'LOW', 'HHSV', 'LLSV', 'HSV', 'LSV', 'HYST')

    def __init__(self, prefix):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        epics.Device.__init__(self, prefix, delim='.',
                              attrs=self.attrs)

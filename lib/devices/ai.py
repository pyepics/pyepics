#!/usr/bin/env python
"""Epics analog input record"""
from .. import Device

class ai(Device):
    "Simple analog input device"

    attrs = ('VAL', 'EGU', 'HOPR', 'LOPR', 'PREC', 'NAME', 'DESC',
             'DTYP', 'INP', 'LINR', 'RVAL', 'ROFF', 'EGUF', 'EGUL',
             'AOFF', 'ASLO', 'ESLO', 'EOFF', 'SMOO', 'HIHI', 'LOLO',
             'HIGH', 'LOW', 'HHSV', 'LLSV', 'HSV', 'LSV', 'HYST')

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Device.__init__(self, prefix, delim='.', attrs=self.attrs, **kwargs)

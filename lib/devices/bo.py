#!/usr/bin/env python
from .. import Device

class bo(Device):
    """
    Simple binary output device
    """

    attrs = ('DOL', 'OMSL', 'RVAL', 'HIGH', 'ZNAM', 'ONAM', 'VAL', 'EGU',
               'HOPR', 'LOPR', 'PREC', 'NAME', 'DESC', 'DTYP')

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Device.__init__(self, prefix, delim='.', attrs=self.attrs, **kwargs)

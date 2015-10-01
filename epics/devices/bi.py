#!/usr/bin/env python
from .. import Device

class bi(Device):
    """
    Simple binary input device
    """

    attrs = ('INP', 'ZNAM', 'ONAM', 'RVAL', 'VAL', 'EGU', 'HOPR', 'LOPR',
               'PREC', 'NAME', 'DESC', 'DTYP')

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Device.__init__(self, prefix, delim='.', attrs=self.attrs, **kwargs)



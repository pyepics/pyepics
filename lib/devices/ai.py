#!/usr/bin/python 
import epics

class AI(epics.Device):
    """ 
    Simple AI device
    
    """
    attrs = ('VAL', 'INP', 'DTYP', 'EGU','HOPR','LOPR','PREC','NAME','DESC',
             'LINR','RVAL','ROFF','EGUF','EGUL')

    def __init__(self,prefix,nchan=8):
        if not prefix.endswith('.'): prefix = "%s." % prefix
        epics.Device.__init__(self,prefix,   attrs=self.attrs)
        epics.poll()
        

#!/usr/bin/python 
import epics

class Mca(epics.Device):
    """ 
    SynApps Mca Record.   
    """
    _fields = ('CALO', 'CALS', 'CALQ', 'TTH', 'EGU' , 'PRTM', 'PLTM',
               'PCT', 'PCTL', 'PCTH', 'CHAS', 'DWEL', 'PSCL', 'ERTM', 'ELTM',
               'ACT' , 'RTIM', 'STIM',  'STRT', 'STOP', 'ERAS', 'ACQG', 'PROC',
               'ERST', 'NUSE', 'NMAX', 'VAL')
    
    def __init__(self,prefix):
        if not prefix.endswith('.'):
            prefix = "%s." % prefix
        epics.Device.__init__(self,prefix,self._fields)

    def Read(self):
        attr = 'VAL'
        return self.get(attr)


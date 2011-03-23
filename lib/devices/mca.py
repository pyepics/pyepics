#!/usr/bin/python 
"""Epics multichannel analyzer record"""
import epics

class Mca(epics.Device):
    """ 
    SynApps Mca Record.   
    """
    attrs = ('CALO', 'CALS', 'CALQ', 'TTH', 'EGU' , 'PRTM', 'PLTM',
             'PCT', 'PCTL', 'PCTH', 'CHAS', 'DWEL', 'PSCL', 'ERTM', 'ELTM',
             'ACT' , 'RTIM', 'STIM',  'STRT', 'STOP', 'ERAS', 'ACQG', 'PROC',
             'ERST', 'NUSE', 'NMAX', 'VAL')
    
    def __init__(self, prefix):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        epics.Device.__init__(self, prefix, delim='.',
                              attrs= self.attrs)

    def Read(self):
        "return value"
        attr = 'VAL'
        return self.get(attr)

    def calibratio(self):
        """return calibration values:
        CALO, CALS, CALQ, TTH
        """
        return (self.get('CALO'), self.get('CALS'),
                self.get('CALQ'), self.get('TTH'))

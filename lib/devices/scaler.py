#!/usr/bin/python 
import epics

class Scaler(epics.Device):
    """ 
    Simple implementation of Joerger Scaler. Principle methods:
    
    """
    attrs = ('.CNT','.CONT','.TP','.T','_calcEnable.VAL')
    chan_attrs = ('.NM%i', '.S%i','_calc%i.VAL', '_calc%i.CALC')

    def __init__(self,prefix,nchan=8):
        epics.Device.__init__(self,prefix,
                              attrs=self.attrs)
        self.prefix = prefix
        self.nchan  = nchan
        for i in range(1,nchan+1):
            for a in self.chan_attrs:
                self.PV(a % i)
        
    def AutoCountMode(self):
        self.put('.CONT', 1)

    def OneShotMode(self):
        self.put('.CONT', 0)

    def Count(self, t=None):
        if t is not None:
            self.put('.TP', t)
        self.put('.CNT', 1)

    def EnableCalcs(self):
        self.put('_calcEnable.VAL', 1)

    def setCalc(self,i,s):
        attr = '_calc%i.CALC'  % i
        self.put(attr, s)

    def getNames(self):
        return [self.get('.NM%i' %i) for i in range(self.nchan)]

    def Read(self, use_calc=False):
        attr = '.S%i'
        if use_calc: attr = '_calc%i.VAL'
        return [self.get(attr %i) for i in range(self.nchan)]


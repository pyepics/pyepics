#!/usr/bin/python 
import epics

class Scaler(epics.Device):
    """ 
    Simple implementation of SynApps Scaler Record.   
    """
    attrs = ('.CNT', '.CONT', '.TP', '.T', '_calcEnable.VAL')
    chan_attrs = ('.NM%i', '.S%i', '_calc%i.VAL', '_calc%i.CALC')

    def __init__(self, prefix, nchan=8):
        epics.Device.__init__(self, prefix, attrs=self.attrs)
        self.put = epics.Device.put
        self.get = epics.Device.get
        self.PV  = epics.Device.PV
        self.prefix = prefix
        self.nchan  = nchan
        self.chans  = list(range(1, nchan+1))
        for a in self.chan_attrs:
            [self.PV(a % i) for i in self.chans]
        
    def AutoCountMode(self):
        "set to autocount mode"
        self.put('.CONT', 1)

    def OneShotMode(self):
        "set to one shot mode"        
        self.put('.CONT', 0)

    def CountTime(self, ctime):
        "set count time"
        self.put('.TP', ctime)
        
    def Count(self, ctime=None):
        "set count, with optional counttime"
        if ctime is not None:
            self.CountTime(ctime)
        self.put('.CNT', 1)

    def EnableCalcs(self):
        " enable calculations"
        self.put('_calcEnable.VAL', 1)

    def setCalc(self, i, calc):
        "set the calculation for scaler i"
        attr = '_calc%i.CALC'  % i
        self.put(attr, calc)

    def getNames(self):
        "get all names"
        return [self.get('.NM%i' % i) for i in self.chans]

    def Read(self, use_calc=False):
        "read all values"
        attr = '.S%i'
        if use_calc:
            attr = '_calc%i.VAL'
        return [self.get(attr % i) for i in self.chans]

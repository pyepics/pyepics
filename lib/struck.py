#!/usr/bin/python 
import epics
import numpy

class Scaler(epics.Device):
    attrs = ('.CNT','.CONT','.TP')
    chan_attrs = ('.NM%i','.S%i','_calc%i.VAL')
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

    def Count(self):
        self.put('.CNT', 1)


class Struck(epics.Device):
    """ 
    Very simple implementation of Struck STR7201 MultiChannelScaler
    
    """
    attrs = ('ChannelAdvance','Prescale','EraseStart','StopAll',
             'PresetReal','Dwell')
    
    def __init__(self,prefix,scaler=None,nchan=8):
        epics.Device.__init__(self,prefix,
                              attrs=self.attrs)
        self.prefix = prefix
        self.nchan  = nchan
        self.scaler = None
        if scaler is not None:
            self.scaler = Scaler(scaler,nchan=nchan)
        
    def ExternalMode(self,prescale=None):
        "put Struck in External Mode"
        o = self.put('ChannelAdvance', 1)  # external
        if self.scaler is not None: self.scaler.OneShotMode()
        if prescale is not None:
            self.put('Prescale',prescale)
        return o
        
    def InternalMode(self,prescale=None):
        "put Struck in Internal Mode"        
        o = self.put('ChannelAdvance', 0)  # internal
        if self.scaler is not None: self.scaler.OneShotMode()
        if prescale is not None:
            self.put('Prescale',prescale)
        return o
        
    def PresetReal(self,val):
        "Set Preset Real Tiem"
        return self.put('PresetReal',val)

    def Dwell(self,val):
        "Set Dwell Time"
        return self.put('Dwell',val)    

    def AutoCountMode(self):
        if self.scaler is not None: self.scaler.AutoCountMode()
        
    def start(self):
        "Start Struck"
        if self.scaler is not None: self.scaler.OneShotMode()        
        return self.put('EraseStart',1)

    def stop(self):
        "Stop Struck Collection"
        return self.put('StopAll',1)

    def readmca(self,n=1):
        "Read a Struck MCA"
        return self.get('mca%i' % n)

    def saveMCAdata(self,fname='Struck.dat', mcas=None,
                    ignore_prefix=None,  npts=None):
        sdata = []
        names = []
        addrs = []
        if mcas is None: mcas = range(1,self.nchan+1)
        for n in mcas:
            if self.scaler is not None:
                scaler_name = self.scaler.get('.NM%i' % n)
                if len(scaler_name) > 0:
                    if (ignore_prefix is not None and
                        scaler_name.startswith(ignore_prefix)):
                        continue
                    sdata.append(self.readmca(n=n))
                    names.append(scaler_name.replace(' ','_'))
                    addrs.append(self.scaler.prefix + '.S%i' % n)

            else:
                sdata.append(self.readmca(n=n))
                names.append(' MCA%i ' % n)
        sdata = numpy.array(sdata).transpose()

        nelem,nmca = sdata.shape
        
        if npts is not None:
            npts = min(nelem,npts+1)
        fout  = open(fname,'w')
        fout.write('# Struck MCA data: %s \n' % self.prefix)
        fout.write('# Nchannels, Nmca = %i, %i\n' % (nelem,nmca))
        fout.write('#----------------------\n')
        fout.write('# %s\n' % (' | '.join(addrs)))
        fout.write('# %s\n' % (' | '.join(names)))
        fmt   =  '%9i ' * nmca + '\n'
        
        [fout.write(fmt % tuple(sdata[i])) for i in range(npts)]
        fout.close()

    
if __name__ == '__main__':
    s = Struck('13IDC:str:')
    a = 'ChannelAdvance'
    print "%s = %s " % (a, s.PV(a).char_value)

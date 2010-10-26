#!/usr/bin/python 
import epics
import epics.devices 
import numpy

class Struck(epics.Device):
    """ 
    Very simple implementation of Struck STR7201 MultiChannelScaler
    
    """
    attrs = ('ChannelAdvance', 'Prescale', 'EraseStart', 'StopAll',
             'PresetReal', 'Dwell')

    _fields = ('_prefix', '_pvs', '_delim', '_nchan', 'scaler')
    
    def __init__(self, prefix, scaler=None, nchan=8):
        self._nchan = nchan
        self.scaler = None
        epics.Device.__init__(self, prefix, delim=':',
                              attrs=self.attrs)
        if scaler is not None:
            self.scaler = epics.devices.Scaler(scaler, nchan=nchan)
        
    def ExternalMode(self, prescale=None):
        "put Struck in External Mode"
        out = self.put('ChannelAdvance', 1)  # external
        if self.scaler is not None:
            self.scaler.OneShotMode()
        if prescale is not None:
            self.put('Prescale', prescale)
        return out
        
    def InternalMode(self, prescale=None):
        "put Struck in Internal Mode"        
        out = self.put('ChannelAdvance', 0)  # internal
        if self.scaler is not None:
            self.scaler.OneShotMode()
        if prescale is not None:
            self.put('Prescale', prescale)
        return out
        
    def setPresetReal(self, val):
        "Set Preset Real Tiem"
        return self.put('PresetReal', val)

    def setDwell(self, val):
        "Set Dwell Time"
        return self.put('Dwell', val)    

    def AutoCountMode(self):
        "set auto count mode"
        if self.scaler is not None:
            self.scaler.AutoCountMode()
        
    def start(self):
        "Start Struck"
        if self.scaler is not None:
            self.scaler.OneShotMode()        
        return self.put('EraseStart', 1)

    def stop(self):
        "Stop Struck Collection"
        return self.put('StopAll', 1)

    def readmca(self, nmca=1):
        "Read a Struck MCA"
        return self.get('mca%i' % nmca)

    def saveMCAdata(self, fname='Struck.dat', mcas=None,
                    ignore_prefix=None, npts=None):
        "save MCA spectra to ASCII file"
        sdata = []
        names = []
        addrs = []
        if mcas is None:
            mcas = list(range(1, self.nchan+1))
        for nmca in mcas:
            if self.scaler is not None:
                scaler_name = self.scaler.get('NM%i' % nmca)
                if len(scaler_name) > 0:
                    if (ignore_prefix is not None and
                        scaler_name.startswith(ignore_prefix)):
                        continue
                    sdata.append(self.readmca(nmca=nmca))
                    names.append(scaler_name.replace(' ', '_'))
                    addrs.append(self.scaler.prefix + 'S%i' % nmca)

            else:
                sdata.append(self.readmca(nmca=nmca))
                names.append(' MCA%i ' % nmca)
        sdata = numpy.array(sdata).transpose()

        nelem, nmca = sdata.shape
        
        if npts is None:
            npts = nelem
        npts = min(nelem, npts)
        fout = open(fname, 'w')
        fout.write('# Struck MCA data: %s \n' % self.prefix)
        fout.write('# Nchannels, Nmca = %i, %i\n' % (npts, nmca))
        fout.write('#----------------------\n')
        fout.write('# %s\n' % (' | '.join(addrs)))
        fout.write('# %s\n' % (' | '.join(names)))
        fmt   =  '%9i ' * nmca + '\n'
        
        [fout.write(fmt % tuple(sdata[i])) for i in range(npts)]
        fout.close()
    
if __name__ == '__main__':
    import sys
    strk = Struck('13IDC:str:')
    adv = 'ChannelAdvance'
    sys.stdout.write("%s = %s\n" % (adv, strk.PV(adv).char_value))

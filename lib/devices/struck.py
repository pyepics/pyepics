#!/usr/bin/env python
import sys
import time
import copy
import numpy
from .. import Device
from .scaler import Scaler
from .mca import MCA

HEADER = '''# Struck MCA data: %s
# Nchannels, Nmca = %i, %i
# Time in microseconds
#----------------------
# %s
# %s
'''

class Struck(Device):
    """
    Very simple implementation of Struck SIS MultiChannelScaler
    """
    attrs = ('ChannelAdvance', 'Prescale', 'EraseStart',
             'EraseAll', 'StartAll', 'StopAll',
             'PresetReal', 'ElapsedReal',
             'Dwell', 'Acquiring', 'NuseAll',
             'CurrentChannel', 'CountOnStart',   # InitialChannelAdvance',
             'SoftwareChannelAdvance', 'Channel1Source',
             'ReadAll', 'DoReadAll', 'Model', 'Firmware')

    _nonpvs  = ('_prefix', '_pvs', '_delim', '_nchan',
               'clockrate', 'scaler', 'mcas')

    def __init__(self, prefix, scaler=None, nchan=8, clockrate=50.0):
        if not prefix.endswith(':'):
            prefix = "%s:" % prefix
        self._nchan = nchan
        self.scaler = None
        self.clockrate = clockrate # clock rate in MHz

        if scaler is not None:
            self.scaler = Scaler(scaler, nchan=nchan)

        self.mcas = []
        for i in range(nchan):
            self.mcas.append(MCA(prefix, mca=i+1, nrois=2))

        Device.__init__(self, prefix, delim='',
                              attrs=self.attrs, mutable=False)

    def ExternalMode(self, countonstart=0, initialadvance=None,
                     realtime=0, prescale=1):
        """put Struck in External Mode, with the following options:
        option            meaning                   default value
        ----------------------------------------------------------
        countonstart    set Count on Start             0
        initialadvance  set Initial Channel Advance    None
        reatime         set Preset Real Time           0
        prescale        set Prescale value             1
        """
        out = self.put('ChannelAdvance', 1)  # external
        if self.scaler is not None:
            self.scaler.OneShotMode()
        if realtime is not None:
            self.put('PresetReal', realtime)
        if prescale is not None:
            self.put('Prescale', prescale)
        if countonstart is not None:
            self.put('CountOnStart', countonstart)
        if initialadvance is not None:
            self.put('InitialChannelAdvancel', initialadvance)

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

    def erase(self):
        "Start Struck"
        return self.put('EraseAll', 1)

    def mcaNread(self, nmca=1):
        "Read a Struck MCA"
        return self.get('mca%i.NORD' % nmca)

    def readmca(self, nmca=1, count=None):
        "Read a Struck MCA"
        return self.get('mca%i' % nmca, count=count)

    def read_all_mcas(self):
        return [self.readmca(nmca=i+1) for i in range(self._nchan)]

    def saveMCAdata(self, fname='Struck.dat', mcas=None,
                    ignore_prefix=None, npts=None):
        "save MCA spectra to ASCII file"
        sdata, names, addrs = [], [], []
        npts =  1.e99
        time.sleep(0.005)
        for nchan in range(self._nchan):
            nmca  = nchan + 1
            _name = 'MCA%i' % nmca
            _addr = '%s.MCA%i' % (self._prefix, nmca)
            time.sleep(0.002)
            if self.scaler is not None:
                scaler_name = self.scaler.get('NM%i' % nmca)
                if scaler_name is not None:
                    _name = scaler_name.replace(' ', '_')
                    _addr = self.scaler._prefix + 'S%i' % nmca
            mcadat = self.readmca(nmca=nmca)
            npts = min(npts, len(mcadat))
            if len(_name) > 0 or sum(mcadat) > 0:
                names.append(_name)
                addrs.append(_addr)
                sdata.append(mcadat)

        sdata = numpy.array([s[:npts] for s in sdata]).transpose()
        sdata[:, 0] = sdata[:, 0]/self.clockrate

        nelem, nmca = sdata.shape
        npts = min(nelem, npts)

        addrs = ' | '.join(addrs)
        names = ' | '.join(names)
        formt = '%9i ' * nmca + '\n'

        fout = open(fname, 'w')
        fout.write(HEADER % (self._prefix, npts, nmca, addrs, names))
        for i in range(npts):
            fout.write(formt % tuple(sdata[i]))
        fout.close()
        return (nmca, npts)

if __name__ == '__main__':
    strk = Struck('13IDE:SIS1:')
    adv = 'ChannelAdvance'
    sys.stdout.write("%s = %s\n" % (adv, strk.PV(adv).char_value))

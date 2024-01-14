#!/usr/bin/python
import sys
import time
import numpy as np
from configparser import  ConfigParser
from epics.utils import IOENCODING

from .. import Device, get_pv, poll, caput, caget

MAX_ROIS = 32
class DXP(Device):
    _attrs = ('PreampGain','MaxEnergy','ADCPercentRule','BaselineCutPercent',
              'BaselineThreshold','BaselineFilterLength','BaselineCutEnable',
              'InputCountRate', 'OutputCountRate',
              'GapTime','PeakingTime','EnergyThreshold','MaxWidth',
              'PresetMode', 'TriggerPeakingTime',
              'TriggerGapTime','TriggerThreshold')

    def __init__(self,prefix,mca=1):
        self._prefix = "%sdxp%i" % (prefix, mca)
        Device.__init__(self, self._prefix, delim=':')
        poll()


class ROI(Device):
    """epics ROI device for MCA record

    >>> from epics.devices.mca import ROI, MCA
    >>> r = ROI('PRE:mca1', roi=1)
    >>> print r.name, r.left, r.right

    arguments
    ---------
    prefix     MCA record prefix
    roi        integer for ROI (0 through 31)
    bgr_width  width in bins for calculating NET counts
    data_pv    optional PV name to read counts from (not needed
               for most MCA records, but useful for some)

    attribute (read/write)
    ----------------------
    LO, left    low bin for ROI
    HI, right   high bin for ROI
    NM, name    name

    properties (read only)
    -----------------------
    center     roi center bin
    width      roi width (in bins)
    address    == prefix
    total      sum counts in ROI
    net        background-subtracted sum counts in ROI

    methods
    -------
    clear     remove ROI
    """

    _nonpvs = ('_prefix', '_pvs', '_delim', 'attrs', 'width', 'center',
               'bgr_width', 'address', 'net', 'total', '_dat_', '_net_')
    _aliases = {'left': 'LO', 'right': 'HI', 'name': 'NM'}
    def __init__(self, prefix, roi=0, bgr_width=3, data_pv=None):
        self.address = self._prefix = '%s.R%i' % (prefix, roi)
        self.bgr_width = bgr_width
        _attrs = ('NM', 'LO', 'HI')
        Device.__init__(self,self._prefix, delim='',
                        attrs=_attrs, aliases=self._aliases,
                        with_poll=False)
        if data_pv is None:
            data_pv = self.address
        if isinstance(data_pv, basestring):
            data_pv = get_pv(data_pv)
        self._pvs['_dat_'] = data_pv
        self._pvs['_net_'] = get_pv(self.address + 'N')

    def __eq__(self, other):
        """used for comparisons"""
        return (self.LO == getattr(other, 'LO', None) and
                self.HI == getattr(other, 'HI', None) and
                self.bgr_width == getattr(other, 'bgr_width', None) )

    def __ne__(self, other): return not self.__eq__(other)
    def __lt__(self, other): return self.LO <  getattr(other, 'LO', None)
    def __le__(self, other): return self.LO <= getattr(other, 'LO', None)
    def __gt__(self, other): return self.LO >  getattr(other, 'LO', None)
    def __ge__(self, other): return self.LO >= getattr(other, 'LO', None)

    def __repr__(self):
        "string representation"
        pref = self._prefix
        if pref.endswith('.'):
            pref = pref[:-1]
        return "<ROI '%s', name='%s', range=[%s:%s]>" % (pref, self.NM,
                                                         self.LO, self.HI)

        #return "<ROI '%s', name='%s', range=[%i:%i]>" % (pref, self.NM,
        #                                                 self.LO, self.HI)

    @property
    def total(self):
        return self.get_counts(net=False)

    @property
    def sum(self):
        return self.get_counts(net=False)

    @property
    def net(self):
        return self.get_counts(net=True)

    @property
    def center(self):
        return int(round(self.HI + self.LO)/2.0)

    @property
    def width(self):
        return int(round(self.HI - self.LO))

    def clear(self):
        self.NM = ''
        self.LO = -1
        self.HI = -1

    def get_counts(self, data=None, net=False):
        """
        calculate total and net counts for a spectra

        Parameters:
        -----------
        * data: numpy array of spectra or None to read from PV
        * net:  bool to set net counts (default=False: total counts returned)
        """
        # implicitly read data from a PV
        if data is None and self._pvs['_dat_'] is not None:
            data = self._pvs['_dat_'].get()
            if net and not isinstance(data, np.ndarray):
                data = self._pvs['_net_'].get()
        if not isinstance(data, np.ndarray):
            return data

        total = data[self.LO:self.HI+1].sum()
        if not net:
            return total
        # calculate net counts
        bgr_width = int(self.bgr_width)
        ilmin = max((self.LO - bgr_width), 0)
        irmax = min((self.HI + bgr_width), len(data)-1) + 1
        bgr_counts = np.concatenate((data[ilmin:self.LO],
                                     data[self.HI+1:irmax])).mean()

        return (total - bgr_counts*(self.HI-self.LO))

class MCA(Device):
    _attrs =('CALO', 'CALS', 'CALQ', 'TTH', 'EGU',
             'PRTM', 'PLTM', 'ACQG', 'NUSE',  'DWEL',
             'ERTM', 'ELTM', 'IDTIM')
    _nonpvs = ('_prefix', '_pvs', '_delim',
               '_npts', 'rois', '_nrois', 'rois')

    def __init__(self, prefix, mca=None, nrois=None, data_pv=None):
        self._prefix = prefix
        self._npts = None
        self._nrois = nrois
        if self._nrois is None:
            self._nrois = MAX_ROIS
        self.rois = []
        if isinstance(mca, int):
            self._prefix = "%smca%i" % (prefix, mca)

        Device.__init__(self,self._prefix, delim='.',
                              attrs=self._attrs, with_poll=False)
        self._pvs['VAL'] = get_pv("%sVAL" % self._prefix, auto_monitor=False)

        self._pvs['_dat_'] = None
        if data_pv is not None:
            self._pvs['_dat_'] = get_pv(data_pv)
        poll()


    def get_rois(self, nrois=None):
        self.rois = []
        data_pv = self._pvs['_dat_']
        prefix = self._prefix
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        if nrois is None:
            nrois = self._nrois
        for i in range(nrois):
            roi = ROI(prefix=prefix, roi=i, data_pv=data_pv)
            if roi.NM is None:
                break
            if len(roi.NM.strip()) <= 0 or roi.HI <= 0:
                break
            self.rois.append(roi)
        poll()

        return self.rois

    def del_roi(self, roiname):
        self.get_rois()
        for roi in self.rois:
            if roi.NM.strip().lower() == roiname.strip().lower():
                roi.clear()
        poll(0.010, 1.0)
        self.set_rois(self.rois)

    def add_roi(self, roiname, lo=-1, hi=-1, calib=None):
        """add an roi, given name, lo, and hi channels, and
        an optional calibration other than that of this mca.

        That is, specifying an ROI with all of lo, hi AND calib
        will set the ROI **by energy** so that it matches the
        provided calibration.  To add an ROI to several MCAs
        with differing calibration, use

           cal_1 = mca1.get_calib()
           for mca im (mca1, mca2, mca3, mca4):
               mca.add_roi('Fe Ka', lo=600, hi=700, calib=cal_1)
        """
        if lo < 0 or hi <0:
            return
        rois = self.get_rois()
        try:
            iroi = len(rois)
        except:
            iroi = 0
        if iroi >= MAX_ROIS:
            raise ValueError('too many ROIs - cannot add more %i/%i' % (iroi, MAX_ROIS))
        data_pv = self._pvs['_dat_']
        prefix = self._prefix
        if prefix.endswith('.'): prefix = prefix[:-1]
        roi = ROI(prefix=prefix, roi=iroi, data_pv=self._pvs['_dat_'])
        roi.NM = roiname.strip()

        offset, scale = 0.0, 1.0
        if calib is not None:
            off, slope, quad = self.get_calib()
            offset = calib[0] - off
            scale  = calib[1] / slope

        roi.LO = round(offset + scale*lo)
        roi.HI = round(offset + scale*hi)
        rois.append(roi)
        self.set_rois(rois)

    def set_rois(self, rois, calib=None):
        """set all rois, with optional calibration that those
        ROIs correspond to (if they have a different energy
        calibration), and ensures they are ordered and contiguous.

        A whole set of ROIs can be copied by energy from one mca
        to another with:

           rois  = mca1.get_rois()
           calib = mca1.get_calib()
           mca2.set_rois(rois, calib=calib)
        """
        data_pv = self._pvs['_dat_']
        prefix = self._prefix
        if prefix.endswith('.'): prefix = prefix[:-1]

        offset, scale = 0.0, 1.0
        if calib is not None:
            off, slope, quad = self.get_calib()
            offset = calib[0] - off
            scale  = calib[1] / slope

        # do an explicit get here to make sure all data is
        # available before trying to sort it!
        poll(0.0050, 1.0)

        [(r.get('NM'), r.get('LO')) for r in rois]
        roidat = [(r.NM, r.LO, r.HI) for r in sorted(rois)]

        iroi = 0
        self.rois = []
        for name, lo, hi in roidat:
            if len(name)<1 or lo<0 or hi<0:
                continue
            roi = ROI(prefix=prefix, roi=iroi, data_pv=data_pv)
            roi.NM = name.strip()
            roi.LO = round(offset + scale*lo)
            roi.HI = round(offset + scale*hi)
            self.rois.append(roi)
            iroi += 1

        # erase any remaning ROIs
        for i in range(iroi, MAX_ROIS):
            lo = caget("%s.R%iLO" % (prefix, i))
            if lo < 0:
                break
            caput("%s.R%iLO" % (prefix, i), -1)
            caput("%s.R%iHI" % (prefix, i), -1)
            caput("%s.R%iNM" % (prefix, i), '')

    def clear_rois(self, nrois=None):
        for roi in self.get_rois(nrois=nrois):
            roi.clear()
        self.rois = []

    def get_calib(self):
        return [self.get(i) for i in ('CALO','CALS','CALQ')]

    def get_energy(self):
        if self._npts is None:
            self._npts = len(self.get('VAL'))

        en = np.arange(self._npts, dtype='f8')
        cal = self.get_calib()
        return cal[0] + en*(cal[1] + en*cal[2])


class MultiXMAP(Device):
    """
    multi-Channel XMAP DXP device
    """

    attrs = ['PresetReal','Dwell','Acquiring', 'EraseStart','StopAll',
             'PresetMode', 'PixelsPerBuffer_RBV', 'NextPixel',
             'PixelsPerRun', 'Apply', 'AutoApply', 'CollectMode',
             'SyncCount', 'BufferSize_RBV']

    pathattrs = ('FilePath', 'FileTemplate', 'FileWriteMode',
                 'FileName', 'FileNumber', 'FullFileName_RBV',
                 'Capture',  'NumCapture', 'WriteFile_RBV',
                 'AutoSave', 'EnableCallbacks',  'ArraySize0_RBV',
                 'FileTemplate_RBV', 'FileName_RBV', 'AutoIncrement')

    _nonpvs  = ('_prefix', '_pvs', '_delim', 'filesaver',
                'pathattrs', '_nonpvs', 'nmca', 'dxps', 'mcas')

    def __init__(self, prefix, filesaver='netCDF1:',nmca=4):
        self.filesaver = filesaver
        self._prefix = prefix
        self.nmca   = nmca

        self.dxps = [DXP(prefix, mca=i+1) for i in range(nmca)]
        self.mcas = [MCA(prefix, mca=i+1) for i in range(nmca)]

        Device.__init__(self, prefix, attrs=self.attrs,
                              delim='', mutable=True)
        for p in self.pathattrs:
            pvname = '%s%s%s' % (prefix, filesaver, p)
            self.add_pv(pvname, attr=p)

    def get_calib(self):
        return [m.get_calib() for m in self.mcas]

    def get_rois(self):
        return [m.get_rois() for m in self.mcas]

    def roi_calib_info(self):
        buff = ['[rois]']
        add = buff.append
        rois = self.get_rois()
        for iroi in range(len(rois[0])):
            name = rois[0][iroi].NM
            s = [[rois[m][iroi].LO, rois[m][iroi].HI] for m in range(self.nmca)]
            dat = repr(s).replace('],', '').replace('[', '').replace(']','').replace(',','')
            add("ROI%2.2i = %s | %s" % (iroi, name, dat))

        caldat = np.array(self.get_calib())
        add('[calibration]')
        add("OFFSET = %s " % (' '.join(["%.7g" % i for i in caldat[:, 0]])))
        add("SLOPE  = %s " % (' '.join(["%.7g" % i for i in caldat[:, 1]])))
        add("QUAD   = %s " % (' '.join(["%.7g" % i for i in caldat[:, 2]])))

        add('[dxp]')
        for a in self.dxps[0]._attrs:
            vals = [str(dxp.get(a, as_string=True)).replace(' ','_') for dxp in self.dxps]
            add("%s = %s" % (a, ' '.join(vals)))
        return buff

    def restore_rois(self, roifile):
        """restore ROI setting from ROI.dat file"""
        cp =  ConfigParser()
        cp.read(roifile)
        rois = []
        self.mcas[0].clear_rois()
        prefix = self.mcas[0]._prefix
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        iroi = 0
        for a in cp.options('rois'):
            if a.lower().startswith('roi'):
                name, dat = cp.get('rois', a).split('|')
                lims = [int(i) for i in dat.split()]
                lo, hi = lims[0], lims[1]
                roi = ROI(prefix=prefix, roi=iroi)
                roi.LO = lo
                roi.HI = hi
                roi.NM = name.strip()
                rois.append(roi)
                iroi += 1

        poll(0.050, 1.0)
        self.mcas[0].set_rois(rois)
        cal0 = self.mcas[0].get_calib()
        for mca in self.mcas[1:]:
            mca.set_rois(rois, calib=cal0)

    def Write_CurrentConfig(self, filename=None):
        buff = []
        add = buff.append
        add('#Multi-Element xMAP Settings saved: %s' % time.ctime())
        add('[general]')
        add('prefix= %s' % self._prefix)
        add('nmcas = %i' % self.nmca)
        add('filesaver= %s' % self.filesaver)
        d.add('starting roi....')
        buff.extend( self.roi_calib_info() )

        d.add('wrote roi / calib / dxp')

        buff = '\n'.join(buff)
        if filename is not None:
            fh = open(filename,'w', encoding=IOENCODING)
            fh.write(buff)
            fh.close()
        d.add('wrote file')
        # d.show()
        return buff

    def start(self):
        "Start Struck"
        self.EraseStart = 1

        if self.Acquiring == 0:
            poll()
            self.EraseStart = 1
        return self.EraseStart

    def stop(self):
        "Stop Struck Collection"
        self.StopAll = 1
        return self.StopAll

    def next_pixel(self):
        "Advance to Next Pixel:"
        self.NextPixel = 1
        return self.NextPixel

    def finish_pixels(self, timeout=2):
        "Advance to Next Pixel until CurrentPixel == PixelsPerRun"
        pprun = self.PixelsPerRun
        cur   = self.dxps[0].get('CurrentPixel')
        t0 = time.time()
        while cur < pprun and time.time()-t0 < timeout:
            time.sleep(0.1)
            pprun = self.PixelsPerRun
            cur   = self.dxps[0].get('CurrentPixel')
        ok = cur >= pprun
        if not ok:
            print('XMAP needs to finish pixels ', cur, ' / ' , pprun)
            for i in range(pprun-cur):
                self.next_pixel()
                time.sleep(0.10)
            self.FileCaptureOff()
        return ok, pprun-cur


    def readmca(self,n=1):
        "Read a Struck MCA"
        return self.get('mca%i' % n)

    def SCAMode(self):
        "put XMAP in SCA mapping mode"
        self.CollectMode = 2

    def SpectraMode(self):
        "put XMAP in MCA spectra mode"
        self.stop()
        self.CollectMode = 0
        self.PresetMode = 0
        # wait until BufferSize is ready
        buffsize = -1
        t0 = time.time()
        while time.time() - t0 < 5:
            self.CollectMode = 0
            time.sleep(0.05)
            if self.BufferSize_RBV < 16384:
                break

    def MCAMode(self, filename=None, filenumber=None, npulses=11):
        "put XMAP in MCA mapping mode"
        self.AutoApply = 1
        self.stop()
        self.PresetMode = 0
        self.setFileWriteMode(2)
        if npulses < 2:
            npulses = 2
        self.CollectMode = 1
        self.PixelsPerRun = npulses

        # First, make sure ArraySize0_RBV for the netcdf plugin
        # is the correct value
        self.FileCaptureOff()
        self.start()
        f_size = -1
        t0 = time.time()
        while (f_size < 16384) and time.time()-t0 < 10:
            for i in range(5):
                time.sleep(0.1)
                self.NextPixel = 1
                f_size = self.fileGet('ArraySize0_RBV')
                if f_size > 16384:
                    break
        #
        self.PixelsPerRun = npulses
        self.SyncCount =  1

        self.setFileNumber(filenumber)
        if filename is not None:
            self.setFileName(filename)

        # wait until BufferSize is ready
        self.Apply = 1
        self.CollectMode = 1
        self.PixelsPerRun = npulses
        time.sleep(0.50)
        t0 = time.time()
        while time.time() - t0 < 10:
            time.sleep(0.25)
            if self.BufferSize_RBV > 16384:
                break

        # set expected number of buffers to put in a single file
        ppbuff = self.PixelsPerBuffer_RBV
        time.sleep(0.25)
        if ppbuff is None:
            ppbuff = 124
        self.setFileNumCapture(1 + (npulses-1)/ppbuff)
        f_buffsize = -1
        t0 = time.time()
        while time.time()- t0 < 5:
            time.sleep(0.1)
            f_buffsize = self.fileGet('ArraySize0_RBV')
            if self.BufferSize_RBV == f_buffsize:
                break

        time.sleep(0.5)
        return

    def filePut(self,attr, value, **kw):
        return self.put("%s%s" % (self.filesaver, attr), value, **kw)

    def fileGet(self, attr, **kw):
        return self.get("%s%s" % (self.filesaver, attr), **kw)

    def setFilePath(self, pathname):
        return self.filePut('FilePath', pathname)

    def setFileTemplate(self, fmt):
        return self.filePut('FileTemplate', fmt)

    def setFileWriteMode(self, mode):
        return self.filePut('FileWriteMode', mode)

    def setFileName(self, fname):
        return self.filePut('FileName', fname)

    def nextFileNumber(self):
        self.setFileNumber(1+self.fileGet('FileNumber'))

    def setFileNumber(self, fnum=None):
        if fnum is None:
            self.filePut('AutoIncrement', 1)
        else:
            self.filePut('AutoIncrement', 0)
            return self.filePut('FileNumber',fnum)

    def getLastFileName(self):
        return self.fileGet('FullFileName_RBV',as_string=True)

    def FileCaptureOn(self):
        return self.filePut('Capture', 1)

    def FileCaptureOff(self):
        return self.filePut('Capture', 0)

    def setFileNumCapture(self,n):
        return self.filePut('NumCapture', n)

    def FileWriteComplete(self):
        return (0==self.fileGet('WriteFile_RBV') )

    def getFileTemplate(self):
        return self.fileGet('FileTemplate_RBV',as_string=True)

    def getFileName(self):
        return self.fileGet('FileName_RBV',as_string=True)

    def getFileNumber(self):
        return self.fileGet('FileNumber_RBV')

    def getFilePath(self):
        return self.fileGet('FilePath_RBV',as_string=True)

    def getFileNameByIndex(self,index):
        return self.getFileTemplate() % (self.getFilePath(), self.getFileName(), index)

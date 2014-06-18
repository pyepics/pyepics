#!/usr/bin/python
import sys
import time
import numpy as np
import epics

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

if sys.version[0] == '2':
    from ConfigParser import  ConfigParser
elif sys.version[0] == '3':
    from configparser import  ConfigParser

MAX_ROIS = 32
class DXP(epics.Device):
    _attrs = ('PreampGain','MaxEnergy','ADCPercentRule','BaselineCutPercent',
              'BaselineThreshold','BaselineFilterLength','BaselineCutEnable',
              'InputCountRate', 'OutputCountRate',
              'GapTime','PeakingTime','EnergyThreshold','MaxWidth',
              'PresetMode', 'TriggerPeakingTime',
              'TriggerGapTime','TriggerThreshold')

    def __init__(self,prefix,mca=1):
        self._prefix = "%sdxp%i" % (prefix, mca)
        epics.Device.__init__(self, self._prefix, delim=':')
        epics.poll()


class ROI(epics.Device):
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
    _nonpvs = ('_prefix', '_pvs', '_delim', '_aliases', 'attrs',
               'width', 'center', 'bgr_width', 'address',
               'net', 'total', '_dat_')

    def __init__(self, prefix, roi=0, bgr_width=3, data_pv=None):
        self.address = self._prefix = '%s.R%i' % (prefix, roi)
        self.bgr_width = bgr_width
        _attrs = ('NM', 'LO', 'HI', '', 'N')
        _aliases = {'name': _attrs[0],
                    'left': _attrs[1],
                    'right': _attrs[2],
                    '_sum_': _attrs[3],
                    '_net_': _attrs[4]}

        epics.Device.__init__(self,self._prefix, delim='',
                              attrs=_attrs, aliases=_aliases)
        self._pvs['_dat_'] = None
        if data_pv is not None:
            self._pvs['_dat_'] = data_pv
        epics.poll()

    def __eq__(self, other):
        """used for comparisons"""
        return (self.left == getattr(other, 'left', None) and
                self.right == getattr(other, 'right', None) and
                self.bgr_width == getattr(other, 'bgr_width', None) )

    def __ne__(self, other): return not self.__eq__(other)
    def __lt__(self, other): return self.left <  getattr(other, 'left', None)
    def __le__(self, other): return self.left <= getattr(other, 'left', None)
    def __gt__(self, other): return self.left >  getattr(other, 'left', None)
    def __ge__(self, other): return self.left >= getattr(other, 'left', None)

    def __repr__(self):
        "string representation"
        pref = self._prefix
        if pref.endswith('.'):
            pref = pref[:-1]
        return "<ROI '%s', name='%s', range=[%i:%i]>" % (pref, self.name, 
                                                   self.left, self.right)

    @property
    def total(self):
        return self.get_counts(net=False)

    @property
    def net(self):
        return self.get_counts(net=True)

    @property
    def center(self):
        return int(round(self.right + self.left)/2.0)

    @property
    def width(self):
        return int(round(self.right - self.left))

    def clear(self):
        self.name = ''
        self.left = -1
        self.right = -1

    def get_counts(self, data=None, net=False):
        """
        calculate total and net counts for a spectra

        Parameters:
        -----------
        * data: numpy array of spectra or None to read from PV
        * net:  bool to set net counts (default=False: total counts returned)
        """
        # implicitly read data from a PV
        if data is None:
            # for a normal MCA/ROI, read from 'RI' or RIN' property
            if self._pvs['_dat_'] is None:
                if net:
                    return self._net_
                return self._sum_
            # for 'fake' MCA/ROI, need a data source
            data = self._pvs['_dat_'].get()
        if not isinstance(data, np.ndarray):
            return 0

        total = data[self.left:self.right+1].sum()
        if not net:
            return total
        # calculate net counts
        bgr_width = int(self.bgr_width)
        ilmin = max((self.left - bgr_width), 0)
        irmax = min((self.right + bgr_width), len(data)-1) + 1
        bgr_counts = np.concatenate((data[ilmin:self.left],
                                     data[self.right+1:irmax])).mean()

        return (total - bgr_counts*(self.right-self.left))

class MCA(epics.Device):
    _attrs =('CALO','CALS','CALQ','TTH', 'EGU', 'VAL',
             'PRTM', 'PLTM', 'ACT', 'RTIM', 'STIM',
             'ACQG', 'NUSE','PCT', 'PTCL',
             'DWEL', 'CHAS', 'PSCL', 'SEQ',
             'ERTM', 'ELTM', 'IDTIM')
    _nonpvs = ('_prefix', '_pvs', '_delim', '_npts', 'rois', '_nrois')

    def __init__(self, prefix, mca=None, nrois=None, data_pv=None):
        self._prefix = prefix
        self._npts = None
        self._nrois = nrois
        if self._nrois is None:
            self._nrois = MAX_ROIS
        self.rois = []
        if isinstance(mca, int):
            self._prefix = "%smca%i" % (prefix, mca)

        epics.Device.__init__(self,self._prefix, delim='.', 
                              attrs=self._attrs)

        self._pvs['_dat_'] = None
        if data_pv is not None:
            self._pvs['_dat_'] = PV(data_pv)
        epics.poll()

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
            if roi.left > 0:
                self.rois.append(roi)
        return self.rois

    def del_roi(self, roiname):
        self.get_rois()
        for roi in self.rois:
            if roi.name.strip().lower() == roiname.strip().lower():
                roi.clear()
        epics.poll(0.010, 1.0)
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
        iroi = len(rois) 
        if iroi >= MAX_ROIS:
            raise ValueError('too many ROIs - cannot add more')
        data_pv = self._pvs['_dat_']
        prefix = self._prefix
        if prefix.endswith('.'): prefix = prefix[:-1]

        roi = ROI(prefix=prefix, roi=iroi, data_pv=self._pvs['_dat_'])
        roi.name = roiname.strip()

        offset, scale = 0.0, 1.0
        if calib is not None:
            off, slope, quad = self.get_calib()
            offset = calib[0] - off
            scale  = calib[1] / slope

        roi.left = round(offset + scale*lo)
        roi.right = round(offset + scale*hi)
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
        epics.poll(0.050, 1.0)
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
        epics.poll(0.050, 1.0)
        [(r.get('NM'), r.get('LO')) for r in rois]
        roidat = [(r.name, r.left, r.right) for r in sorted(rois)]

        iroi = 0
        self.rois = []
        for name, lo, hi in roidat:
            if len(name)<1 or lo<0 or hi<0:
                continue
            roi = ROI(prefix=prefix, roi=iroi, data_pv=data_pv)
            roi.name = name.strip()
            roi.left = round(offset + scale*lo)
            roi.right = round(offset + scale*hi)
            self.rois.append(roi)
            iroi += 1

        for i in range(iroi+1, MAX_ROIS):
            roi = ROI(prefix=prefix, roi=i)
            roi.clear()

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
    

class MultiXMAP(epics.Device):
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

        epics.Device.__init__(self, prefix, attrs=self.attrs,
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
            name = rois[0][iroi].name
            s = [[rois[m][iroi].left, rois[m][iroi].right] for m in range(self.nmca)]
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
                roi.left = lo
                roi.right = hi
                roi.name = name.strip()
                rois.append(roi)
                iroi += 1

        epics.poll(0.050, 1.0)
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
            fh = open(filename,'w')
            fh.write(buff)
            fh.close()
        d.add('wrote file')
        # d.show()
        return buff

    def start(self):
        "Start Struck"
        self.EraseStart = 1

        if self.Acquiring == 0:
            epics.poll()
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


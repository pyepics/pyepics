import numpy as np
import time

from .. import PV, caget, caput, poll, Device

MAX_CHAN = 4096
MAX_ROIS = 32
class ADMCAROI(Device):
    """
    MCA ROI using ROIStat plugin from areaDetector2,
    as used for Xspress3 detector.
    """
    _attrs =('Use', 'Name', 'MinX', 'SizeX', 'BgdWidth',
             'SizeX_RBV', 'MinX_RBV',
             'Total_RBV', 'Net_RBV')
    _aliases = {'left': 'MinX',
                'width': 'SizeX',
                'name': 'Name',
                'sum': 'Total_RBV',
                'net': 'Net_RBV'}
    _nonpvs = ('_prefix', '_pvs', '_delim', 'attrs',
               'center', 'set_center', 'get_center',  'data_pv')

    _reprfmt = "<ADMCAROI '%s', name='%s', range=[%s:%s]>"
    def __init__(self, prefix, roi=1, bgr_width=3, data_pv=None):
        self._prefix = '%s:%i' % (prefix, roi)
        Device.__init__(self,self._prefix, delim=':',
                        attrs=self._attrs,
                        aliases=self._aliases,
                        with_poll=True)
        self.data_pv = data_pv

    def __eq__(self, other):
        """used for comparisons"""
        return (self.MinX     == getattr(other, 'MinX', None) and
                self.SizeX    == getattr(other, 'SizeX', None) and
                self.BgdWidth == getattr(other, 'BgdWidth', None) )

    def __ne__(self, other): return not self.__eq__(other)
    def __lt__(self, other): return self.MinX <  getattr(other, 'MinX', None)
    def __le__(self, other): return self.MinX <= getattr(other, 'MinX', None)
    def __gt__(self, other): return self.MinX >  getattr(other, 'MinX', None)
    def __ge__(self, other): return self.MinX >= getattr(other, 'MinX', None)

    def __repr__(self):
        "string representation"
        pref = self._prefix
        if pref.endswith('.'):
            pref = pref[:-1]

        return self._reprfmt % (pref, self.Name, self.MinX,
                                self.MinX+self.SizeX)

    def get_right(self):
        return self.MinX + self.SizeX

    def set_right(self, val):
        """set the upper ROI limit (adjusting size, leaving left unchanged)"""
        self._pvs['SizeX'].put(val - self.MinX)

    right = property(get_right, set_right)

    def get_center(self):
        return int(round(self.MinX + self.SizeX/2.0))

    def set_center(self, val):
        """set the ROI center (adjusting left, leaving width unchanged)"""
        self._pvs['MinX'].put(int(round(val  - self.SizeX/2.0)))

    center = property(get_center, set_center)

    def clear(self):
        self.Name = ''
        self.MinX = 0
        self.SizeX = 0

    def get_counts(self, data=None, net=False):
        """
        calculate total and net counts for a spectra

        Parameters:
        -----------
         data   numpy array of spectra or None to read from PV
         net    bool to set net counts (default=False: total counts returned)
        """
        if data is None and self.data_pv is not None:
            data = self.data_pv.get()

        out = self.Total_RBV
        if net:
            out = self.Net_RBV
        if isinstance(data, np.ndarray):
            lo = self.MinX
            hi = self.MinX + self.SizeX
            out = data[lo:hi+1].sum()
            if net:
                wid = int(self.bgr_width)
                jlo = max((lo - wid), 0)
                jhi = min((hi + wid), len(data)-1) + 1
                bgr = np.concatenate((data[jlo:lo],
                                       data[hi+1:jhi])).mean()
                out = out - bgr*(hi-lo)
        return out

class ADMCA(Device):
    """
    MCA using ROIStat plugin from areaDetector2,
    as used for Xspress3 detector.
    """
    _attrs =('AcquireTime', 'Acquire', 'NumImages')
    _nonpvs = ('_prefix', '_pvs', '_delim', '_roi_prefix',
               '_npts', 'rois', '_nrois', 'rois', '_calib')
    _calib = (0.00, 0.01, 0.00)

    def __init__(self, prefix, data_pv=None, nrois=None, roi_prefix=None):

        self._prefix = prefix
        Device.__init__(self, self._prefix, delim='',
                              attrs=self._attrs, with_poll=False)
        if data_pv is not None:
            self._pvs['VAL'] = PV(data_pv)

        self._npts = None
        self._nrois = nrois
        if self._nrois is None:
            self._nrois = MAX_ROIS
        self.rois = []
        self._roi_prefix = roi_prefix
        if roi_prefix is not None:
            for i in range(self._nrois):
                self.rois.append(ADMCAROI(roi_prefix, roi=i+1))
        poll()


    def start(self):
        "Start AD MCA"
        self.Acquire = 1
        poll()
        return self.Acquire

    def stop(self):
        "Stop AD MCA"
        self.Acquire = 0
        return self.Acquire

    def get_calib(self):
        """get energy calibration tuple (offset, slope, quad)"""
        return self._calib

    def get_energy(self):
        """return energy for AD MCA"""
        if self._npts is None and self._pvs['VAL'] is not None:
            self._npts = len(self.get('VAL'))
        en = np.arange(self._npts, dtype='f8')
        cal = self._calib
        return cal[0] + en*(cal[1] + en*cal[2])

    def clear_rois(self, nrois=None):
        for roi in self.get_rois(nrois=nrois):
            roi.clear()
        self.rois = []

    def get_rois(self, nrois=None):
        "get all rois"
        self.rois = []
        data_pv = self._pvs['VAL']
        prefix = self._roi_prefix
        if prefix is None:
            return self.rois

        if nrois is None:
            nrois = self._nrois
        for i in range(nrois):
            roi = ADMCAROI(prefix=self._roi_prefix, roi=i+1)
            if len(roi.Name.strip()) <= 0 or roi.MinX < 0:
                break
            self.rois.append(roi)
        poll()

        return self.rois

    def del_roi(self, roiname):
        "delete an roi by name"
        if self.rois is None:
            self.get_rois()
        for roi in self.rois:
            if roi.Name.strip().lower() == roiname.strip().lower():
                roi.clear()
        poll(0.010, 1.0)
        self.set_rois(self.rois)

    def add_roi(self, roiname, lo, wid=None, hi=None, calib=None):
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
        if lo is None or (hi is None and wid is None):
            return
        rois = self.get_rois()
        try:
            iroi = len(rois)
        except:
            iroi = 0
        if iroi >= MAX_ROIS:
            raise ValueError('too many ROIs - cannot add more %i/%i' % (iroi, MAX_ROIS))
        data_pv = self._pvs['VAL']
        prefix = self._roi_prefix

        roi = ADMCAROI(prefix=prefix, roi=iroi, data_pv=data_pv)
        roi.Name = roiname.strip()

        offset, scale = 0.0, 1.0
        if calib is not None:
            off, slope, quad = self.get_calib()
            offset = calib[0] - off
            scale  = calib[1] / slope

        nmax = MAX_CHAN
        if self._npts is None and self._pvs['VAL'] is not None:
            nmax = self._npts = len(self.get('VAL'))

        roi.MinX = min(nmax-1, round(offset + scale*lo))
        if hi is not None:
            hi = min(nmax, hi)
            roi.SizeX = round(offset + scale*(hi-lo))
        elif wid is not None:
            wid = min(nmax, wid+roi.MinX) - roi.MinX
            roi.SizeX = round(scale*(wid))

        rois.append(roi)
        self.set_rois(rois)

    def set_rois(self, rois, calib=None):
        """set all rois, with optional calibration that those
        ROIs correspond to (if they have a different energy
        calibration), and ensures they are ordered and contiguous.


           rois  = mca1.get_rois()
           calib = mca1.get_calib()
           mca2.set_rois(rois, calib=calib)
        """
        data_pv = self._pvs['VAL']
        nmax = MAX_CHAN
        if self._npts is None and data_pv is not None:
            nmax = self._npts = len(data_pv.get())

        roi_prefix = self._roi_prefix
        offset, scale = 0.0, 1.0
        if calib is not None:
            off, slope, quad = self.get_calib()
            offset = calib[0] - off
            scale  = calib[1] / slope

        # do an explicit get here to make sure all data is
        # available before trying to sort it!
        poll(0.0050, 1.0)

        [(r.Name, r.MinX, r.SizeX) for r in rois]
        roidat = [(r.Name, r.MinX, r.SizeX) for r in sorted(rois)]

        iroi = 1
        self.rois = []
        previous_roi = ('', 0, 0)
        for ix, dat in enumerate(roidat):
            if dat == previous_roi:
                continue

            name, lo, wid = previous_roi = dat

            if len(name)<1 or lo<0 or wid<=0:
                continue
            roi = ADMCAROI(prefix=roi_prefix, roi=iroi, data_pv=data_pv)
            roi.Name  = name.strip()
            roi.MinX  = min(nmax-1, round(offset + scale*lo))
            hi        = min(nmax, round(offset + scale*(lo+wid)))
            roi.SizeX = hi-roi.MinX
            self.rois.append(roi)
            iroi += 1

        # erase any remaining ROIs
        for i in range(iroi, MAX_ROIS+1):
            pref = "%s:%i" % (roi_prefix, i)
            lo = caget("%s:MinX" % pref)
            if lo > 0:
                caput("%s:MinX"  % pref, 0)
                caput("%s:SizeX" % pref, 0)
                caput("%s:Name"  % pref, '')

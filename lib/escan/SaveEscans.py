import os
import sys

import glob
import shutil

import time
import numpy
try:
    import json
except:
    import simplejson as json

from string import printable
from ConfigParser import  ConfigParser

from read_xmap_netcdf import read_xmap_netcdf
from util import debugtime, nativepath
from configFile import FastMapConfig

def readASCII(fname, nskip=0, isnumeric=True):
    dat, header = [], []
    for line in open(fname,'r').readlines():
        if line.startswith('#') or line.startswith(';'):
            header.append(line[:-1])
            continue
        if nskip > 0:
            nskip -= 1
            header.append(line[:-1])
            continue
        if isnumeric:
            dat.append([float(x) for x in line[:-1].split()])
        else:
            dat.append(line[:-1].split())
    if isnumeric:
        dat = numpy.array(dat)
    return header, dat

def readMasterFile(fname):
    return readASCII(fname, nskip=0, isnumeric=False)

def readEnvironFile(fname):
    h, d = readASCII(fname, nskip=0, isnumeric=False)
    return h

def readScanConfig(sfile):
    cp =  ConfigParser()
    cp.read(sfile)
    scan = {}
    for a in cp.options('scan'):
        scan[a]  = cp.get('scan',a)
    general = {}
    for a in cp.options('general'):
        general[a]  = cp.get('general',a)
    return scan, general

def readROIFile(hfile):
    cp =  ConfigParser()
    cp.read(hfile)
    output = []
    try:
        rois = cp.options('rois')
    except:
        print 'rois not found'
        return []

    for a in cp.options('rois'):
        if a.lower().startswith('roi'):
            iroi = int(a[3:])
            name, dat = cp.get('rois',a).split('|')
            xdat = [int(i) for i in dat.split()]
            dat = [(xdat[0], xdat[1]), (xdat[2], xdat[3]),
                   (xdat[4], xdat[5]), (xdat[6], xdat[7])] 
            output.append((iroi, name.strip(), dat))
    output = sorted(output)
    print 'Read ROI data: %i ROIS ' % len(output)
    return output
        
class EscanWriter(object):
    ScanFile   = 'Scan.cnf'
    EnvFile    = 'Environ.dat'
    ROIFile    = 'ROI.dat'
    MasterFile = 'Master.dat'
    off_struck = 0
    off_xmap   = 0

    def __init__(self, folder=None, **kw):
        self.folder = folder
        self.master_header = None
        self.environ = None
        self.roidata = None
        self.scanconf = None        
        self.last_row = 0
        self.clear()
        
    def ReadMaster(self):
        self.rowdata = None
        self.master_header = None

        if self.folder is not None:
            fname = os.path.join(nativepath(self.folder), self.MasterFile)
            # print  'EscanWriter Read Scan file ', fname
            if os.path.exists(fname):
                try:
                    header, rows = readMasterFile(fname)
                except:
                    print 'Cannot read Scan folder'
                    return
                self.master_header = header
                self.rowdata = rows
                self.starttime = self.master_header[0][6:]
        if self.environ is None:
            self.environ = readEnvironFile(os.path.join(self.folder, self.EnvFile))

        if self.roidata is None:
            # print 'Read ROI data from ', os.path.join(self.folder,self.ROIFile)
            self.roidata = readROIFile(os.path.join(self.folder,self.ROIFile))

        if self.scanconf is None:
            fastmap = FastMapConfig()
            self.slow_positioners = fastmap.config['slow_positioners']
            self.fast_positioners = fastmap.config['fast_positioners']

            self.scanconf, self.generalconf = readScanConfig(os.path.join(self.folder,self.ScanFile))
            scan = self.scanconf
            self.mca_prefix = self.generalconf['xmap']

            self.dim = self.scanconf['dimension']
            self.comments = self.scanconf['comments']
            self.filename = self.scanconf['filename']

            self.pos1 = self.scanconf['pos1']

            self.ipos1 = -1
            for i, posname in enumerate(self.fast_positioners):
                if posname == self.pos1:
                    self.ipos1 = i

            if self.dim > 1:
                self.pos2 =self.scanconf['pos2']

    def make_header(self):
        def add(x):
            self.buff.append(x)
        yval0 = self.rowdata[0][0]
        
        add('; Epics Scan %s dimensional scan' % self.dim)
        if int(self.dim) == 2:
            add(';2D %s: %s' % (self.pos2,yval0))
        add('; current scan = 1')
        add('; scan dimension = %s' % self.dim)
        add('; scan prefix = FAST')
        add('; User Titles:')
        for i in self.comments.split('\\n'):
            add(';   %s' % i)
        add('; PV list:')
        for t in self.environ:  add("%s"% t)

        if self.scanconf is not None:
            add('; Scan Regions: Motor scan with        1 regions')
            add(';       Start       Stop       Step    Time')
            add(';     %(start1)s      %(stop1)s      %(step1)s     %(time1)s' % self.scanconf)
            
        add('; scan %s'  % self.master_header[0][6:])
        add(';====================================')

    def clear(self):
        self.buff = []
       
    def process(self, maxrow=None):
        # print '=== Escan Writer: ', self.folder
        self.ReadMaster()
        if self.last_row >= len(self.rowdata):
            return 0

        def add(x):
            self.buff.append(x)
            
        if self.last_row == 0 and len(self.rowdata)>0:
            self.make_header()

        if maxrow is None:
            maxrow = len(self.rowdata)
        while self.last_row <  maxrow:
            irow = self.last_row
            # print '>EscanWrite.process row %i of %i' % (self.last_row, len(self.rowdata))
            # print self.rowdata[irow]

            yval, xmapfile, struckfile, gatherfile, dtime = self.rowdata[irow]

            shead,sdata = readASCII(os.path.join(self.folder,struckfile))
            ghead,gdata = readASCII(os.path.join(self.folder,gatherfile))
            t0 = time.time()
            atime = -1
            while atime < 0 and time.time()-t0 < 10:
                try:
                    atime = time.ctime(os.stat(os.path.join(self.folder,
                                                            xmapfile)).st_ctime)
                    xmapdat     = read_xmap_netcdf(os.path.join(self.folder,xmapfile),verbose=False)
                    print '.',
                    if (irow+1) % 50 == 0: print
                    sys.stdout.flush()
                except:
                    print 'xmap data failed to read'
                    self.clear()
                    atime = -1
                time.sleep(0.03)
            if atime < 0:
                return 0
            # print 'EscanWrite.process Found xmapdata in %.3f sec (%s)' % (time.time()-t0, xmapfile)

            struck_range = slice(0, len(sdata))
            if self.off_struck > 0:
                struck_range = slice(self.off_struck, len(sdata))
            elif self.off_struck < 0:
                struck_range = slice(0, len(sdata)+self.off_struck)

            sdata = sdata[struck_range]
            gnpts, ngather  = gdata.shape          
            snpts, nscalers = sdata.shape

            nxmap = len(xmapdat.inputCounts)
            xmap_range = slice(0, nxmap)
            if self.off_xmap > 0:
                xmap_range = slice(self.off_xmap, nxmap)
            elif self.off_xmap < 0:
                xmap_range = slice(0, nxmap+self.off_xmap)
                
            xmdat = xmapdat.data[xmap_range]
            xmicr = xmapdat.inputCounts[xmap_range]
            xmocr = xmapdat.outputCounts[xmap_range]
            xm_tl = xmapdat.liveTime[xmap_range]
            xm_tr = xmapdat.realTime[xmap_range]
            xnpts = xmdat.shape[0]
            npts = min(snpts,gnpts,xnpts)

            if irow == 0:
                self.npts0 = npts
                add('; scan ended at time: %s'  % atime)
                add('; npts = %i' % npts)
                add('; column labels:')
                p1label = self.slow_positioners[self.pos1]

                add('; P1 = {%s} --> %s (drive)' % (p1label, self.pos1))
                add('; D1 = {MCS Count Time} --> CountTime (ms)')
                add('; D2 = {MCA Real Time} --> RealTime (ms)')
                add('; D3 = {MCA Live Time} --> LiveTime (ms)')
                legend = ['P1','D1', 'D2', 'D3']
                struckPVs = [i.strip() for i in shead[-2][1:].split('|')]
                struckLabels = [i.strip() for i in shead[-1][1:].split('|')]
                for i,pvn in enumerate(struckPVs):
                    add('; D%i = {%s} --> %s' % (i+4,struckLabels[i],pvn))
                    legend.append('D%i' % (i+1))
                    idet = i+1
                idet = idet+3
                suf,rnam = ('','.R') # ): #  , ('(raw)','.R1')):
                mca="%smca1%s" % (self.mca_prefix, rnam)
                for iroi,label,roidat in self.roidata:
                    idet  = idet + 1
                    legend.append('D%i' % (idet))
                    add('; D%i = {%s%s} --> %s%i' % (idet,label,suf,mca,iroi))
                self.legend = ' '.join(legend)
            else:
                if npts > self.npts0:  npts = self.npts0
                if npts < self.npts0:
                    print 'Broken Data : ', npts, self.npts0
                # print ' > NPTS: (xps, struck, xmap, expected: ) =', npts, gnpts, snpts, xnpts, self.npts0
                add(';2D %s: %s' % (self.pos2, yval))
                add('; scan ended at time: %s'  % atime)
            add(';---------------------------------')    
            add('; %s' % self.legend)

            points = range(1,npts)
            span   = (gdata[-1,0] - gdata[0,0])
            
            if (span/abs(span)) < 0:
                points.reverse()
            for ipt in points:
                xval = (gdata[ipt,self.ipos1] + gdata[ipt-1,self.ipos1])/2.0
                x = ['%.4f %.1f %.1f %.1f' % (xval, sdata[ipt,0]*1.e-3, 
                                              1000*xm_tr[ipt].mean(), 1000*xm_tl[ipt].mean()) ]  #
                x.extend(['%i' %i for i in sdata[ipt,:]])
                # icr_corr = xmicr[ipt,:] /  (1.e-10 + 1.0*xmocr[ipt,:])
                raw,cor = [],[]
                for iroi,lab,rb in self.roidata:
                    intens = numpy.array([xmdat[ipt, i, rb[i][0]:rb[i][1]].sum()  for i in range(4)])
                    # cor.append((intens*icr_corr).sum())
                    raw.append( intens.sum() )
                # x.extend(["%.2f" % r for r in cor])
                x.extend(["%i"   % r for r in raw])            
                add(' '.join(x))
                # print ipt, raw
                
            self.last_row += 1
        # print "EscanWrite: ", len(self.buff), ' new lines'
        return len(self.buff)


def make_backup(fname, extension = '.bak'):
    bak = fname + '.bak'
    print 'Backup up file ', fname
    shutil.copy(fname, bak)

def save_folder(foldername, offset=0):
    w = EscanWriter(folder=foldername)
    w.ReadMaster()
    fout = w.scanconf['filename']
    
    backup_thread = None
    if os.path.exists(fout):
        backup_thread = Thread(target=make_backup, args=(fout,))
        backup_thread.start()
    #
    w.off_xmap = offset
    print ' processing with offset = ', offset
    w.process()

    if backup_thread is not None:
        backup_thread.join()
        
    # fout = 't1.out'
    print 'writing %s' % fout
    f = open(fout, 'w')
    f.write('\n'.join(w.buff))
    f.write('\n')
    f.close()

if __name__ == '__main__':
    if len(sys.argv) > 0:
        foldername = sys.argv[1]
        offset = 0
        if len(sys.argv) > 2:
            offset    = int(sys.argv[2])
        
        save_folder(foldername, offset=offset)
    

#!/usr/bin/python 
import sys
import time
import epics
import numpy
import ordereddict
import debugtime
    
#     _attrs =('PreampGain','MaxEnergy','ADCPercentRule','BaselineCutPercent',
#              'BaselineThreshold','BaselineFilterLength','BaselineCutEnable',
#              'CurrentPixel', 'InputCountRate', 'OutputCountRate', 
#              'GapTime','PeakingTime','EnergyThreshold','MaxWidth',
#              'PresetMode', 'PresetTriggers', 'PresetEvents',
#              'Triggers', 'Events', 'TriggerPeakingTime',
#              'TriggerGapTime','TriggerThreshold')
# 

class DXP(epics.Device):
    _attrs =('PreampGain','MaxEnergy','ADCPercentRule','BaselineCutPercent',
             'BaselineThreshold','BaselineFilterLength','BaselineCutEnable',
             'InputCountRate', 'OutputCountRate', 
             'GapTime','PeakingTime','EnergyThreshold','MaxWidth',
             'PresetMode', 
             'TriggerPeakingTime',
             'TriggerGapTime','TriggerThreshold')

    def __init__(self,prefix,mca=1):
        self._prefix = "%sdxp%i" % (prefix, mca)
        self._maxrois = 16

        epics.Device.__init__(self, self._prefix, delim=':')
        epics.poll()
            
class MCA(epics.Device):  
    _attrs =('CALO','CALS','CALQ','TTH', 'EGU', 'VAL',
             'PRTM', 'PLTM', 'ACT', 'RTIM', 'STIM',
             'ACQG', 'NUSE','PCT', 'PTCL', 
             'DWEL', 'CHAS', 'PSCL', 'SEQ',
             'ERTM', 'ELTM', 'IDTIM')

    def __init__(self,prefix,mca=1):
        self._prefix = "%smca%i" % (prefix, mca)
        self._maxrois = 16
        attrs = list(self._attrs)
        for i in range(self._maxrois):
            attrs.extend(['R%i'%i, 'R%iN' %i, 'R%iNM' %i,
                          'R%iLO'%i,'R%iHI'%i, 'R%iBG'%i])

        epics.Device.__init__(self,self._prefix, delim='.',
                              attrs= attrs)
        epics.poll()
        
    def getrois(self):
        rois = ordereddict.OrderedDict()        
        for i in range(self._maxrois):
            name = self.get('R%iNM'%i)
            if name is not None and len(name.strip()) > 0:
                rois[name] = (self.get('R%iLO'%i),self.get('R%iHI'%i))
        return rois

    def get_calib(self):
        return [self.get(i) for i in ('CALO','CALS','CALQ')]

class MultiXMAP(epics.Device):
    """ 
    multi-Channel XMAP DXP device
    """
    attrs = ('PresetReal','Dwell','EraseStart','StopAll',
             # 'PresetMode',
             'NextPixel', 'PixelsPerRun',
             'CollectMode', 'SyncCount', 'BufferSize_RBV')

    pathattrs = ('FilePath', 'FileTemplate', 'FileWriteMode',
                 'FileName', 'FileNumber', 'FullFileName_RBV',
                 'Capture',  'NumCapture', 'WriteFile_RBV',
                 'FileTemplate_RBV', 'FileName_RBV', 'AutoIncrement')    
    
    # _fields = ('_pvs', '_prefix', '_delim',
    #           'nmca', 'mcas', 'dxps', 'filesaver')
    
    def __init__(self,prefix,filesaver='netCDF1:',nmca=4):
        attrs = list(self.attrs)
        attrs.extend(['%s%s' % (filesaver,p) for p in self.pathattrs])

        self.filesaver = filesaver
        self._prefix = prefix
        self.nmca   = nmca

        self.dxps   = [DXP(prefix,i+1) for i in range(nmca)]
        self.mcas   = [MCA(prefix,i+1) for i in range(nmca)]
        epics.Device.__init__(self, prefix, attrs=attrs, delim='')

    def get_calib(self):
        return [m.get_calib() for m in self.mcas]

    def get_rois(self):
        return [m.getrois() for m in self.mcas]    
        
    def roi_calib_info(self):
        buff = ['[roi]']

        roidat = self.get_rois()
        caldat = numpy.array(self.get_calib())

        for i, k in enumerate(roidat[0].keys()):
            s = [list(roidata[m][k]) for m in range(self.nmca)]
            rd = repr(s).replace('],', '').replace('[', '').replace(']','').replace(',','')
            buff.append("ROI%2.2i = %s | %s" % (i,k,rd))
        buff.append('[calibration]')
        buff.append("OFFSET = %s " % (' '.join(["%.7g" % i for i in caldat[:, 0]])))
        buff.append("SLOPE  = %s " % (' '.join(["%.7g" % i for i in caldat[:, 1]])))
        buff.append("QUAD   = %s " % (' '.join(["%.7g" % i for i in caldat[:, 2]])))
        return buff
    
    def Write_CurrentConfig(self, filename=None):
        d = debugtime.debugtime()

        # print 'Write Current Config'
        buff = []
        def add(s):
            buff.append(s)
        
        add('#Multi-Element xMAP Settings saved: %s' % time.ctime())
        add('[general]')
        add('prefix= %s' % self._prefix)
        add('nmcas = %i' % self.nmca)
        add('filesaver= %s' % self.filesaver)
        d.add('starting roi....')
        add.extend( self.roi_calib_info() )

        d.add('wrote roi / calib')
        add('[dxp]')
        dxp_attrs = self.dxps[0]._attrs
        print len(dxp_attrs), len(self.dxps)
        for  a in dxp_attrs:
            vals = [str(dxp.get(a, as_string=True)) for dxp in self.dxps]
            add("%s = %s" % (a, ' '.join(vals)))
        d.add('wrote dxp params')
        buff = '\n'.join(buff)
        if filename is not None:
            fh = open(filename,'w')
            fh.write(buff)
            fh.close()
        d.add('wrote file')
        d.show()
        return buff

    def GetAcquire(self,**kw):
        return self.get('Acquiring',**kw)

    def start(self):
        "Start Struck"
        ret = self.put('EraseStart',1)
        
        if self.GetAcquire() == 0:
            epics.poll()
            self.EraseStart = 1
        return self.EraseStart

    def stop(self):
        "Stop Struck Collection"
        return self.put('StopAll',1)

    def next_pixel(self):
        "Advance to Next Pixel:"
        return self.put('NextPixel',1)


    def finish_pixels(self):
        "Advance to Next Pixel until CurrentPixel == PixelsPerRun"
        pprun = self.get('PixelsPerRun')
        cur   = self.dxps[0].get('CurrentPixel')
        for i in range(pprun-cur):
            self.next_pixel()
            time.sleep(0.001)
        return pprun-cur

    def readmca(self,n=1):
        "Read a Struck MCA"
        return self.get('mca%i' % n)

    def SCAMode(self):
        "put XMAP in SCA mapping mode"
        self.CollectMode = 2    

    def SpectraMode(self):
        "put XMAP in MCA spectra mode"
        self.CollectMode = 0
        self.PresetMode = 0
        # wait until BufferSize is ready
        buffsize = -1
        t0 = time.time()
        while time.time() - t0 < 3:
            self.CollectMode = 0
            epics.poll()
            buffsize = self.get('BufferSize_RBV')
            if buffsize < 16384:
                break

        self.start()
        

    def MCAMode(self,filename=None,filenumber=1,npulses=11):
        "put XMAP in MCA mapping mode"
        debug = debugtime.debugtime()

        print 'Putting xMAP MED into MCA mode'
        self.stop()
        epics.poll()
        self.CollectMode = 1
        self.PresetMode = 0
        self.PixelsPerRun =  npulses
        self.SyncCount =  1
        epics.poll()
        debug.add(' >> xmap MCAmode: Mode Set: ')
        self.setFileNumber(filenumber)
        if filename is not None:
            self.setFileName(filename)
        
        self.start()
        time.sleep(0.25)
        self.stop()

        # wait until BufferSize is ready
        buffsize = -1
        t0 = time.time()
        while time.time() - t0 < 10:
            time.sleep(0.25)
            epics.poll()
            buffsize = self.get('BufferSize_RBV')
            if buffsize > 16384:
                break
        debug.add(' >> xmap MCAmode: BuffSize OK? %i' % buffsize)

        # set expected number of buffers to put in a single file
        ppbuff = 1.0 * self.get('PixelsPerBuffer_RBV')

        self.setFileNumCapture( 1 + int(npulses/ppbuff) )

        debug.add(' >> xmap MCAmode: FileNumCapture: ')
           
        f_buffsize = -1
        t0 = time.time()
        while time.time()- t0 < 3:
            epics.poll()
            f_buffsize = self.fileGet('ArraySize0_RBV')
            if buffsize == f_buffsize:
                break            

        debug.add(' >> xmap MCAmode NC ArraySize: %i %i ' % ( f_buffsize, buffsize))
        self.FileCaptureOff()
        self.stop()
        debug.add(' >> xmap MCAmode: Done. ')
        # debug.show()
        return

    def filePut(self,attr,value, **kw):
        return self.put("%s%s" % (self.filesaver, attr),value, **kw)

    def fileGet(self,attr, **kw):
        return self.get("%s%s" % (self.filesaver,attr),**kw)
    
    def setFilePath(self,pathname):
        return self.filePut('FilePath',pathname)

    def setFileTemplate(self,fmt):
        return self.filePut('FileTemplate',fmt)

    def setFileWriteMode(self,mode):
        return self.filePut('FileWriteMode',mode)

    def setFileName(self,fname):
        return self.filePut('FileName',fname)

    def setFileNumber(self,fnum):
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
    
if __name__ == '__main__':

    qv = MultiXMAP('13SDD1:', nmca=4)

    qv.Write_CurrentConfig(filename='QuadVortex.conf')
# # print 'Config written.'
#     
#     for k, v in q._pvs.items():
#         print k, v.get()    
# 
#     print q.mcas
# 
#     t0 = time.time()
#     print q.nmca
#     print len(q._pvs) 
#         
#     m = MCA('13SDD1:', mca=1)
#     print 'MCA: ', len(m._pvs), len(m._pvs)*12 
#     d = DXP('13SDD1:', mca=1)
#     print 'DXP: ', len(d._pvs), len(d._pvs)*12 
    
#     q.Write_CurrentConfig(filename='QuadVortex.conf')
#     time.sleep(0.5)
#     print 'now do it again:'
#     t0 = time.time()
#     q.Write_CurrentConfig(filename='QuadVortex2.conf')    
#     print time.time()-t0

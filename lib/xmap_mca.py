#!/usr/bin/python 
import epics
import time
from util import debugtime
import ordereddict
import debugtime

import sys
def pend(t=0.05):
    epics.ca.poll()
    time.sleep(t)
    
class DXP(epics.Device):
    _attrs =('PreampGain','MaxEnergy','ADCPercentRule','BaselineCutPercent',
             'BaselineThreshold','BaselineFilterLength','BaselineCutEnable',
             'CurrentPixel', 
             'GapTime','PeakingTime','EnergyThreshold','MaxWidth',
             'TriggerPeakingTime','TriggerGapTime','TriggerThreshold')

    def __init__(self,prefix,mca=1):
        self.prefix = "%sdxp%i:" % (prefix,mca)
        # attrs = [ ':%s' % (i) for i in self._attrs]
        epics.Device.__init__(self, self.prefix, self._attrs)
        pend()
            
class MCA(epics.Device):
    calib_attrs =('.CALO','.CALS','.CALQ')
    def __init__(self,prefix,mca=1):
        self.prefix = "%smca%i" % (prefix,mca)
        self.maxrois = 16
        attrs = list(self.calib_attrs)
        for i in range(self.maxrois):
            attrs.extend(['.R%iNM' %i,'.R%iLO'%i,'.R%iHI'%i])

        epics.Device.__init__(self,self.prefix,attrs)
        pend()
        
    def getrois(self):
        rois = ordereddict.OrderedDict()        
        for i in range(self.maxrois):
            name = self.get('.R%iNM'%i)
            if name is not None and len(name.strip()) > 0:
                rois[name] = (self.get('.R%iLO'%i),self.get('.R%iHI'%i))
        self.rois = rois
        return rois

    def get_calib(self):
        return [self.get(i) for i in self.calib_attrs]

class QuadVortex(epics.Device):
    """ 
    4-Channel XMAP DXP device
    """
    attrs = ('PresetReal','Dwell','EraseStart','StopAll',
             'NextPixel', 'PixelsPerRun',
             'CollectMode', 'SyncCount', 'BufferSize_RBV')

    pathattrs = ('FilePath', 'FileTemplate', 'FileWriteMode',
                 'FileName', 'FileNumber', 'FullFileName_RBV',
                 'Capture',  'NumCapture', 'WriteFile_RBV',
                 'FileTemplate_RBV', 'FileName_RBV', 'AutoIncrement')    
    
    def __init__(self,prefix,filesaver='netCDF1:',nmca=4):


        attrs = list(self.attrs)
        attrs.extend(['%s%s' % (filesaver,p) for p in self.pathattrs])

        epics.Device.__init__(self,prefix, attrs=attrs)
        self.filesaver = filesaver
        self.prefix = prefix
        self.nmca   = nmca

        # print ' Quadvortex init: ', nmca, prefix
        
        self.dxps   = [DXP(prefix,i+1) for i in range(nmca)]
        self.mcas   = [MCA(prefix,i+1) for i in range(nmca)]

    def get_calib(self):
        return [m.get_calib() for m in self.mcas]

    def get_rois(self):
        return [m.getrois() for m in self.mcas]    

    def Write_CurrentConfig(self, filename=None):
        d = debugtime.debugtime()

        roidata = self.get_rois()
        d.add('got rois')
        # print 'Write Current Config'
        buff = []
        def add(s): buff.append(s)
        
        add('#QuadVortex Settings saved: %s' % time.ctime())
        add('[general]')
        add('prefix= %s' % self.prefix)
        add('nmcas = %i' % self.nmca)
        add('filesaver= %s' % self.filesaver)
        d.add('1')
        add('[roi]')        
        for i, k in enumerate(roidata[0].keys()):
            s = [list(roidata[m][k]) for m in range(self.nmca)]
            rd = repr(s).replace('],', '').replace('[', '').replace(']','').replace(',','')
            add("ROI%2.2i = %s | %s" % (i,k,rd))
        d.add('2')

        cal = [[],[],[]]
        for i,dat in enumerate(self.get_calib()):
            off,slope,quad = dat
            cal[0].append(off)
            cal[1].append(slope)
            cal[2].append(quad)
        add('[calibration]')
        add("OFFSET = %.7g  %.7g %.7g %.7g" % tuple(cal[0]))
        add("SLOPE  = %.7g  %.7g %.7g %.7g" % tuple(cal[1]))
        add("QUAD   = %.7g  %.7g %.7g %.7g" % tuple(cal[2]))
        d.add('3')
        add('[dxp]\n')
        dxp_attrs = self.dxps[0]._attrs
        for  a in dxp_attrs:
            vals =[dxp.get(a, as_string=True) for dxp in self.dxps]
            add("%s = %s" % (a, ' '.join(vals)))
        d.add('wrote dxp params')
        buff = '\n'.join(buff)
        if filename is not None:
            fh = open(filename,'w')
            fh.write(buff)
            fh.close()
        d.add('wrote file')
        # d.show()
        return buff

    def GetAcquire(self,**kw):
        return self.get('Acquiring',**kw)

    def PresetMode(self,mode=0):
        return self.put('PresetMode',mode)

    def PresetReal(self,val):
        "Set Preset Real Tiem"
        return self.put('PresetReal',val)

    def Dwell(self,val):
        "Set Dwell Time"
        return self.put('Dwell',val)    

    def start(self):
        "Start Struck"
        ret = self.put('EraseStart',1)
        
        if self.GetAcquire() == 0:
            pend()
            ret = self.put('EraseStart',1)
        return ret
        

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

    def CollectMode(self,mode=0):
        return self.put('CollectMode',mode)

    def SCAMode(self):
        "put XMAP in SCA mapping mode"
        return self.CollectMode(2)    

    def SpectraMode(self):
        "put XMAP in MCA spectra mode"
        self.CollectMode(0)
        self.PresetMode(0)
        # wait until BufferSize is ready
        buffsize = -1
        t0 = time.time()
        while time.time() - t0 < 3:
            self.CollectMode(0)
            pend()
            buffsize = self.get('BufferSize_RBV')
            if buffsize < 16384:
                break

        self.start()
        

    def MCAMode(self,filename=None,filenumber=1,npulses=11):
        "put XMAP in MCA mapping mode"
        debug = debugtime.debugtime()

        print 'Putting XMAP/QuadVortex into MCA mode'
        self.stop()
        pend()
        self.CollectMode(1)
        self.PresetMode(0)
        self.put('PixelsPerRun', npulses)
        self.put('SyncCount', 1)
        pend()
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
            pend()
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
            pend()
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
        return self.put("%s%s" % (self.filesaver,attr),value, **kw)

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
    q = QuadVortex('13SDD1:')
    q.Write_CurrentConfig(filename='QuadVortex.conf')
    time.sleep(0.5)
    print 'now do it again:'
    t0 = time.time()
    q.Write_CurrentConfig(filename='QuadVortex2.conf')    
    print time.time()-t0

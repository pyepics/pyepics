#!/usr/bin/python
import sys
import time
from .. import Device

class AD_PerkinElmer(Device):
    camattrs = ('PEAcquireOffset', 'PENumOffsetFrames',
                'ImageMode', 'TriggerMode',
                'Acquire',  'AcquireTime', 'Model_RBV',
                'NumImages', 'ShutterControl', 'ShutterMode')

    pathattrs = ('FilePath', 'FileTemplate', 'FileWriteMode',
                 'FileName', 'FileNumber', 'FullFileName_RBV',
                 'Capture',  'Capture_RBV', 'NumCapture', 'WriteFile_RBV',
                 'AutoSave', 'EnableCallbacks',  'ArraySize0_RBV',
                 'FileTemplate_RBV', 'FileName_RBV', 'AutoIncrement')

    _nonpvs  = ('_prefix', '_pvs', '_delim', 'filesaver',
                'camattrs', 'pathattrs', '_nonpvs')

    def __init__(self,prefix, filesaver='netCDF1:'):
        camprefix = prefix + 'cam1:'
        Device.__init__(self, camprefix, delim='',
                        mutable=False,
                        attrs=self.camattrs)
        self.filesaver = "%s%s" % (prefix, filesaver)
        for p in self.pathattrs:
            pvname = '%s%s%s' % (prefix, filesaver, p)
            self.add_pv(pvname, attr='File_'+p)


    def AcquireOffset(self, timeout=10, open_shutter=True):
        """Acquire Offset -- a slightly complex process

        Arguments
        ---------
        timeout :       float (default 10)  time in seconds to wait
        open_shutter :  bool (default True)  open shutters on exit

        1. close shutter
        2. set image mode to single /internal trigger
        3. acquire offset correction
        4. reset image mode and trigger mode
        5. optionally (by default) open shutter
        """
        self.ShutterMode = 1
        self.ShutterControl = 0
        image_mode_save = self.ImageMode
        trigger_mode_save = self.TriggerMode
        self.ImageMode = 0
        self.TriggerMode = 0
        offtime = self.PENumOffsetFrames * self.AcquireTime
        time.sleep(0.50)
        self.PEAcquireOffset = 1
        t0 = time.time()
        time.sleep(offtime/3.0)
        while self.PEAcquireOffset > 0 and time.time()-t0 < timeout+offtime:
            time.sleep(0.1)
        time.sleep(1.00)
        self.ImageMode = image_mode_save
        self.TriggerMode = trigger_mode_save
        time.sleep(1.00)
        if open_shutter:
            self.ShutterControl = 1
        self.ShutterMode = 0
        time.sleep(1.00)

    def SetExposureTime(self, t, open_shutter=True):
        "set exposure time, re-acquire offset correction"
        self.AcquireTime = t
        self.AcquireOffset(open_shutter=open_shutter)

    def SetMultiFrames(self, n, trigger='external'):
        """set number of multiple frames for streaming
        this sets number of images for camera in Multiple Image Mode
        AND sets the number of images to capture with file plugin
        """
        self.ImageMode = 1  #  multiple images

        # trigger mode
        trigger_mode = 0 # internal
        if trigger.lower().startswith('ext'):
            trigger_mode = 1 # external
        elif trigger.lower().startswith('free'):
            trigger_mode = 2 # free running
        elif trigger.lower().startswith('soft'):
            trigger_mode = 3 # soft trigger
        time.sleep(0.1)

        self.TriggerMode = trigger_mode
        # number of images for collection and streaming
        self.NumImages  = n
        # set filesaver
        self.filePut('NumCapture',    n)
        self.filePut('EnableCallbacks', 1)
        self.filePut('FileNumber',    1)
        self.filePut('AutoIncrement', 1)
        time.sleep(2.0)

    def StartStreaming(self):
        """start streamed acquisition to save with
        file saving plugin, and start acquisition
        """
        self.ShutterMode = 0
        self.filePut('AutoSave', 1)
        self.filePut('FileWriteMode', 2)  # stream
        time.sleep(0.05)
        self.filePut('Capture', 1)  # stream
        self.Acquire = 1
        time.sleep(0.25)


    def FinishStreaming(self, timeout=5.0):
        """start streamed acquisition to save with
        file saving plugin, and start acquisition
        """
        t0 = time.time()
        capture_on = self.fileGet('Capture_RBV')
        while capture_on==1 and time.time() - t0 < timeout:
            time.sleep(0.05)
            capture_on = self.fileGet('Capture_RBV')
        if capture_on != 0:
            print( 'Forcing XRD Streaming to stop')
            self.filePut('Capture', 0)
            t0 = time.time()
            while capture_on==1 and time.time() - t0 < timeout:
                time.sleep(0.05)
                capture_on = self.fileGet('Capture_RBV')
        time.sleep(0.50)


    def filePut(self, attr, value, **kw):
        return self.put("File_%s" % attr, value, **kw)

    def fileGet(self, attr, **kw):
        return self.get("File_%s" % attr, **kw)

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


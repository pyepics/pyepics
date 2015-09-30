from .. import Device

class AD_FilePlugin(Device):
    """
    AreaDetector File Plugin
    """
    attrs = ("AutoIncrement", "AutoIncrement_RBV",
             "AutoSave", "AutoSave_RBV",
             "Capture", "Capture_RBV",
             "EnableCallbacks",  "EnableCallbacks_RBV",
             "FileName", "FileName_RBV",
             "FileNumber",  "FileNumber_RBV",
             "FilePath",  "FilePath_RBV",
             "FilePathExists_RBV",
             "FileTemplate", "FileTemplate_RBV",
             "FileWriteMode", "FileWriteMode_RBV",
             "FullFileName_RBV",
             "NDArrayPort",  "NDArrayPort_RBV",
             "NumCapture", "NumCapture_RBV", "NumCaptured_RBV",
             "ReadFile", "ReadFile_RBV",
             "WriteFile", "WriteFile_RBV",
             "WriteMessage", "WriteStatus")

    _nonpvs = ('_prefix', '_pvs', '_delim')

    def __init__(self, prefix):
        Device.__init__(self, prefix, delim='', mutable=False,
                              attrs=self.attrs)

    def ensure_value(self, attr, value, wait=False):
        """ensures that an attribute with an associated _RBV value is
        set to the specifed value
        """
        rbv_attr = "%s_RBV" % attr
        if rbv_attr not in self._pvs:
            return self._pvs[attr].put(value, wait=wait)

        if  self._pvs[rbv_attr].get(as_string=True) != value:
            self._pvs[attr].put(value, wait=wait)


    def setFileName(self,fname):
        return self.put('FileName',fname)

    def nextFileNumber(self):
        self.setFileNumber(1+self.get('FileNumber'))

    def setFileNumber(self, fnum=None):
        if fnum is None:
            self.put('AutoIncrement', 1)
        else:
            self.put('AutoIncrement', 0)
            return self.put('FileNumber',fnum)

    def setPath(self,pathname):
        return self.put('FilePath', pathname)

    def setTemplate(self, fmt):
        return self.put('FileTemplate', fmt)

    def setWriteMode(self, mode):
        return self.put('FileWriteMode', mode)

    def getLastFileName(self):
        return self.get('FullFileName_RBV',as_string=True)

    def CaptureOn(self):
        return self.put('Capture', 1)

    def CaptureOff(self):
        return self.put('Capture', 0)

    def setNumCapture(self,n):
        return self.put('NumCapture', n)

    def WriteComplete(self):
        return (0==self.get('WriteFile_RBV') )

    def getTemplate(self):
        return self.get('FileTemplate_RBV',as_string=True)

    def getName(self):
        return self.get('FileName_RBV',as_string=True)

    def getNumber(self):
        return self.get('FileNumber_RBV')

    def getPath(self):
        return self.get('FilePath_RBV',as_string=True)

    def getFileNameByIndex(self,index):
        return self.getTemplate() % (self.getPath(), self.getName(), index)



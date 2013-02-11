import epics

class AD_FilePlugin(epics.Device):
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

    _fields = ('_prefix', '_pvs', '_delim', '_nchan', '_chans')

    def __init__(self, prefix):
        epics.Device.__init__(self, prefix, delim='', attrs=self.attrs)

    def ensure_value(self, attr, value, wait=False):
        """ensures that an attribute with an associated _RBV value is
        set to the specifed value
        """
        rbv_attr = "%s_RBV" % attr
        if rbv_attr not in self._pvs:
            return self._pvs[attr].put(value, wait=wait)

        if  self._pvs[rbv_attr].get(as_string=True) != value:
            self._pvs[attr].put(value, wait=wait)


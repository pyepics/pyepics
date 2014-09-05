from .. import Device

class AD_Camera(Device):
    """
    Basic AreaDetector Camera Device
    """
    attrs = ("Acquire", "AcquirePeriod", "AcquirePeriod_RBV",
             "AcquireTime", "AcquireTime_RBV",
             "ArrayCallbacks", "ArrayCallbacks_RBV",
             "ArrayCounter", "ArrayCounter_RBV", "ArrayRate_RBV",
             "ArraySizeX_RBV", "ArraySizeY_RBV", "ArraySize_RBV",
             "BinX", "BinX_RBV", "BinY", "BinY_RBV",
             "ColorMode", "ColorMode_RBV",
             "DataType", "DataType_RBV", "DetectorState_RBV",
             "Gain", "Gain_RBV", "ImageMode", "ImageMode_RBV",
             "MaxSizeX_RBV", "MaxSizeY_RBV",
             "MinX", "MinX_RBV", "MinY", "MinY_RBV",
             "NumImages", "NumImagesCounter_RBV", "NumImages_RBV",
             "SizeX", "SizeX_RBV", "SizeY", "SizeY_RBV",
             "TimeRemaining_RBV",
             "TriggerMode", "TriggerMode_RBV", "TriggerSoftware")


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


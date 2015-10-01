from .. import Device

class AD_ImagePlugin(Device):
    """
    AreaDetector Image Plugin
    """
    attrs = ('ArrayData',
             'UniqueId', 'UniqueId_RBV',
             'NDimensions', 'NDimensions_RBV',
             'ArraySize0', 'ArraySize0_RBV',
             'ArraySize1', 'ArraySize1_RBV',
             'ArraySize2', 'ArraySize2_RBV',
             'ColorMode', 'ColorMode_RBV')

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


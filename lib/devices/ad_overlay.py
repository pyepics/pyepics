from .. import Device

class AD_OverlayPlugin(Device):
    """
    AreaDetector Overlay Plugin
    """
    attrs = ('Name', 'Name_RBV',
             'Use', 'Use_RBV',
             'PositionX', 'PositionX_RBV',
             'PositionY', 'PositionY_RBV',
             'PositionXLink', 'PositionYLink', 
             'SizeXLink', 'SizeYLink', 
             'SizeX', 'SizeX_RBV',
             'SizeY', 'SizeY_RBV',
             'Shape', 'Shape_RBV',
             'DrawMode', 'DrawMode_RBV',
             'Red',    'Red_RBV',
             'Green', 'Green_RBV',
             'Blue', 'Blue_RBV')

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


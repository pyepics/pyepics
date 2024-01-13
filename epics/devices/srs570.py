#!/usr/bin/env python 
"""Epics Support for
Stanford Research Systems 570 current amplifier
"""
from .. import Device

VALID_STEPS = [1, 2, 5, 10, 20, 50, 100, 200, 500]
VALID_UNITS = ['pA/V', 'nA/V','uA/V', 'mA/V']

class SRS570(Device):
    """ 
    SRS (Stanford Research Systems) 570 current amplifier
    """

    attrs = ('sens_num', 'sens_unit', 'offset_num', 'offset_unit',
             'offset_sign', 'offset_on', 'off_u_put', 'bias_put',
             'gain_mode', 'filter_type', 'invert_on', 'init.PROC')
    
    _nonpvs = ('_prefix', '_pvs', '_delim', '_nchan', '_chans')
    
    def __init__(self, prefix):
        Device.__init__(self, prefix, delim='',
                        attrs=self.attrs, mutable=False)
        self.initialize()

    def initialize(self, bias=0, gain_mode=0, filter_type=0,
                   invert=False):
        """set initial values"""
        inv_val = 0
        if invert: inv_val = 1
        self.put('gain_mode', gain_mode) # 0 = low noise
        self.put('filter_type', filter_type) # 0  no filter
        self.put('invert_on', inv_val)
        self.put('bias_put', bias)
           
    def set_sensitivity(self, value, units, offset=None, 
                        scale_offset=True):
        "set sensitivity"
        if value not in VALID_STEPS or units not in VALID_UNITS:
            print('invalid input')
            return
        
        ival = VALID_STEPS.index(value)
        uval = VALID_UNITS.index(units)

        self.put('sens_num', ival)
        self.put('sens_unit', uval)
        if scale_offset:
            # scale offset to by 0.1 x sensitivity
            # i.e, a sensitivity of 200 nA/V should 
            # set set the input offset to 20 nA.
            ioff = ival - 3
            uoff = uval
            if ioff < 0:
                ioff = ival + 6
                uoff = uval - 1
            self.put('offset_num',  ioff)
            self.put('offset_unit', uoff)
        if offset is not None:
            self.set_offset(offset)
        self.put('init.PROC', 1)

    def set_offset(self, value):
        self.put('off_u_put', value)

    def increase_sensitivity(self):
        "increase sensitivity by 1 step"
        snum  = self.get('sens_num')
        sunit = self.get('sens_unit')
        if snum == 0:
            snum = 9
            sunit = sunit - 1
            if sunit < 0:
                # was at highest sensitivity
                snum, sunit = 1, 0
        snum = snum - 1
        self.set_sensitivity(VALID_STEPS[snum], VALID_UNITS[sunit])

    def decrease_sensitivity(self):
        "decrease sensitivity by 1 step"
        snum  = self.get('sens_num')
        sunit = self.get('sens_unit')
        if snum == 8:
            snum = -1
            sunit = sunit + 1
            if sunit > 3:
                # was at lowest sensitivity
                snum, sunit = 7, 3
        snum = snum + 1
        self.set_sensitivity(VALID_STEPS[snum], VALID_UNITS[sunit])


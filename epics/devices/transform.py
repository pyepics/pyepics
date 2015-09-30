#!/usr/bin/env python
"""Epics transform record"""
from .. import Device

class Transform(Device):
    "Epics transfrom record"

    attr_fmts = {'Value': '%s',
                 'Input': 'INP%s',
                 'Input_Valid': 'I%sV',
                 'Expression': 'CLC%s',
                 'Output':  'OUT%s',
                 'Output_Valid': 'O%sV',
                 'Comment': 'CMT%s',
                 'Expression_Valid': 'C%sV',
                 'Previous_Value': 'L%s'}

    rows = 'ABCDEFGHIJKLMNOP'
    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]

        self.attrs = ['COPT', 'PREC']
        for fmt in self.attr_fmts.values():
            for let in self.rows:
                self.attrs.append(fmt %  let)

        Device.__init__(self, prefix, delim='.',
                        attrs=self.attrs, **kwargs)

    def __validrow(self, row):
        return (isinstance(row, (str, unicode)) and
                len(row)==1 and row in self.rows)

    def get_row(self, row='A'):
        """get full data for a calculation 'row' (or letter):

        returns dictionary with keywords (and PV suffix for row='B'):

        'Value':             B
        'Input':             INPB
        'Input_Valid':       IBV
        'Expression':        CLCB
        'Output':            OUTB
        'Output_Valid':      OBV
        'Comment':           CMTB
        'Expression_Valid':  CBV
        'Previous_Value':    LB

        """
        if not self.__validrow(row):
            return None
        dat = {}
        for label, fmt in self.attr_fmts.items():
            dat[label] = self._pvs[fmt % row].get()
        return dat

    def set_row(self, row='A', data=None):
        """set full data for a calculation 'row' (or letter):

        data should be a dictionary as returned from get_row()
        """
        if not self.__validrow(row):
            return None
        for key, value in data.items():
            if key in self.attr_fmts:
                attr = self.attr_fmts[key] % row
                if self._pvs[attr].write_access:
                    self._pvs[attr].put(value)

    def set_calc(self, row='A', calc=''):
        """set calc for a 'row' (or letter):
        calc should be a string"""
        if not self.__validrow(row):
            return None
        self._pvs[self.attr_fmts['Expression'] % row].put(calc)

    def set_comment(self, row='A', comment=''):
        """set comment for a 'row' (or letter):
        comment should be a string"""
        if not self.__validrow(row):
            return None
        self._pvs[self.attr_fmts['Comment'] % row].put(calc)

    def set_input(self, row='A', input=''):
        """set input PV for a 'row' (or letter):
        input should be a string"""
        if not self.__validrow(row):
            return None
        self._pvs[self.attr_fmts['Input'] % row].put(calc)



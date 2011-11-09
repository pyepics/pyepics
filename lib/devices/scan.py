#!/usr/bin/env python
"""
Epics scan record
"""
import epics
import threading

NUM_POSITIONERS = 4
NUM_TRIGGERS    = 4
NUM_DETECTORS   = 70

class Scan(epics.Device):
    """
    A Device representing an Epics sscan record.

    The Scan Device represents an sscan record.
    """

    attrs = ('VAL', 'SMSG', 'CMND', 'NPTS', 'EXSC', 'NAME', 'PDLY',
             'PAUS', 'CPT')

    posit_attrs = ('PV', 'SP', 'EP', 'SI', 'CP', 'WD', 'PA', 'AR', 'SM')
    trig_attrs = ('PV', 'NV')

    _alias = {'device':      'P1PV',
              'start':       'P1SP',
              'end':         'P1EP',
              'step':        'P1SI',
              'table':       'P1PA',
              'absrel':      'P1AR',
              'mode':        'P1SM',
              'npts':        'NPTS',
              'execute':     'EXSC',
              'trigger':     'T1PV',
              'pause':       'PAUS',
              'current_point':  'CPT'}

    def __init__(self, name):
        """
        Initialize the scan.

        name: The name of the scan record.
        """
        attrs = list(self.attrs)
        for i in range(1, NUM_POSITIONERS+1):
            for a in posit_attrs:
                attrs.append('P%i%s' % (i, a))
        for i in range(1, NUM_TRIGGERS+1):
            for a in trig_attrs:
                attrs.append('T%i%s' % (i, a))
        for i in range(1, NUM_DETECTORS+1):
            attrs.append('D%2.2iPV' % i)

        self.waitSemaphore = threading.Semaphore(0)
        epics.Device.__init__(self, name, delim='.', attrs=attrs)
        for attr, pv in Scan._alias.items():
            self.add_pv('%s.%s' % (name,pv), attr)

        # make sure this is really a sscan!
        rectype = self.get('RTYP')
        if rectype != 'sscan':
            raise ScanException("%s is not an Epics Scan" % name)

        self.put('SMSG', '')
        self.put('NPTS', 0)
        for i in range(1, NUM_TRIGGERS+1):
            self.put('T%iPV' % i, '')

    def run(self, wait=False):
        """
        Execute the scan.
        """
        self.add_callback('EXSC', self._onDone)
        self.put('EXSC', 1)
        if wait:
            cbindex = self.waitSemaphore.acquire()
        self.remove_callbacks('EXSC', cbindex)
        # could consider using
        # self.put('EXSC', 1, use_complete=wait)

    def _onDone(self, **kwargs):
        if kwargs['value'] == 0:
            self.waitSemaphore.release()

    def reset(self):
        """Reset scan to some default values"""
        for i in range(1, NUM_TRIGGERS+1):
            self.put('T%iPV' % i, '')
        for i in range(1, NUM_POSITIONERS+1):
            self.put('P%iPV' % i, '')
        for i in range(1, NUM_DETECTORS+1):
            self.put('D%2.2iPV' % i, '')

    def _print(self):
        print('PV = %s' % self.get('P1PV'))
        print('SP = %s' % self.get('P1SP'))
        print('EP = %s' % self.get('P1EP'))
        print('NPTS = %s' % self.get('NPTS'))
        print(' T = %s' % self.get('T1PV'))

class ScanException(Exception):
    """ raised to indicate a problem with a scan"""
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)

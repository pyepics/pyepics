"""
Epics scan record
"""
import lib as epics
import threading

NUM_POSITIONERS = 4

class Scan(epics.Device):
    """
    A Device representing an Epics sscan record.
    
    The Scan Device represents an sscan record.
    
    """
    
    attrs = ('VAL', 'SMSG', 'CMND', 'NPTS', 'EXSC', 'NAME', 'PDLY',
             'PAUS', 'CPT')
    
    posit_attrs = ('P%iPV', 'P%iSP', 'P%iEP', 'T%iPV', 'D0%iPV')
    
    _alias = {
              'device':         'P1PV',
              'start':          'P1SP',
              'end':            'P1EP',
              'npts':           'NPTS',
              'execute':        'EXSC',
              'trigger':        'T1PV',
              'pause':          'PAUS',
              'current_point':  'CPT'}

    def __init__(self, name):
        """
        Initialize the scan.
        
        name: The name of the scan record.
        """
        attrs = list(self.attrs)
        for i in range(1,NUM_POSITIONERS):
            for att in self.posit_attrs:
                attrs.append(att % i)
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
        for i in range(1, NUM_POSITIONERS):
            self.put('T%iPV' % i, '')

    def run(self, wait=False):
        """
        Execute the scan.
        """
        if wait:
            self.add_callback('EXSC', self._onDone)
        self.put('EXSC', 1)
        if wait:
            cbindex = self.waitSemaphore.acquire()
            self.remove_callbacks('EXSC', cbindex)

    def _onDone(self, **kwargs):
        if kwargs['value'] == 0:
            self.waitSemaphore.release()
    
    def reset(self):
        """Reset scan to some default values"""
        for i in range(1, NUM_POSITIONERS):
            self.put('T%iPV' % i, '')
            self.put('P%iPV' % i, '')

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

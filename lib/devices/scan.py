"""
Epics scan record
"""
import epics

NUM_POSITIONERS = 4

class Scan(epics.Device):
    """
    A Epics scan record.
    
    A Scan object is a pyepics Device that represents a scan record. Current
    version is limited to linear scans. Typical usage for a simple scan:
    
       >>> s1 = Scan('L3:scan1')
       >>> s1.setPositioner(positioner='L3:psi', start=0. end=300)
       >>> s1.setNpts(20)
       >>> s1.run()
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
        
        epics.Device.__init__(self, name, delim='.', attrs=attrs)
        
        # make sure this is really a sscan!
        rectype = self.get('RTYP')
        if rectype != 'sscan':
            raise ScanException("%s is not an Epics Scan" % name)

        self.put('SMSG', '')
        self.put('NPTS]', 0)
        for i in range(1, NUM_POSITIONERS):
            self.put('T%iPV' % i, '')

    def __getattr__(self, attr):
        " internal method "
        if attr in self._alias:
            attr = self._alias[attr]
        if attr in self._pvs:
            return self.get(attr)
        if not attr.startswith('__'):
            try:
                self.PV(attr)
                return self.get(attr)
            except:
                raise ScanException("EpicsMotor has no attribute %s" % attr)
        else:
            return self.__dict__[attr]
                
    def __setattr__(self, attr, val):
        if attr in ('name', '_prefix', '_pvs', '_delim', '_init',
                    '_alias', '_nonpvs', '_extra', '_callbacks'):
            self.__dict__[attr] = val
            return 
        if attr in self._alias:
            attr = self._alias[attr]
        if attr in self._pvs:
            return self.put(attr, val)
        elif attr in self.__dict__: 
            self.__dict__[attr] = val           
        elif self._init:
            try:
                self.PV(attr)
                return self.put(attr, val)
            except:
                raise ScanException("EpicsScan has no attribute %s" % attr)


    def setPositioner(self, positioner = None, index=1):
        """
        Define a positioner for the scan
        
        index: Positioner id, (1,2,3 or 4). Default 1
        positioner: PV name of the positioner
        start: Start position of scan
        end:  End position of scan
        """
        if not positioner:
            #TODO: this is an error. Do something
            return
        
        self.put('P%iPV' % index, positioner)

        
    def setNpts(self, npts):
        """
        Define the number of points for the scan
        """
        self.put('NPTS', npts)
        
    def setStart(self, start=0, index=1):
        self.put("P%iSP" % index, start)

    def setEnd(self, end=0, index=1):
        self.put("P%iEP" % index, end)

    def setDelay(self, delay):
        self.put('PDLY', delay)

    def run(self):
        """
        Execute the scan.
        """
        self.put('EXSC', 1)
    
    def trigger(self, inner_scan):
        """
        Add an 'inner loop' scan.
        
        inner_scan: Scan to be triggered by this scan.
        """
        scanName = inner_scan.get('NAME')
        self.put('T1PV', scanName + '.EXSC')
        
    def reset(self):
        """Reset scan to some default values"""
        for i in range(1, NUM_POSITIONERS):
            self.put('T%iPV' % i, '')
            self.put('P%iPV' % i, '')
    
    def setPause(self, value):
        self.put('PAUS', value)
        
    def getCpt(self):
        return self.get('CPT')
        

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


if __name__ == '__main__':
    print('starting')
    s = Scan('L3:scan1')
    s.setPositioner(positioner='L3:psi.VAL')
    s.setStart(0)
    s.setEnd(300)
    s.setNpts(5)
    
    sinner = Scan('L3:scan2')
    sinner.setPositioner(positioner='L3:theta.VAL')
    sinner.setStart(20)
    sinner.setEnd(50)
    sinner.setNpts(3)
#    sinner.run()
    
    s.loop(sinner)
    s.run()
    print('ending')
    
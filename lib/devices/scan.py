"""
Epics scan record
"""
import epics

class Scan(epics.Device):
    """
    An Epics scan record.
    
    Uses linear scan.
    """
    
    attrs = ('VAL', 'SMSG', 'CMND', 'CPT', 'NPTS', 'EXSC', 'NAME')
    
    posit_attrs = ('P%iPV', 'P%iSP', 'P%iEP', 'T%iPV', 'D0%iPV')

    def __init__(self, prefix):
        """
        Constructor
        """
        attrs = list(self.attrs)
        for i in range(1,5):
            for att in self.posit_attrs:
                attrs.append(att % i)
        
        epics.Device.__init__(self, prefix, delim='.', attrs=attrs)

    def define(self, index=1, positioner = None, start=0, end=0, npts=0):

        if not positioner:
            #TODO: this is an error. Do something
            return
        
        self.put('P%iPV' % index, positioner)
        self.put('P%iSP' % index, start)
        self.put('P%iEP' % index, end)
        self.put('NPTS', npts)
        
    def run(self):
        self.put('EXSC', 1)
    
    def loop(self, inner_scan):
        scanName = inner_scan.get('NAME')
        self.put('T1PV', scanName + '.EXSC')


if __name__ == '__main__':
    print('starting')
    s = Scan('L3:scan1')
    s.define(positioner='L3:psi.VAL', start=0, end=360, npts=3)
    
    sinner = Scan('L3:scan2')
    sinner.define(positioner='L3:theta.VAL', start=20, end=300, npts=3)
    
    s.loop(sinner)
    s.run()
    print('ending')
    
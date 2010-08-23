import sys

import epics
import pvnames

p = epics.PV(pvnames.double_pv)
val = p.get()

sys.stdout.write( 'PV    =  %s\n' % p)
sys.stdout.write( 'Value = %s\n' % repr(val))
sys.stdout.write('Info Paragraph:\n')
sys.stdout.write('%s\n' %p.info)


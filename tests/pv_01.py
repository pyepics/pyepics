import sys
import time
import epics
import pvnames

p = epics.PV(pvnames.double_pv)

sys.stdout.write( 'PV    =  %s\n' % p)
sys.stdout.write( 'Value = %s\n' % repr(p.value))
sys.stdout.write('Info Paragraph:\n')
sys.stdout.write('%s\n' %p.info)


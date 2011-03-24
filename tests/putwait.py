"""This script tests using EPICS CA and Python threads together

Based on code from  Friedrich Schotte, NIH, modified by Matt Newville
20-Apr-2010
"""

import time
import epics
import sys
import pvnames 

write = sys.stdout.write
flush = sys.stdout.flush

write('initial put: \n')
epics.caput(pvnames.motor1, -2.0)
epics.caput(pvnames.motor2, 33.0)

write('sleep...')
time.sleep(2.0)
flush()

write('now put with wait: \n')
flush()

epics.caput(pvnames.motor2, -20.0, wait=True)
write('done with move 1\n')
flush()

epics.caput(pvnames.motor2, 20.0, wait=True)
write('done with move 2\n')

epics.caput(pvnames.motor2, -20.0, wait=True)
write('done with move 3\n')

epics.caput(pvnames.motor2, 20.0, wait=True)
write('done with move 4\n')

from __future__ import print_function

import sys
import time

import epics

from pvnames import motor_list

pvnames= []
for a in ('VAL','RBV','DVAL', 'RVAL','LLM','HLM','DIR','OFF',
          'FOFF','VELO','VBAS','ACCL','DESC','MRES'):
    for m in motor_list:
        pvnames.append("%s.%s" %(m,a))

print( pvnames)

def testconnect(pvnames,connect=True):
    t0 = time.time()
    pvlist= []
    for pvname in pvnames:
        x = epics.PV(pvname)
        if connect:    
            x.connect()
        pvlist.append(x)
        
    for x in pvlist:
        x.get()

    dt = time.time()-t0
#    for x in pvlist:
#        x.get()
    sys.stdout.write('===Connect with PV(connect=%s) to %i pvs\n' % (connect, len(pvlist)))
    sys.stdout.write('   Total Time = %.4f s, Time per PV = %.1f ms\n' % ( dt, 1000.*dt/len(pvlist)))


sys.stdout.write( """
Test connection time for many PVs.

With:
  pvs = []
  for pvn in pvnames:
      x = epics.PV(pvn)
      x.connect()
      pvs.append(x)

  for x in pvs: x.get()
  
connection takes 30ms per PV

With
  pvs = []
  for pvname in pvlist:
      x = PV(pvname)
      pvs.append(x)

  for x in pvs: x.get()

connection takes less than 8ms per PV.
""")

testconnect(pvnames, False)

epics.ca._cache = {}

testconnect(pvnames, True)

print( 'Done')

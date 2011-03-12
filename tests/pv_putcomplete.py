import epics
import time
import pvnames

vals = (1.35, 1.50, 1.44, 1.445, 1.45, 1.45, 1.4505, 1.453, 1.446, 1.447, 1.450, 1.450, 1.490, 1.5, 1.500)
    
p = epics.PV(pvnames.motor1)

for v in vals:
    t0 = time.time()
    p.put(v) 
    count = 0
    for i in range(100000):
        time.sleep(0.001)
	count = count + 1
        if p.put_complete:
            break
    print 'Done  value= %.3f, elapsed time= %.4f sec (count=%i)' % (v, time.time()-t0, count)


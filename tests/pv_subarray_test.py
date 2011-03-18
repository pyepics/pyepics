import time
import epics
import pvnames
import random
import numpy
driver = epics.PV(pvnames.subarr_driver)
sub1   = epics.PV(pvnames.subarr1)
sub2   = epics.PV(pvnames.subarr2)
sub3   = epics.PV(pvnames.subarr3)
sub4   = epics.PV(pvnames.subarr4)

print driver.get()
print sub1.get()
print sub2.get()
time.sleep(1)
print '====================='

for i in range(10):
    driver.put([random.random() for x in range(16)])
    time.sleep(0.1)
    d = driver.get()
    print ' test ' , i
    print 'input array = ', d
    
    x = numpy.array([sub1.get(), sub2.get(), sub3.get(), sub4.get()])
    time.sleep(0.1)
    print 'subarrays = ', x
    print 'Total difference of driver and subarrays = ', (d - x.flatten()).sum()
    time.sleep(1.0)
    print '======'

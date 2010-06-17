import epics
import time
m1 = epics.Motor('13XRM:m1')
m1.drive =  0.0
m1.tweak_val = 0.10
m1.move(0.0, wait=True)

for i in range(20):
    m1.tweak(dir='forward', wait=True)
    print 'Motor:  ', m1.description , m1.drive, ' Currently at ', m1.readback
    time.sleep(0.5)

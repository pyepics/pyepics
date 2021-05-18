from __future__ import print_function
import epics
import time
import pvnames

epics.ca.DEFAULT_CONNECTION_TIMEOUT=10.

def test1(motorname, start, step, npts):
    "simple test: stepping with wait"
    m1 = epics.Motor(motorname)
    m1.drive =  start
    m1.tweak_val = step
    m1.move(start, wait=True)

    for i in range(npts):
        m1.tweak(dir='forward', wait=True)
        print('Motor:  ', m1.description , m1.drive, ' Currently at ', m1.readback)
        time.sleep(0.01)

def testDial(motorname,start, step, npts, offset=1.0):
    "test using dial coordinates"
    m1 = epics.Motor(motorname)
    m1.offset = offset
    m1.tweak_val = step
    m1.move(start, wait=True, dial=True)
    
    print('Motor position ', motorname, m1.description)
    user = m1.get_position()
    dial = m1.get_position(dial=True)
    raw  = m1.get_position(raw=True)
    print(' User/Dial/Raw = %f / %f / %f' % (user, dial, raw))


testDial(pvnames.motor1, 0.5, 0.01, 10, offset=0.1)

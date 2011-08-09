import time
import epics
import pvnames
pvname = pvnames.double_pv

mypv = epics.PV(pvname)


def wait(timeout=6):
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(1.e-3)
        epics.poll()


print( 'Created PV = ', mypv)
def CB1(pvname=None, value=None, char_value=None, **kw):
    print( 'CB1 PV Changed! ', pvname, value, char_value )


def CB2(pvname=None, value=None, char_value=None, **kw):
    print( 'CB2 ! ', pvname, value, char_value)

mypv.add_callback(CB1)

print( 'Added a callback.  Now wait for changes')

print( 'ready')

wait(10)
print( 'now, add another: ')
mypv.add_callback(CB2)

wait(10)




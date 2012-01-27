import time
import epics
import sys
import pvnames

pvname = pvnames.updating_pv1 # motor1

mypv = epics.PV(pvname)

write = sys.stdout.write

mypv.get_ctrlvars()

write('Created PV = %s\n' % mypv)
def onChanges(pvname=None, value=None, char_value=None, **kw):
    write( 'PV %s %s, %s Changed!\n' % (pvname, repr(value), char_value))

mypv.add_callback(onChanges)

write('Added a callback.  Now wait for changes...\n')

def wait(timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout: time.sleep(1.e-4)

wait(10)

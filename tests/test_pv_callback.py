import time
import epics
import sys
import pvnames

pvname = pvnames.updating_pv1 # motor1
write = sys.stdout.write

def wait(timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(1.e-4)

change_count = 0
def onChanges(pvname=None, value=None, char_value=None, **kw):
    global change_count
    change_count += 1
    try:
        write( 'PV %s %s, %s Changed!\n' % (pvname, repr(value), char_value))
    except:
        pass

def test_pv_callback():
    mypv = epics.get_pv(pvname)
    global change_count
    mypv.get_ctrlvars()
    mypv.add_callback(onChanges)
    wait(5)
    assert change_count > 5

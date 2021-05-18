import time
import epics
import sys
import pvnames

# Test than when a PV connections all callbacks fire successfully
#
# does not require Setup/simulator.py to be running (PV is deliberately one which does not change)

write = sys.stdout.write


def wait(timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(1.e-4)

got_callback_a = False
got_callback_b = False

def callback_a(pvname=None, value=None, **kw):
    global got_callback_a
    write( "Got callback A (%s, %s)\n" % (pvname, repr(value)) )
    got_callback_a = True

def callback_b(pvname=None, value=None, **kw):
    global got_callback_b
    write( "Got callback B (%s, %s)\n" % (pvname, repr(value)) )
    got_callback_b = True

def CB1(pvname=None, value=None, char_value=None, **kw):
    print( 'CB1 PV Changed! ', pvname, value, char_value )

def CB2(pvname=None, value=None, char_value=None, **kw):
    print( 'CB2 ! ', pvname, value, char_value)


def test_initial_callbacks():
    global got_callback_a, got_callback_b
    pvname = pvnames.non_updating_pv
    mypv = epics.PV(pvname, callback=(callback_a, callback_b))

    wait(3)
    assert mypv.connected
    assert got_callback_a
    assert got_callback_b

def test_multiple_callbacks():
    global got_callback_a, got_callback_b
    got_callback_a =  got_callback_b = False
    mypv = epics.PV(pvnames.double_pv)
    mypv.add_callback(callback_a)

    wait(2)
    assert got_callback_a
    assert not got_callback_b

    mypv.add_callback(callback_b)
    wait(2)
    assert got_callback_b


if __name__ == '__main__':
    test_initial_callbacks()
    test_multiple_callbacks()

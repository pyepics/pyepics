import time
import epics
import sys
import pvnames

# Test than when a PV connections all callbacks fire successfully
#
# does not require Setup/simulator.py to be running (PV is deliberately one which does not change)

write = sys.stdout.write

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


pvname = pvnames.non_updating_pv
mypv = epics.PV(pvname, callback=(callback_a, callback_b))

write('Created PV with two callbacks = %s\n' % mypv)

write('Now wait for changes...\n')

def wait(timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout and not (got_callback_a and got_callback_b):
        time.sleep(1.e-4)

wait(2)

if not mypv.connected:
    write('ERROR: PV never connected\n')
    sys.exit(1)

if not (got_callback_a and got_callback_b):
    write('ERROR: Inconsistent initial value callbacks - callback A = %s, callback B = %s\n'
          % (got_callback_a, got_callback_b) )
    sys.exit(1)

write('Got both callbacks OK!\n')

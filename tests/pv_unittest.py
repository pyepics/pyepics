#!/usr/bin/env python
# unit-tests for ca interface

import os
import sys
import time
import unittest
import numpy
from epics import PV, caput, caget, ca

import pvnames

def write(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

CONN_DAT ={}
CHANGE_DAT = {}

def onConnect(pvname=None, conn=None, chid=None,  **kws):
    write('  :Connection status changed:  %s  connected=%s\n' % (pvname, conn))
    global CONN_DAT
    CONN_DAT[pvname] = conn

def onChanges(pvname=None, value=None, **kws):
    write( '/// New Value: %s  value=%s, kw=%s\n' %( pvname, str(value), repr(kws)))
    global CHANGE_DAT
    CHANGE_DAT[pvname] = value

def pause_updating():
    caput(pvnames.pause_pv, 1)

def resume_updating():
    caput(pvnames.pause_pv, 0)

class PV_Tests(unittest.TestCase):
    def testA_CreatePV(self):
        write('Simple Test: create pv\n')
        pv = PV(pvnames.double_pv)
        self.assertNotEqual(pv, None)

    def testA_CreatedWithConn(self):
        write('Simple Test: create pv with conn callback\n')
        pv = PV(pvnames.int_pv,
                connection_callback=onConnect)
        val = pv.get()

        global CONN_DAT
        conn = CONN_DAT.get(pvnames.int_pv, None)
        self.assertEqual(conn, True)

    def test_caget(self):
        write('Simple Test of caget() function\n')
        pvs = (pvnames.double_pv, pvnames.enum_pv, pvnames.str_pv)
        for p in pvs:
            val = caget(p)
            self.assertNotEqual(val, None)
        sval = caget(pvnames.str_pv)
        self.assertEqual(sval, 'ao')

    def test_get1(self):
        write('Simple Test: test value and char_value on an integer\n')
        pause_updating()
        pv = PV(pvnames.int_pv)
        val = pv.get()
        cval = pv.get(as_string=True)

        self.failUnless(int(cval)== val)
        resume_updating()


    def test_stringarray(self):
        write('String Array: \n')
        pause_updating()
        pv = PV(pvnames.string_arr_pv)
        val = pv.get()
        self.failUnless(len(val) > 10)
        self.failUnless(isinstance(val[0], str))
        self.failUnless(len(val[0]) > 1)
        self.failUnless(isinstance(val[1], str))
        self.failUnless(len(val[1]) > 1)
        resume_updating()

    def test_putcomplete(self):
        write('Put with wait and put_complete (using real motor!) \n')
        vals = (1.35, 1.50, 1.44, 1.445, 1.45, 1.453, 1.446, 1.447, 1.450, 1.450, 1.490, 1.5, 1.500)
        p = PV(pvnames.motor1)
        see_complete = []
        for v in vals:
            t0 = time.time()
            p.put(v, use_complete=True)
            count = 0
            for i in range(100000):
                time.sleep(0.001)
                count = count + 1
                if p.put_complete:
                    see_complete.append(True)
                    break
                # print( 'made it to value= %.3f, elapsed time= %.4f sec (count=%i)' % (v, time.time()-t0, count))
        self.failUnless(len(see_complete) > (len(vals) - 5))

    def test_putwait(self):
        write('Put with wait (using real motor!) \n')
        pv = PV(pvnames.motor1)
        val = pv.get()

        t0 = time.time()
        if  val < 5:
            pv.put(val + 1.0, wait=True)
        else:
            pv.put(val - 1.0, wait=True)
        dt = time.time()-t0
        write('    put took %s sec\n' % dt)
        self.failUnless( dt > 0.1)

        # now with a callback!
        global put_callback_called
        put_callback_called = False

        def onPutdone(pvname=None, **kws):
            print( 'put done ', pvname, kws)
            global put_callback_called
            put_callback_called = True
        val = pv.get()
        if  val < 5:
            pv.put(val + 1.0, callback=onPutdone)
        else:
            pv.put(val - 1.0, callback=onPutdone)

        t0 = time.time()
        while time.time()-t0 < dt*1.50:
            time.sleep(0.02)

        write('    put should be done by now?  %s \n' % put_callback_called)
        self.failUnless(put_callback_called)

        # now using pv.put_complete
        val = pv.get()
        if  val < 5:
            pv.put(val + 1.0, use_complete=True)
        else:
            pv.put(val - 1.0, use_complete=True)
        t0 = time.time()
        count = 0
        while time.time()-t0 < dt*1.50:
            if pv.put_complete:
                break
            count = count + 1
            time.sleep(0.02)
        write('    put_complete=%s (should be True), and count=%i (should be>3)\n' %
              (pv.put_complete, count))
        self.failUnless(pv.put_complete)
        self.failUnless(count > 3)

    def test_get_callback(self):
        write("Callback test:  changing PV must be updated\n")
        global NEWVALS
        mypv = PV(pvnames.updating_pv1)
        NEWVALS = []
        def onChanges(pvname=None, value=None, char_value=None, **kw):
            write( 'PV %s %s, %s Changed!\n' % (pvname, repr(value), char_value))
            NEWVALS.append( repr(value))

        mypv.add_callback(onChanges)
        write('Added a callback.  Now wait for changes...\n')

        t0 = time.time()
        while time.time() - t0 < 3:
            time.sleep(1.e-4)
        write('   saw %i changes.\n' % len(NEWVALS))
        self.failUnless(len(NEWVALS) > 3)
        mypv.clear_callbacks()


    def test_subarrays(self):
        write("Subarray test:  dynamic length arrays\n")
        driver = PV(pvnames.subarr_driver)
        subarr1 = PV(pvnames.subarr1)
        subarr1.connect()

        len_full = 64
        len_sub1 = 16
        full_data = numpy.arange(len_full)/1.0

        caput("%s.NELM" % pvnames.subarr1, len_sub1)
        caput("%s.INDX" % pvnames.subarr1, 0)


        driver.put(full_data) ;
        time.sleep(0.1)
        subval = subarr1.get()

        self.assertEqual(len(subval), len_sub1)
        self.failUnless(numpy.all(subval == full_data[:len_sub1]))
        write("Subarray test:  C\n")
        caput("%s.NELM" % pvnames.subarr2, 19)
        caput("%s.INDX" % pvnames.subarr2, 3)

        subarr2 = PV(pvnames.subarr2)
        subarr2.get()

        driver.put(full_data) ;   time.sleep(0.1)
        subval = subarr2.get()

        self.assertEqual(len(subval), 19)
        self.failUnless(numpy.all(subval == full_data[3:3+19]))

        caput("%s.NELM" % pvnames.subarr2, 5)
        caput("%s.INDX" % pvnames.subarr2, 13)

        driver.put(full_data) ;   time.sleep(0.1)
        subval = subarr2.get()

        self.assertEqual(len(subval), 5)
        self.failUnless(numpy.all(subval == full_data[13:5+13]))

    def testEnumPut(self):
        pv = PV(pvnames.enum_pv)
        self.assertNotEqual(pv, None)
        pv.put('Stop')
        time.sleep(0.1)
        val = pv.get()
        self.assertEqual(val, 0)


    def test_DoubleVal(self):
        pvn = pvnames.double_pv
        pv = PV(pvn)
        pv.get()
        cdict  = pv.get_ctrlvars()
        write( 'Testing CTRL Values for a Double (%s)\n'   % (pvn))
        self.failUnless('severity' in cdict)
        self.failUnless(len(pv.host) > 1)
        self.assertEqual(pv.count,1)
        self.assertEqual(pv.precision, pvnames.double_pv_prec)
        units= ca.BYTES2STR(pv.units)
        self.assertEqual(units, pvnames.double_pv_units)
        self.failUnless(pv.access.startswith('read'))


    def test_type_converions_2(self):
        write("CA type conversions arrays\n")
        pvlist = (pvnames.char_arr_pv,
                  pvnames.long_arr_pv,
                  pvnames.double_arr_pv)
        pause_updating()
        chids = []
        for name in pvlist:
            chid = ca.create_channel(name)
            ca.connect_channel(chid)
            chids.append((chid, name))
            ca.poll(evt=0.025, iot=5.0)
        ca.poll(evt=0.05, iot=10.0)

        values = {}
        for chid, name in chids:
            values[name] = ca.get(chid)
        for promotion in ('ctrl', 'time'):
            for chid, pvname in chids:
                write('=== %s  chid=%s as %s\n' % (ca.name(chid),
                                                   repr(chid), promotion))
                time.sleep(0.01)
                if promotion == 'ctrl':
                    ntype = ca.promote_type(chid, use_ctrl=True)
                else:
                    ntype = ca.promote_type(chid, use_time=True)

                val  = ca.get(chid, ftype=ntype)
                cval = ca.get(chid, as_string=True)
                for a, b in zip(val, values[pvname]):
                    self.assertEqual(a, b)

        resume_updating()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase( PV_Tests)
    unittest.TextTestRunner(verbosity=1).run(suite)


#     chid = ca.create_channel(pvnames.int_pv,
#                              callback=onConnect)
#
#     time.sleep(0.1)


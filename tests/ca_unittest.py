#!/usr/bin/env python
# test expression parsing

import os
import sys
import time
import unittest
import numpy
import ctypes
from contextlib import contextmanager
from epics import ca, dbr, caput

import pvnames

def _ca_connect(chid,timeout=5.0):
    n  = 0
    t0 = time.time()
    conn = 2==ca.state(chid)
    while (not conn) and (time.time()-t0 < timeout):
        ca.poll(1.e-6,1.e-4)
        conn = 2==ca.state(chid)
        n += 1
    return conn, time.time()-t0, n

def write(msg):
    sys.stdout.write('%s\n'% msg)
    sys.stdout.flush()

CONN_DAT ={}
CHANGE_DAT = {}

def onConnect(pvname=None, conn=None, chid=None,  **kws):
    write('  /// Connection status changed:  %s  %s' % (pvname, repr(kws)))
    global CONN_DAT
    CONN_DAT[pvname] = conn

def onChanges(pvname=None, value=None, **kws):
    write( '/// New Value: %s  value=%s, kw=%s' %( pvname, str(value), repr(kws)))
    global CHANGE_DAT
    CHANGE_DAT[pvname] = value

@contextmanager
def no_simulator_updates():
    '''Context manager which pauses and resumes simulator PV updating'''
    try:
        caput(pvnames.pause_pv, 1)
        yield
    finally:
        caput(pvnames.pause_pv, 0)

class CA_BasicTests(unittest.TestCase):

    def setUp(self):
        write('Starting %s...' % self.id().split(".")[-1])
    def tearDown(self):
        write('Completed %s...\n' % self.id().split(".")[-1])

    def testA_CreateChid(self):
        write('Simple Test: create chid')
        chid = ca.create_channel(pvnames.double_pv)
        self.assertIsNot(chid, None)

    def testA_GetNonExistentPV(self):
        write('Simple Test: get on a non-existent PV')
        chid = ca.create_channel('Definitely-Not-A-Real-PV')
        self.assertRaises(ca.ChannelAccessException, ca.get, chid)

    def testA_CreateChid_CheckTypeCount(self):
        write('Simple Test: create chid, check count, type, host, and access')
        chid = ca.create_channel(pvnames.double_pv)
        ret = ca.connect_channel(chid)
        ca.pend_event(1.e-3)

        ftype  = ca.field_type(chid)
        count  = ca.element_count(chid)
        host    = ca.host_name(chid)
        rwacc = ca.access(chid)

        self.assertIsNot(chid, None)
        self.assertIsNot(host, None)
        self.assertEqual(count, 1)
        self.assertEqual(ftype, 6)
        self.assertEqual(rwacc,'read/write')


    def testA_CreateChidWithConn(self):
        write('Simple Test: create chid with conn callback')
        chid = ca.create_channel(pvnames.int_pv,
                                 callback=onConnect)
        val = ca.get(chid)

        global CONN_DAT
        conn = CONN_DAT.get(pvnames.int_pv, None)
        self.assertEqual(conn, True)

    def test_dbrName(self):
        write( 'DBR Type Check')
        self.assertEqual(dbr.Name(dbr.STRING), 'STRING')
        self.assertEqual(dbr.Name(dbr.FLOAT),  'FLOAT')
        self.assertEqual(dbr.Name(dbr.ENUM), 'ENUM')
        self.assertEqual(dbr.Name(dbr.CTRL_CHAR), 'CTRL_CHAR')
        self.assertEqual(dbr.Name(dbr.TIME_DOUBLE), 'TIME_DOUBLE')
        self.assertEqual(dbr.Name(dbr.TIME_LONG), 'TIME_LONG')

        self.assertEqual(dbr.Name('STRING', reverse=True), dbr.STRING)
        self.assertEqual(dbr.Name('DOUBLE', reverse=True), dbr.DOUBLE)
        self.assertEqual(dbr.Name('CTRL_ENUM', reverse=True), dbr.CTRL_ENUM)
        self.assertEqual(dbr.Name('TIME_LONG', reverse=True), dbr.TIME_LONG)

    def test_Connect1(self):
        chid = ca.create_channel(pvnames.double_pv)
        conn,dt,n = _ca_connect(chid, timeout=2)
        write( 'CA Connection Test1: connect to existing PV')
        write( ' connected in %.4f sec' % (dt))
        self.assertEqual(conn,True)

    def test_Connected(self):
        pvn = pvnames.double_pv
        chid = ca.create_channel(pvn,connect=True)
        isconn = ca.isConnected(chid)
        write( 'CA test Connected (%s) = %s' % (pvn,isconn))
        self.assertEqual(isconn,True)
        state= ca.state(chid)
        self.assertEqual(state,ca.dbr.CS_CONN)
        acc = ca.access(chid)
        self.assertEqual(acc,'read/write')


    def test_DoubleVal(self):
        pvn = pvnames.double_pv
        chid = ca.create_channel(pvn,connect=True)
        cdict  = ca.get_ctrlvars(chid)
        write( 'CA testing CTRL Values for a Double (%s)'   % (pvn))
        self.failUnless('units' in cdict)
        self.failUnless('precision' in cdict)
        self.failUnless('severity' in cdict)

        hostname = ca.host_name(chid)
        self.failUnless(len(hostname) > 1)

        count = ca.element_count(chid)
        self.assertEqual(count,1)

        ftype= ca.field_type(chid)
        self.assertEqual(ftype,ca.dbr.DOUBLE)

        prec = ca.get_precision(chid)
        self.assertEqual(prec, pvnames.double_pv_prec)

        units= ca.BYTES2STR(ca.get_ctrlvars(chid)['units'])
        self.assertEqual(units, pvnames.double_pv_units)

        rwacc= ca.access(chid)
        self.failUnless(rwacc.startswith('read'))


    def test_UnConnected(self):
        write( 'CA Connection Test1: connect to non-existing PV (2sec timeout)')
        chid = ca.create_channel('impossible_pvname_certain_to_fail')
        conn,dt,n = _ca_connect(chid, timeout=2)
        self.assertEqual(conn,False)


    def test_putwait(self):
        'test put with wait'
        pvn = pvnames.non_updating_pv
        chid = ca.create_channel(pvn, connect=True)
        o  = ca.put(chid, -1, wait=True)
        val = ca.get(chid)
        self.assertEqual(val, -1)
        o  = ca.put(chid, 2, wait=True)
        val = ca.get(chid)
        self.assertEqual(val, 2)

    def test_promote_type(self):
        pvn = pvnames.double_pv
        chid = ca.create_channel(pvn,connect=True)
        write( 'CA promote type (%s)' % (pvn))
        f_t  = ca.promote_type(chid,use_time=True)
        f_c  = ca.promote_type(chid,use_ctrl=True)
        self.assertEqual(f_t, ca.dbr.TIME_DOUBLE)
        self.assertEqual(f_c, ca.dbr.CTRL_DOUBLE)

    def test_ProcPut(self):
        pvn  = pvnames.enum_pv
        chid = ca.create_channel(pvn, connect=True)
        write( 'CA test put to PROC Field (%s)' % (pvn))
        for input in (1, '1', 2, '2', 0, '0', 50, 1):
            ret = None
            try:
                ret = ca.put(chid, 1)
            except:
                pass
            self.assertIsNot(ret, None)

    def test_subscription_double(self):
        pvn = pvnames.updating_pv1
        chid = ca.create_channel(pvn,connect=True)
        cb, uarg, eventID = ca.create_subscription(chid, callback=onChanges)

        start_time = time.time()
        global CHANGE_DAT
        while time.time()-start_time < 5.0:
            time.sleep(0.01)
            if CHANGE_DAT.get(pvn, None) is not None:
                break
        val = CHANGE_DAT.get(pvn, None)
        ca.clear_subscription(eventID)
        self.assertIsNot(val, None)

    def test_subscription_custom(self):
        pvn = pvnames.updating_pv1
        chid = ca.create_channel(pvn, connect=True)

        global change_count
        change_count = 0

        def my_callback(pvname=None, value=None, **kws):
            write( ' Custom Callback  %s  value=%s' %(pvname, str(value)))
            global change_count
            change_count = change_count + 1

        cb, uarg, eventID = ca.create_subscription(chid, callback=my_callback)

        start_time = time.time()
        while time.time()-start_time < 2.0:
            time.sleep(0.01)

        ca.clear_subscription(eventID)
        time.sleep(0.2)
        self.assertTrue(change_count > 2)

    def test_subscription_str(self):

        pvn = pvnames.updating_str1
        write(" Subscription on string: %s " % pvn)
        chid = ca.create_channel(pvn,connect=True)
        cb, uarg, eventID = ca.create_subscription(chid, callback=onChanges)

        start_time = time.time()
        global CHANGE_DAT
        while time.time()-start_time < 3.0:
            time.sleep(0.01)
            ca.put(chid, "%.1f" % (time.time()-start_time) )
            if CHANGE_DAT.get(pvn, None) is not None:
                break
        val = CHANGE_DAT.get(pvn, None)
        # ca.clear_subscription(eventID)
        self.assertIsNot(val, None)
        time.sleep(0.2)


    def _test_array_callback(self, arrayname, array_type, length, element_type):
        """ Helper function to subscribe to a PV array and check it
        receives at least one subscription callback w/ specified type,
        length & uniform element type. Checks separately for normal,
        TIME & CTRL subscription variants. Returns the array or fails
        an assertion."""
        results = {}
        for form in [ 'normal', 'time', 'ctrl' ]:
            chid = ca.create_channel(arrayname,connect=True)
            cb, uarg, eventID = ca.create_subscription(chid, use_time=form=='time', use_ctrl=form=='ctrl', callback=onChanges)

            CHANGE_DAT.pop(arrayname, None)
            timeout=0
            # wait up to 6 seconds, if no callback probably due to simulator.py
            # not running...
            while timeout<120 and not arrayname in CHANGE_DAT:
                time.sleep(0.05)
                timeout = timeout+1
            val = CHANGE_DAT.get(arrayname, None)
            ca.clear_subscription(eventID)
            self.assertIsNot(val, None)
            self.assertEqual(type(val), array_type)
            self.assertEqual(len(val), length)
            self.assertEqual(type(val[0]), element_type)
            self.assertTrue(all( type(e)==element_type for e in val))
            results[form] = val
        return results

    def test_subscription_long_array(self):
        """ Check that numeric arrays callbacks successfully send correct data """
        self._test_array_callback(pvnames.long_arr_pv, numpy.ndarray, 2048, numpy.int32)

    def test_subscription_double_array(self):
        """ Check that double arrays callbacks successfully send correct data """
        self._test_array_callback(pvnames.double_arr_pv, numpy.ndarray, 2048, numpy.float64)

    def test_subscription_string_array(self):
        """ Check that string array callbacks successfully send correct data """
        results = self._test_array_callback(pvnames.string_arr_pv, list, 128, str)
        self.assertTrue(len(results["normal"][0]) > 0)
        self.assertTrue(len(results["time"][0]) > 0)
        self.assertTrue(len(results["ctrl"][0]) > 0)

    def test_subscription_char_array(self):
        """ Check that uchar array callbacks successfully send correct data as arrays """
        self._test_array_callback(pvnames.char_arr_pv, numpy.ndarray, 128, numpy.uint8)



    def test_Values(self):
        write( 'CA test Values (compare 5 values with caget)')
        os.system('rm ./caget.tst')
        vals = {}
        with no_simulator_updates():
            for pvn in (pvnames.str_pv,  pvnames.int_pv,
                        pvnames.float_pv, pvnames.enum_pv,
                        pvnames.long_pv):
                os.system('caget  -n -f5 %s >> ./caget.tst' % pvn)
                chid = ca.create_channel(pvn)
                ca.connect_channel(chid)
                vals[pvn] = ca.get(chid)
            rlines = open('./caget.tst', 'r').readlines()
            for line in rlines:
                pvn, sval = [i.strip() for i in line[:-1].split(' ', 1)]
                tval = str(vals[pvn])
                if pvn in (pvnames.float_pv,pvnames.double_pv):
                    # use float precision!
                    tval = "%.5f" % vals[pvn]
                self.assertEqual(tval, sval)

    def test_type_converions_1(self):
        write("CA type conversions scalars")
        pvlist = (pvnames.str_pv, pvnames.int_pv, pvnames.float_pv,
                  pvnames.enum_pv,  pvnames.long_pv,  pvnames.double_pv2)
        chids = []
        with no_simulator_updates():
            for name in pvlist:
                chid = ca.create_channel(name)
                ca.connect_channel(chid)
                chids.append((chid, name))
                ca.poll(evt=0.025, iot=5.0)
            ca.poll(evt=0.05, iot=10.0)

            values = {}
            for chid, name in chids:
                values[name] = ca.get(chid, as_string=True)

            for promotion in ('ctrl', 'time'):
                for chid, pvname in chids:
                    write('=== %s  chid=%s as %s' % (ca.name(chid), repr(chid),
                                                     promotion))
                    time.sleep(0.01)
                    if promotion == 'ctrl':
                        ntype = ca.promote_type(chid, use_ctrl=True)
                    else:
                        ntype = ca.promote_type(chid, use_time=True)

                    val  = ca.get(chid, ftype=ntype)
                    cval = ca.get(chid, as_string=True)
                    if ca.element_count(chid) > 1:
                        val = val[:12]
                    self.assertEqual(cval, values[pvname])

    def test_type_converions_2(self):
        write("CA type conversions arrays")
        pvlist = (pvnames.char_arr_pv,
                  pvnames.long_arr_pv,
                  pvnames.double_arr_pv)
        with no_simulator_updates():
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
                    write('=== %s  chid=%s as %s' % (ca.name(chid), repr(chid),
                                                     promotion))
                    time.sleep(0.01)
                    if promotion == 'ctrl':
                        ntype = ca.promote_type(chid, use_ctrl=True)
                    else:
                        ntype = ca.promote_type(chid, use_time=True)

                    val  = ca.get(chid, ftype=ntype)
                    cval = ca.get(chid, as_string=True)
                    for a, b in zip(val, values[pvname]):
                        self.assertEqual(a, b)


    def test_Array0(self):
        write('Array Test: get double array as numpy array, ctypes Array, and list')
        chid = ca.create_channel(pvnames.double_arrays[0])
        aval = ca.get(chid)
        cval = ca.get(chid, as_numpy=False)

        self.assertTrue(isinstance(aval, numpy.ndarray))
        self.assertTrue(len(aval) > 2)

        self.assertTrue(isinstance(cval, ctypes.Array))
        self.assertTrue(len(cval) > 2)
        lval = list(cval)
        self.assertTrue(isinstance(lval, list))
        self.assertTrue(len(lval) > 2)
        self.assertTrue(lval == list(aval))

    def test_xArray1(self):
        write('Array Test: get(wait=False) / get_complete()')
        chid = ca.create_channel(pvnames.double_arrays[0])
        val0 = ca.get(chid)
        aval = ca.get(chid, wait=False)
        self.assertTrue(aval is  None)
        val1 = ca.get_complete(chid)
        self.assertTrue(all(val0 == val1))

    def test_xArray2(self):
        write('Array Test: get fewer than max vals using ca.get(count=0)')
        chid = ca.create_channel(pvnames.double_arrays[0])
        maxpts = ca.element_count(chid)
        npts = int(max(2, maxpts/2.3 - 1))
        write('max points is %s' % (maxpts, ))
        dat = numpy.random.normal(size=npts)
        write('setting array to a length of npts=%s' % (npts, ))
        ca.put(chid, dat)
        out1 = ca.get(chid)
        self.assertTrue(isinstance(out1, numpy.ndarray))
        self.assertEqual(len(out1), npts)
        out2 = ca.get(chid, count=0)
        self.assertTrue(isinstance(out2, numpy.ndarray))
        self.assertEqual(len(out2), npts)

    def test_xArray3(self):
        write('Array Test: get char array as string')
        chid = ca.create_channel(pvnames.char_arrays[0])
        val = ca.get(chid)
        self.assertTrue(isinstance(val, numpy.ndarray))
        char_val = ca.get(chid, as_string=True)
        self.assertTrue(isinstance(char_val, str))
        conv = ''.join([chr(i) for i in val])
        self.assertEqual(conv, char_val)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase( CA_BasicTests)
    unittest.TextTestRunner(verbosity=1).run(suite)


#     chid = ca.create_channel(pvnames.int_pv,
#                              callback=onConnect)
#
#     time.sleep(0.1)
# ;

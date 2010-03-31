#!/usr/bin/env python
# test expression parsing

import os
import sys
import time
import unittest

from epics import ca

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
    
class CA_BasicTests(unittest.TestCase):
        
    def testA_CreateChid(self):
        sys.stdout.write('Simple Test: create chid\n')
        chid = ca.create_channel(pvnames.double_pv)
        self.assertNotEqual(chid,None)

    def test_Connect1(self):
        chid = ca.create_channel(pvnames.double_pv)
        conn,dt,n = _ca_connect(chid, timeout=2)
        sys.stdout.write( 'CA Connection Test1: connect to existing PV\n')
        sys.stdout.write( ' connected in %.4f sec\n' % (dt))
        self.assertEqual(conn,True)

    def test_Connected(self):
        pvn = pvnames.double_pv
        chid = ca.create_channel(pvn,connect=True)
        isconn = ca.isConnected(chid)
        sys.stdout.write( 'CA test Connected (%s) = %s\n' % (pvn,isconn))
        self.assertEqual(isconn,True)
        state= ca.state(chid)
        self.assertEqual(state,ca.dbr.CS_CONN)
        acc = ca.access(chid)
        self.assertEqual(acc,'read/write')


    def test_DoubleVal(self):
        pvn = pvnames.double_pv
        chid = ca.create_channel(pvn,connect=True)
        cdict  = ca.get_ctrlvars(chid)
        sys.stdout.write( 'CA testing CTRL Values for a Double (%s)\n'   % (pvn))
        self.failUnless('units' in cdict)
        self.failUnless('precision' in cdict)
        self.failUnless('severity' in cdict)
       
        hostname = ca.host_name(chid)
        self.failUnless(hostname.startswith(pvnames.double_pv_host))

        count = ca.element_count(chid)
        self.assertEqual(count,1)

        ftype= ca.field_type(chid)
        self.assertEqual(ftype,ca.dbr.DOUBLE)

        prec = ca.get_precision(chid)
        self.assertEqual(prec, pvnames.double_pv_prec)

        units= ca.get_ctrlvars(chid)['units']
        self.assertEqual(units, pvnames.double_pv_units)

    def test_UnConnected(self):
        sys.stdout.write( 'CA Connection Test1: connect to non-existing PV (2sec timeout)\n')
        chid = ca.create_channel('impossible_pvname_certain_to_fail')
        conn,dt,n = _ca_connect(chid, timeout=2)
        self.assertEqual(conn,False)


    def test_promote_type(self):
        pvn = pvnames.double_pv
        chid = ca.create_channel(pvn,connect=True)
        sys.stdout.write( 'CA promote type (%s)\n' % (pvn))
        f_t  = ca.promote_type(chid,use_time=True)
        f_c  = ca.promote_type(chid,use_ctrl=True)        
        self.assertEqual(f_t, ca.dbr.TIME_DOUBLE)
        self.assertEqual(f_c, ca.dbr.CTRL_DOUBLE)

    def test_Enum(self):
        pvn  = pvnames.enum_pv
        chid = ca.create_channel(pvn,connect=True)
        enumstrs = ca.get_enum_strings(chid)
        self.failUnless(len(enumstrs)>1)

        self.failUnless(isinstance(enumstrs[0],str))
        sys.stdout.write( 'CA EnumStrings (%s) = %s\n' % (pvn,repr(enumstrs)))
        self.failUnless(enumstrs,pvnames.enum_pv_strs)
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase( CA_BasicTests)
    unittest.TextTestRunner(verbosity=1).run(suite)


    

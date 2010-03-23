#!/usr/bin/env python
# test expression parsing

from __future__ import print_function
import os
import sys
import time
import unittest
sys.path.insert(0,'..')
from lib import ca

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
    pv_host       = 'ioc13ida.cars.aps.anl.gov:50'
    pvname_double = '13IDA:m1.VAL'
    pvname_broken = 'non-pv'
    pvname_enum   = '13IDA:m1.DIR'
    pvname_string = '13IDA:m1.DESC'
    
        
    def testA_CreateChid(self):
        print( 'Simple Test: create chid' )
        chid = ca.create_channel(self.pvname_double)
        self.assertNotEqual(chid,None)

    def test_Connect1(self):
        chid = ca.create_channel(self.pvname_double)
        conn,dt,n = _ca_connect(chid, timeout=2)
        print( 'CA Connection Test1: connect to existing PV',end='l')
        print( ' connected in %.4f sec' % (dt))
        self.assertEqual(conn,True)

    def test_Connect2(self):
        print( 'CA Connection Test1: connect to non-existing PV (2sec timeout)')
        chid = ca.create_channel(self.pvname_broken)
        conn,dt,n = _ca_connect(chid, timeout=2)
        self.assertEqual(conn,False)

    def test_GetHost(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        hostname = ca.host_name(chid)
        print( 'CA GetHost (%s) = %s' % (pvn,hostname))
        self.failUnless(hostname.startswith(self.pv_host))

    def test_GetElementCount(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        count = ca.element_count(chid)
        print( 'CA GetElementCount (%s) = %s' % (pvn,count))
        self.assertEqual(count,1)

    def test_GetFieldType(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        ftype= ca.field_type(chid)
        print( 'CA GetFieldType (%s) = %s' % (pvn,ftype))
        self.assertEqual(ftype,ca.dbr.DOUBLE)

    def test_isConnected(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        isconn = ca.isConnected(chid)
        print( 'CA isConnected (%s) = %s' % (pvn,isconn))
        self.assertEqual(isconn,True)
        
    def test_state(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        state= ca.state(chid)
        print( 'CA state (%s) = %s' % (pvn,state))
        self.assertEqual(state,ca.dbr.CS_CONN)

    def test_access(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        acc = ca.access(chid)
        print( 'CA access (%s) = %s' % (pvn,acc))
        self.assertEqual(acc,'read/write')

    def test_promote_type(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        print( 'CA promote type (%s)' % (pvn))
        f_t  = ca.promote_type(chid,use_time=True)
        f_c  = ca.promote_type(chid,use_ctrl=True)        
        self.assertEqual(f_t, ca.dbr.TIME_DOUBLE)
        self.assertEqual(f_c, ca.dbr.CTRL_DOUBLE)

    def test_get_ctrlvars(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn,connect=True)
        cdict  = ca.get_ctrlvars(chid)
        print( 'CA get_ctrlvars (%s)  %i members'   % (pvn,len(cdict)))
        self.failUnless('units' in cdict)
        self.failUnless('precision' in cdict)
        self.failUnless('severity' in cdict)
        
    def test_EnumStr(self):
        pvn  = self.pvname_enum
        chid = ca.create_channel(pvn,connect=True)
        enumstrs = ca.get_enum_strings(chid)
        self.failUnless(len(enumstrs)>1)
        self.failUnless(isinstance(enumstrs[0],str))
        print( 'CA EnumStrings (%s) = %s' % (pvn,repr(enumstrs)))
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase( CA_BasicTests)
    unittest.TextTestRunner(verbosity=1).run(suite)


    

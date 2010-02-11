#!/usr/bin/env python
# test expression parsing
from __future__ import print_function
import os
import sys
import time
import unittest
sys.path.insert(0,'..')

from lib import ca

import numpy

def _ca_connect(chid,timeout=5.0):
    n  = 0
    t0 = time.time()
    conn = 2==ca.state(chid)
    while (not conn) and (time.time()-t0 < timeout):
        ca.poll(1.e-6,1.e-4)
        conn = 2==ca.state(chid)
        n += 1
    return conn, time.time()-t0, n

    
class CAInitTest(unittest.TestCase):
    pv_host       = 'ioc13ida.cars.aps.anl.gov:50'
    pvname_double = '13IDA:m1.VAL'
    pvname_broken = 'foo'
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

    def test_Connect3(self):
        self.test_Connect1()

    def test_GetHost(self):
        pvn = self.pvname_double
        chid = ca.create_channel(pvn)
        conn,dt,n = _ca_connect(chid, timeout=2)
        hostname = ca.host_name(chid)
        print( 'CA GetHost (%s) = %s' % (pvn,hostname))
        self.failUnless(hostname.startswith(self.pv_host))

    def test_EnumStr(self):
        pvn  = self.pvname_enum
        chid = ca.create_channel(pvn)
        conn,dt,n = _ca_connect(chid, timeout=2)
        enumstrs = ca.get_enum_strings(chid)
        self.failUnless(len(enumstrs)>1)
        self.failUnless(isinstance(enumstrs[0],str))
        print( 'CA EnumStrings (%s) = %s' % (pvn,repr(enumstrs)))
        
        
if __name__ == '__main__':
    
    ca.initialize_libca(context=0)

    suite = unittest.TestLoader().loadTestsFromTestCase( CAInitTest)
    unittest.TextTestRunner(verbosity=1).run(suite)
    time.sleep(0.01)
    ca.poll(1.e-3,1.0)
    ca.shutdown()



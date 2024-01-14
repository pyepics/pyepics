#!/usr/bin/env python
# test expression parsing

import os
import sys
import time
import numpy
import ctypes
from contextlib import contextmanager
from epics import ca, dbr, caput
from epics.utils import IOENCODING

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


def test_CreateChid():
    write('Simple Test: create chid')
    chid = ca.create_channel(pvnames.double_pv)
    assert chid is not None

def test_GetNonExistentPV():
    write('Simple Test: get on a non-existent PV')
    chid = ca.create_channel('Definitely-Not-A-Real-PV')
    val = ca.get(chid)
    assert val is None

def test_CreateChid_CheckTypeCount():
    write('Simple Test: create chid, check count, type, host, and access')
    chid = ca.create_channel(pvnames.double_pv)
    ret = ca.connect_channel(chid)
    ca.pend_event(1.e-3)

    ftype  = ca.field_type(chid)
    count  = ca.element_count(chid)
    host    = ca.host_name(chid)
    rwacc = ca.access(chid)

    assert chid is not None
    assert host is not None
    assert count == 1
    assert ftype == 6
    assert rwacc == 'read/write'


def test_CreateChidWithConn():
    write('Simple Test: create chid with conn callback')
    chid = ca.create_channel(pvnames.int_pv,
                             callback=onConnect)
    val = ca.get(chid)
    global CONN_DAT
    conn = CONN_DAT.get(pvnames.int_pv, None)
    assert conn

def test_dbrName():
    write( 'DBR Type Check')
    assert dbr.Name(dbr.STRING) == 'STRING'
    assert dbr.Name(dbr.FLOAT) == 'FLOAT'
    assert dbr.Name(dbr.ENUM) == 'ENUM'
    assert dbr.Name(dbr.CTRL_CHAR) == 'CTRL_CHAR'
    assert dbr.Name(dbr.TIME_DOUBLE) == 'TIME_DOUBLE'
    assert dbr.Name(dbr.TIME_LONG) == 'TIME_LONG'

    assert dbr.Name('STRING', reverse=True) == dbr.STRING
    assert dbr.Name('DOUBLE', reverse=True) == dbr.DOUBLE
    assert dbr.Name('CTRL_ENUM', reverse=True) == dbr.CTRL_ENUM
    assert dbr.Name('TIME_LONG', reverse=True) == dbr.TIME_LONG

def test_Connect1():
    chid = ca.create_channel(pvnames.double_pv)
    conn,dt,n = _ca_connect(chid, timeout=2)
    write( 'CA Connection Test1: connect to existing PV')
    write( ' connected in %.4f sec' % (dt))
    assert conn

def test_Connected():
    pvn = pvnames.double_pv
    chid = ca.create_channel(pvn,connect=True)
    isconn = ca.isConnected(chid)
    write( 'CA test Connected (%s) = %s' % (pvn,isconn))
    assert isconn
    assert ca.state(chid) == ca.dbr.CS_CONN
    assert ca.access(chid) == 'read/write'

def test_DoubleVal():
    pvn = pvnames.double_pv
    chid = ca.create_channel(pvn,connect=True)
    cdict  = ca.get_ctrlvars(chid)
    write( 'CA testing CTRL Values for a Double (%s)'   % (pvn))
    assert 'units' in cdict
    assert 'precision' in cdict
    assert 'severity' in cdict

    assert len(ca.host_name(chid)) > 2
    assert ca.element_count(chid) == 1

    assert ca.field_type(chid) == ca.dbr.DOUBLE
    assert ca.get_precision(chid) == pvnames.double_pv_prec
    assert ca.get_ctrlvars(chid)['units'] == pvnames.double_pv_units
    assert ca.access(chid).startswith('read')

def test_UnConnected():
    write( 'CA Connection Test1: connect to non-existing PV (2sec timeout)')
    chid = ca.create_channel('impossible_pvname_certain_to_fail')
    conn, dt, n = _ca_connect(chid, timeout=2)
    assert not conn

def test_putwait():
    'test put with wait'
    pvn = pvnames.non_updating_pv
    chid = ca.create_channel(pvn, connect=True)
    o  = ca.put(chid, -1, wait=True)
    time.sleep(0.01)
    assert ca.get(chid) == -1

    ca.put(chid, 2, wait=True)
    assert ca.get(chid) == 2

def test_promote_type():
    pvn = pvnames.double_pv
    chid = ca.create_channel(pvn,connect=True)
    write( 'CA promote type (%s)' % (pvn))
    assert ca.promote_type(chid, use_time=True) == ca.dbr.TIME_DOUBLE
    assert ca.promote_type(chid, use_ctrl=True) == ca.dbr.CTRL_DOUBLE

def test_ProcPut():
    pvn  = pvnames.enum_pv
    chid = ca.create_channel(pvn, connect=True)
    write( 'CA test put to PROC Field (%s)' % (pvn))
    for input in (1, '1', 2, '2', 0, '0', 50, 1):
        ret = None
        try:
            ret = ca.put(chid, 1)
        except:
            pass
        assert ret is not None

def test_subscription_double():
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
    assert val is not None

def test_subscription_custom():
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
    assert change_count > 2

def test_subscription_str():
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
    assert CHANGE_DAT.get(pvn, None) is not None

def arrcallback(arrayname, array_type, length, element_type):
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
        assert val is not None
        assert type(val) == array_type
        assert len(val) == length
        assert type(val[0]) == element_type
        assert all(type(e)==element_type for e in val)
        results[form] = val
    return results

def test_subscription_long_array():
    """ Check that numeric arrays callbacks successfully send correct data """
    arrcallback(pvnames.long_arr_pv, numpy.ndarray, 2048, numpy.int32)

def test_subscription_double_array():
    """ Check that double arrays callbacks successfully send correct data """
    arrcallback(pvnames.double_arr_pv, numpy.ndarray, 2048, numpy.float64)

def test_subscription_string_array():
    """ Check that string array callbacks successfully send correct data """
    results = arrcallback(pvnames.string_arr_pv, list, 128, str)
    assert len(results["normal"][0]) > 0
    assert len(results["time"][0]) > 0
    assert len(results["ctrl"][0]) > 0

def test_subscription_char_array():
    """ Check that uchar array callbacks successfully send correct data as arrays """
    arrcallback(pvnames.char_arr_pv, numpy.ndarray, 128, numpy.uint8)

def test_Values():
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
        rlines = open('./caget.tst', 'r', encoding=IOENCODING).readlines()
        for line in rlines:
            pvn, sval = [i.strip() for i in line[:-1].split(' ', 1)]
            tval = str(vals[pvn])
            if pvn in (pvnames.float_pv,pvnames.double_pv):
                # use float precision!
                tval = "%.5f" % vals[pvn]
            assert tval == sval

def test_type_converions_1():
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
                assert cval == values[pvname]

def test_type_converions_2():
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
                    assert a == b


def test_Array0():
    write('Array Test: get double array as numpy array, ctypes Array, and list')
    chid = ca.create_channel(pvnames.double_arrays[0])
    aval = ca.get(chid)
    cval = ca.get(chid, as_numpy=False)

    assert isinstance(aval, numpy.ndarray)
    assert len(aval) > 2
    assert isinstance(cval, ctypes.Array)
    assert len(cval) > 2
    lval = list(cval)
    assert isinstance(lval, list)
    assert len(lval) > 2
    assert lval == list(aval)

def test_xArray1():
    write('Array Test: get(wait=False) / get_complete()')
    chid = ca.create_channel(pvnames.double_arrays[0])
    val0 = ca.get(chid)
    aval = ca.get(chid, wait=False)
    assert aval is  None
    val1 = ca.get_complete(chid)
    assert all(val0 == val1)

def test_xArray2():
    write('Array Test: get fewer than max vals using ca.get(count=0)')
    chid = ca.create_channel(pvnames.double_arrays[0])
    maxpts = ca.element_count(chid)
    npts = int(max(2, maxpts/2.3 - 1))
    write('max points is %s' % (maxpts, ))
    dat = numpy.random.normal(size=npts)
    write('setting array to a length of npts=%s' % (npts, ))
    ca.put(chid, dat)
    out1 = ca.get(chid)
    assert isinstance(out1, numpy.ndarray)
    assert len(out1) == npts
    out2 = ca.get(chid, count=0)
    assert isinstance(out2, numpy.ndarray)
    assert len(out2) == npts

def test_xArray3():
    write('Array Test: get char array as string')
    chid = ca.create_channel(pvnames.char_arrays[0])
    val = ca.get(chid)
    assert isinstance(val, numpy.ndarray)
    char_val = ca.get(chid, as_string=True)
    assert isinstance(char_val, str)
    conv = ''.join([chr(i) for i in val])
    assert conv == char_val

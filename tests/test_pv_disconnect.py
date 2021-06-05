#!/usr/bin/python

# test of simplest device
from epics import PV, get_pv, caget, camonitor, camonitor_clear

import os
import psutil
import time

import pvnames
mypv = pvnames.updating_pv1


def test_connect_disconnect():
    pv = PV(mypv, auto_monitor=True, callback=lambda **args: ...)

    pv.wait_for_connection()

    # check that PV is connected
    assert pv.connected is True

    # check that data is received
    value = pv.get()
    assert value is not None

    pv.disconnect()

    # check that PV is disconnected
    assert pv.connected is False

    # check that no data is received after disconnect
    value = pv.get()
    assert value is None


def test_reconnect():
    # connect and disconnect
    pv = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
    pv.wait_for_connection()
    pv.disconnect()

    # try to reconnect to the same PV
    connected = pv.reconnect()

    # check that PV is connected
    assert connected is True

    # check that data is received
    value = pv.get()
    assert value is not None


def test_with_two_PVs():
    # create 2 PV objects connecting to the same PV signal
    pv1 = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
    pv2 = PV(mypv, auto_monitor=True, callback=lambda **args: ...)

    pv1.wait_for_connection()
    pv2.wait_for_connection()

    # check that both PVs are connected
    assert pv1.connected is True
    assert pv2.connected is True

    # check that data is received
    assert pv1.get() is not None
    assert pv2.get() is not None

    # disconnect 1 PV
    pv1.disconnect()

    # check that the first PV is disconnected and doesn't receive data
    assert pv1.connected is False
    assert pv1.get() is None

    # check that the other PV is connected and still receives data
    assert pv2.connected is True
    assert pv2.get() is not None


def test_with_PV_and_getPV():
    # create 2 PV objects connecting to the same PV signal, one using PV class and the other one using get_pv()
    pv1 = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
    pv2 = get_pv(mypv)

    pv1.wait_for_connection()
    pv2.wait_for_connection()

    # check that both PVs are connected
    assert pv1.connected is True
    assert pv2.connected is True

    # check that data is received
    assert pv1.get() is not None
    assert pv2.get() is not None

    # disconnect 1 PV
    pv1.disconnect()

    time.sleep(1)

    # check that the first PV is disconnected and doesn't receive data
    assert pv1.connected is False
    assert pv1.get() is None

    # check that the other PV is connected and still receives data
    assert pv2.connected is True
    assert pv2.get() is not None


def test_with_getPV():
    # create 2 PV objects connecting to the same PV signal using get_pv()
    pv1 = get_pv(mypv)
    pv2 = get_pv(mypv)

    pv1.wait_for_connection()
    pv2.wait_for_connection()

    # check that both PVs are connected
    assert pv1.connected is True
    assert pv2.connected is True

    # check that data is received
    assert pv1.get() is not None
    assert pv2.get() is not None

    # disconnect 1 PV
    pv1.disconnect()

    time.sleep(1)

    # check that the first PV is disconnected and doesn't receive data
    assert pv1.connected is False
    assert pv1.get() is None

    # check that the other PV is also disconnected and doesn't receive data either
    assert pv2.connected is False
    assert pv2.get() is None


def test_with_caget():
    pv = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
    pv.wait_for_connection()

    # check that the PV is connected and  data is received
    assert pv.connected is True
    assert pv.get() is not None

    # use caget to get data from the same PV
    assert caget(mypv) is not None

    # disconnect PV object
    pv.disconnect()

    # check that the PV is disconnected and doesn't receive data
    assert pv.connected is False
    assert pv.get() is None

    # check that you can still use caget to get data from the same PV
    assert caget(mypv) is not None


def test_with_caget_nomonitor():
    pv = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
    pv.wait_for_connection()

    # check that the PV is connected and  data is received
    assert pv.connected is True
    assert pv.get() is not None

    # use caget to get data from the same PV
    assert caget(mypv, use_monitor=False) is not None

    # disconnect PV object
    pv.disconnect()

    # check that the PV is disconnected and doesn't receive data
    assert pv.connected is False
    assert pv.get() is None

    # check that you can still use caget to get data from the same PV
    assert caget(mypv, use_monitor=False) is not None


def test_with_camonitor():
    pv = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
    pv.wait_for_connection()

    # check that the PV is connected and  data is received
    assert pv.connected is True
    assert pv.get() is not None

    # use camonitor
    received = {'flag': False}

    def callback(**args):
        received['flag'] = True
    camonitor(mypv, callback=callback)
    time.sleep(1)

    # check that the monitor receives data
    assert received['flag'] is True

    # disconnect PV object
    pv.disconnect()
    time.sleep(1)

    # check that the PV is disconnected and doesn't receive data
    assert pv.connected is False
    assert pv.get() is None

    # reset the flag to check that new data is received by camonitor
    received['flag'] = False
    time.sleep(1)
    assert received['flag'] is True

    # clear the monitor
    camonitor_clear(mypv)
    time.sleep(1)

    # reset the flag to check that no new data is received by camonitor
    received['flag'] = False
    time.sleep(1)
    assert received['flag'] is False


def test_memleak_disconnect():
    # try to connect multiple times to the same PV
    mem = []
    for i in range(int(2)):
        for j in range(int(1000)):
            pv = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
            pv.disconnect()

        process = psutil.Process(os.getpid())
        mem.append(process.memory_info().rss)

    # check used memory by the process didn't increase by more than 1%
    assert mem[1]/mem[0] < 1.01

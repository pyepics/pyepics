#!/usr/bin/python

# test of simplest device
from epics import PV

import os
import psutil
import pytest

import pvnames
mypv = pvnames.updating_pv1


def test_connect_disconnect():
    pv = PV(mypv, auto_monitor=True, callback=lambda **args: ...)

    pv.wait_for_connection()

    # check that PV is connected
    assert pv.connect() is True

    # check that data is received
    value = pv.get()
    assert value is not None

    pv.disconnect()

    # check that PV is disconnected
    assert pv.connect() is False

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


def test_connect_disconnect_with_two_PVs():
    # create 2 PV objects connecting to the same PV signal
    pv1 = PV(mypv, auto_monitor=True, callback=lambda **args: ...)
    pv2 = PV(mypv, auto_monitor=True, callback=lambda **args: ...)

    pv1.wait_for_connection()
    pv2.wait_for_connection()

    # check that both PVs are connected
    assert pv1.connect() is True
    assert pv2.connect() is True

    # check that data is received
    assert pv1.get() is not None
    assert pv2.get() is not None

    # disconnect 1 PV
    pv1.disconnect()

    # check that the first PV is disconnected and doesn't receive data
    assert pv1.connect() is False
    assert pv1.get() is None

    # check that the other PV is connected and still receives data
    assert pv2.connect() is True
    assert pv2.get() is not None


@pytest.mark.skip(reason="disabled until memleak is fixed")
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

#!/usr/bin/python

# test of simplest device
from epics import PV

import os
import psutil
import pytest

import pvnames
mypv = pvnames.updating_pv1


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

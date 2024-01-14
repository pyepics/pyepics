#!/usr/bin/python

# test of simplest device

from epics.devices import ao
import sys
import time
from epics.utils import IOENCODING

def test_aodevice():
    myao = ao('PyTest:ao1')
    assert len(myao._pvs) > 10
    assert myao.VAL is not None
    myao.write_state('tmp_aostate.txt')

    time.sleep(0.5)
    flines = []
    with open('tmp_aostate.txt', encoding=IOENCODING) as fh:
        flines.extend( fh.readlines())
    assert len(flines) > 10

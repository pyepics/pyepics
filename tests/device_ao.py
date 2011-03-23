#!/usr/bin/python

# test of simplest device

from epics.devices import ao
import sys
import time

myao = ao('Py:ao1')


if len(myao._pvs) < 10:
    print(" Not enough PVS!!")
    sys.exit()

if myao.VAL is None:
    print(" Value is None!!")
    sys.exit()


myao.write_state('tmp_aostate.txt')

time.sleep(0.5)

flines = open('tmp_aostate.txt').readlines()
if len(flines) < 10:
    print(" write_state didn't work properly")
    sys.exit()

print(" all tests passed!")



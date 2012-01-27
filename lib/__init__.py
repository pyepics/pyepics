"""
   epics channel access python module

   version    :  3.2.0
   last update:  19-Jan-2012

   Principle Authors:
      Matthew Newville <newville@cars.uchicago.edu>, CARS, University of Chicago
      Angus Gratton <angus.gratton@anu.edu.au>, Australian National University

== License:
   Except where explicitly noted, this file and all files in this
   distribution are licensed under the Epics Open License
   See license.txt in the top-level directory of this distribution.

== Overview:
   Python Interface to the Epics Channel Access protocol of the Epics control system.

"""

__version__ = '3.2.0'

import time
import sys
from . import ca
from . import dbr
from . import pv
from . import alarm
from . import device
from . import motor

PV    = pv.PV
Alarm = alarm.Alarm
Motor = motor.Motor
Device = device.Device
poll  = ca.poll

# some constants
NO_ALARM = 0
MINOR_ALARM = 1
MAJOR_ALARM = 2
INVALID_ALARM = 3

# compatibility with other CA libraries
# from  .compat import epicsPV

# a local cache for PVs used in caget/caput/cainfo/camonitor functions
_CACHE_ = {}
# a local cache for Monitored PVs
_MONITORS_ = {}

def __create_pv(pvname, timeout=5.0):
    "create PV, wait for connection: "
    if pvname in _CACHE_:
        return _CACHE_[pvname]

    start_time = time.time()
    thispv = PV(pvname)
    thispv.connect()
    while not thispv.connected:
        poll()
        if time.time()-start_time > timeout:
            break
    if not thispv.connected:
        ca.write('cannot connect to %s' % pvname)
        return None
    # save this one for next time
    _CACHE_[pvname] = thispv
    return thispv

def caput(pvname, value, wait=False, timeout=60):
    """caput(pvname, value, wait=False, timeout=60)
    simple put to a pv's value.
       >>> caput('xx.VAL',3.0)

    to wait for pv to complete processing, use 'wait=True':
       >>> caput('xx.VAL',3.0,wait=True)
    """
    thispv = __create_pv(pvname)
    if thispv is not None:
        return thispv.put(value, wait=wait, timeout=timeout)

def caget(pvname, as_string=False, count=None, as_numpy=True,
          use_monitor=False, timeout=None):
    """caget(pvname, as_string=False)
    simple get of a pv's value..
       >>> x = caget('xx.VAL')

    to get the character string representation (formatted double,
    enum string, etc):
       >>> x = caget('xx.VAL', as_string=True)

    to get a truncated amount of data from an array, you can specify
    the count with
       >>> x = caget('MyArray.VAL', count=1000)
    """
    thispv = __create_pv(pvname)
    if thispv is not None:
        if as_string:
            thispv.get_ctrlvars()
        val = thispv.get(count=count, timeout=timeout,
                         use_monitor=use_monitor,
                         as_string=as_string,
                         as_numpy=as_numpy)
        poll()
        return val

def cainfo(pvname, print_out=True):
    """cainfo(pvname,print_out=True)

    return printable information about pv
       >>>cainfo('xx.VAL')

    will return a status report for the pv.

    If print_out=False, the status report will be printed,
    and not returned.
    """
    thispv = __create_pv(pvname)
    if thispv is not None:
        thispv.get()
        thispv.get_ctrlvars()
        if print_out:
            ca.write(thispv.info)
        else:
            return thispv.info

def camonitor_clear(pvname):
    """clear a monitor on a PV"""
    if pvname in _MONITORS_:
        if isinstance(_MONITORS_[pvname], PV):
            _MONITORS_[pvname].clear_callbacks()
        _MONITORS_.pop(pvname)

def camonitor(pvname, writer=None, callback=None):
    """ camonitor(pvname, writer=None, callback=None)

    sets a monitor on a PV.
       >>>camonitor('xx.VAL')

    This will write a message with the latest value for that PV each
    time the value changes and when ca.poll() is called.

    To write the result to a file, provide the writer option a write method
    to an open file or some other method that accepts a string.

    To completely control where the output goes, provide a callback method
    and you can do whatever you'd like with them.

    Your callback will be sent keyword arguments for pvname, value, and
    char_value Important: use **kwd!!
    """

    if writer is None:
        writer = ca.write
    if callback is None:
        def callback(pvname=None, value=None, char_value=None, **kwds):
            "generic monitor callback"
            if char_value is None:
                char_value = repr(value)
            writer("%.32s %s %s" % (pvname, pv.fmt_time(), char_value))

    thispv = __create_pv(pvname)
    if thispv is not None:
        thispv.get()
        thispv.add_callback(callback, with_ctrlvars=True)
        _MONITORS_[pvname] = thispv

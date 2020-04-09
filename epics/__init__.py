from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

__doc__ = """
   epics channel access python module

   version: %s
   Principal Authors:
      Matthew Newville <newville@cars.uchicago.edu> CARS, University of Chicago
      Angus Gratton <angus.gratton@anu.edu.au>, Australian National University

== License:

   Except where explicitly noted, this file and all files in this
   distribution are licensed under the Epics Open License See license.txt in
   the top-level directory of this distribution.

== Overview:
   Python Interface to the Epics Channel Access
   protocol of the Epics control system.

""" % (__version__)


import time
import sys
import threading
from . import ca
from . import dbr
from . import pv
from . import alarm
from . import device
from . import motor
from . import multiproc

PV    = pv.PV
Alarm = alarm.Alarm
Motor = motor.Motor
Device = device.Device
poll  = ca.poll

get_pv = pv.get_pv

CAProcess = multiproc.CAProcess
CAPool = multiproc.CAPool

# some constants
NO_ALARM = 0
MINOR_ALARM = 1
MAJOR_ALARM = 2
INVALID_ALARM = 3

_PVmonitors_ = {}

def caput(pvname, value, wait=False, timeout=60):
    """caput(pvname, value, wait=False, timeout=60)
    simple put to a pv's value.
       >>> caput('xx.VAL',3.0)

    to wait for pv to complete processing, use 'wait=True':
       >>> caput('xx.VAL',3.0,wait=True)
    """
    start_time = time.time()
    thispv = get_pv(pvname, timeout=timeout, connect=True)
    if thispv.connected:
        timeout -= (time.time() - start_time)
        return thispv.put(value, wait=wait, timeout=timeout)

def caget(pvname, as_string=False, count=None, as_numpy=True,
          use_monitor=False, timeout=5.0):
    """caget(pvname, as_string=False,count=None,as_numpy=True,
             use_monitor=False,timeout=5.0)
    simple get of a pv's value..
       >>> x = caget('xx.VAL')

    to get the character string representation (formatted double,
    enum string, etc):
       >>> x = caget('xx.VAL', as_string=True)

    to get a truncated amount of data from an array, you can specify
    the count with
       >>> x = caget('MyArray.VAL', count=1000)
    """
    start_time = time.time()
    thispv = get_pv(pvname, timeout=timeout, connect=True)
    if thispv.connected:
        if as_string:
            thispv.get_ctrlvars()
        timeout -= (time.time() - start_time)
        val = thispv.get(count=count, timeout=timeout,
                         use_monitor=use_monitor,
                         as_string=as_string,
                         as_numpy=as_numpy)
        poll()
        return val

def cainfo(pvname, print_out=True, timeout=5.0):
    """cainfo(pvname,print_out=True,timeout=5.0)

    return printable information about pv
       >>>cainfo('xx.VAL')

    will return a status report for the pv.

    If print_out=False, the status report will be printed,
    and not returned.
    """
    start_time = time.time()
    thispv = get_pv(pvname, timeout=timeout, connect=True)
    if thispv.connected:
        conn_time = time.time() - start_time
        thispv.get(timeout=timeout-conn_time)
        get_time = time.time() - start_time
        thispv.get_ctrlvars(timeout=timeout-get_time)
        if print_out:
            ca.write(thispv.info)
        else:
            return thispv.info

def camonitor_clear(pvname):
    """clear a monitor on a PV"""
    if pvname in _PVmonitors_:
        _PVmonitors_[pvname].remove_callback(index=-999)
        _PVmonitors_.pop(pvname)

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

    thispv = get_pv(pvname, connect=True)
    if thispv.connected:
        thispv.get()
        thispv.add_callback(callback, index=-999, with_ctrlvars=True)
        _PVmonitors_[pvname] = thispv

def caget_many(pvlist, as_string=False, as_numpy=True, count=None,
               timeout=1.0, conn_timeout=1.0):
    """get values for a list of PVs, working as fast as possible

    Arguments
    ---------
     pvlist (list):        list of pv names to fetch
     as_string (bool):     whether to get values as strings [False]
     as_numpy (bool):      whether to get values as numpy arrys [True]
     count  (int or None): max number of elements to get [None]
     timeout (float):      timeout on *each* get()  [1.0]
     conn_timeout (float): timeout for *all* pvs to connect [1.0]

    Returns
    --------
      list of values, with `None` signifying 'not connected' or 'timed out'.

    Notes
    ------
       this does not cache PV objects.

    """
    chids, connected, out = [], [], []
    for name in pvlist:
        chids.append(ca.create_channel(name, auto_cb=False, connect=False))

    all_connected = False
    expire_time = time.time() + timeout
    while (not all_connected and (time.time() < expire_time)):
        connected = [dbr.CS_CONN==ca.state(chid) for chid in chids]
        all_connected = all(connected)
        poll()

    for (chid, conn) in zip(chids, connected):
        if conn:
            ca.get(chid, count=count, as_string=as_string, as_numpy=as_numpy,
                   wait=False)

    poll()
    for (chid, conn) in zip(chids, connected):
        val = None
        if conn:
            val = ca.get_complete(chid, count=count, as_string=as_string,
                                  as_numpy=as_numpy, timeout=timeout)
        out.append(val)
    return out

def caput_many(pvlist, values, wait=False, connection_timeout=None, put_timeout=60):
    """put values to a list of PVs, as fast as possible
    This does not maintain the PV objects it makes.  If
    wait is 'each', *each* put operation will block until
    it is complete or until the put_timeout duration expires.
    If wait is 'all', this method will block until *all*
    put operations are complete, or until the put_timeout
    duration expires.
    Note that the behavior of 'wait' only applies to the
    put timeout, not the connection timeout.
    Returns a list of integers for each PV, 1 if the put
    was successful, or a negative number if the timeout
    was exceeded.
    """
    if len(pvlist) != len(values):
        raise ValueError("List of PV names must be equal to list of values.")
    out = []
    pvs = [PV(name, auto_monitor=False, connection_timeout=connection_timeout) for name in pvlist]
    conns = [p.connected for p in pvs]
    wait_all = (wait == 'all')
    wait_each = (wait == 'each')
    for p, v in zip(pvs, values):
        out.append(p.put(v, wait=wait_each, timeout=put_timeout, use_complete=wait_all))
    if wait_all:
        start_time = time.time()
        while not all([(p.connected and p.put_complete) for p in pvs]):
            ca.poll()
            elapsed_time = time.time() - start_time
            if elapsed_time > put_timeout:
                break
        return [1 if (p.connected and p.put_complete) else -1 for p in pvs]
    else:
        return [o if o == 1 else -1 for o in out]

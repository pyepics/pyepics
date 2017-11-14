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
    thispv = get_pv(pvname, connect=True)
    if thispv.connected:
        return thispv.put(value, wait=wait, timeout=timeout)

def caget(pvname, as_string=False, count=None, as_numpy=True,
          use_monitor=False, timeout=5.0):
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

def cainfo(pvname, print_out=True):
    """cainfo(pvname,print_out=True)

    return printable information about pv
       >>>cainfo('xx.VAL')

    will return a status report for the pv.

    If print_out=False, the status report will be printed,
    and not returned.
    """
    thispv = get_pv(pvname, connect=True)
    if thispv.connected:
        thispv.get()
        thispv.get_ctrlvars()
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

def caget_many(pvlist, as_string=False, count=None, as_numpy=True, timeout=5.0):
    """get values for a list of PVs
    This does not maintain PV objects, and works as fast
    as possible to fetch many values.
    """
    chids, out = [], []
    for name in pvlist: chids.append(ca.create_channel(name,
                                                       auto_cb=False,
                                                       connect=False))
    for chid in chids: ca.connect_channel(chid)
    for chid in chids: ca.get(chid, count=count, as_string=as_string, as_numpy=as_numpy, wait=False)
    for chid in chids: out.append(ca.get_complete(chid, 
                                                  count=count, 
                                                  as_string=as_string, 
                                                  as_numpy=as_numpy, 
                                                  timeout=timeout))
    return out

def caput_many(pvlist, values, wait=False, connection_timeout=None, put_timeout=60):
    """put values to a list of PVs
    This does not maintain PV objects.  If wait is 'each',
    *each* put operation will block until it is complete.
    or until the put_timeout duration expires.
    If wait is 'all', this method will block until *all*
    put operations are complete, or until the put_timeout
    duration expires.
    Note that the behavior of 'wait' only applies to the
    put timeout, not the connection timeout.
    Returns a list of integers for each PV, 1 if the put
    was successful, or a negative number if the timeout
    was exceeded.
    """
    chids, conns = [], []
    for name in pvlist: chids.append(ca.create_channel(name,
                                                       auto_cb=False,
                                                       connect=False))
    for chid in chids: conns.append(ca.connect_channel(chid,
                                                       timeout=connection_timeout))
    #Number of put requests awaiting completion. Only used if wait=='all'.
    #Reminder: acquire 'all_done' (defined further down) 
    #before using unfinished.
    unfinished = len([conn for conn in conns if conn > 0])
    #mutex is used to coordinate access to 'unfinished'.
    mutex = threading.Lock()
    #Notify all_done if there are no remaining puts to complete.
    #This function will block until all_done is notified, or
    #the put_timeout expires.
    all_done  = threading.Condition(mutex)
    t0 = time.time()
    wait_for_each = (wait == "each")
    wait_for_all = (wait == "all")
    #'out' is a list of return statuses for each put request.  1 if success, -1 if fail.
    #'out' is filled with fail to begin with.
    out = [-1 for i in range(0,len(chids))]
    #To get around the fact that you can't *assign* to variables while
    #in put_complete_callback's scope, but you can modify them.
    put_context = {"unfinished": unfinished, "all_done": all_done, "status": out}
    def put_complete_callback(data=None, **kws):
        #put_complete_callback is used in wait_all mode.
        put_context["all_done"].acquire()
        remaining = put_context["unfinished"] - 1
        put_context["status"][data] = 1
        if remaining <= 0:
            #We're all done!
            #Notify the main thread to stop waiting for puts to complete.
            put_context["all_done"].notify_all()
        put_context["unfinished"] = remaining
        put_context["all_done"].release()
    for (i, chid) in enumerate(chids):
        if conns[i]:
            if wait_for_all:
                ca.put(chid, values[i], callback=put_complete_callback, callback_data=i)
            else:
                #If we are waiting for each, or not waiting for anything, don't bother
                #with callbacks.
                out[i] = ca.put(chid, values[i], wait=wait_for_each, timeout=put_timeout)
    if not wait_for_all:
        return out
    #All put requests have been submitted, now we wait...
    with all_done:
        while put_context["unfinished"] > 0:
            elapsed_time = time.time() - t0
            remaining_time = put_timeout - elapsed_time
            if remaining_time <= 0.0:
                #Timeout expired, return the status of the puts.
                return out
            all_done.wait(remaining_time)
    #If you get this far, all puts completed successfully within the timeout.
    return out


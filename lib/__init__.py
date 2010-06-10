"""
   epics python module
   Matthew Newville <newville@cars.uchicago.edu>
   CARS, University of Chicago

   version    :  3.0.6 
   last update:  10-Jun-2010
   
== License:
   Except where explicitly noted, this file and all files in this
   distribution are licensed under the Epics Open License
   See license.txt in the top-level directory of this distribution.
   
== Overview:
   rewrite of EpicsCA v 2.*, with major goals of:
      a) replacing swig interface with ctypes
      b) better support for thread safety
      c) more complete low-level support to epics channel access interface
      
   major classes will be:
      PV -- Process Variable which will work largely as in EpicsCA 2.*
"""

__version__ = '3.0.6'

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
sleep = time.sleep # should probably remove this!

def __createPV(pvname, timeout=5.0):
    "create PV, wait for connection: "
    start_time = time.time()
    thispv = PV(pvname)
    thispv.connect()
    while not thispv.connected:
        time.sleep(1.e-4)
        ca.poll()
        if time.time()-start_time > timeout:
            break
    if not thispv.connected:
        sys.stdout.write('cannot connect to %s\n' % pvname)
        return None
    return thispv

def caput(pvname, value, wait=False, timeout=60):
    """caput(pvname, value, wait=False, timeout=60)
    simple put to a pv's value.
       >>> caput('xx.VAL',3.0)

    to wait for pv to complete processing, use 'wait=True':
       >>> caput('xx.VAL',3.0,wait=True)
    """ 
    thispv = __createPV(pvname)
    if thispv is not None:
        ret = thispv.put(value, wait=wait, timeout=timeout)
        ca.poll()
        return ret

def caget(pvname, as_string=False):
    """caget(pvname, as_string=False)
    simple get of a pv's value..
       >>> x = caget('xx.VAL')

    to get the character string representation (formatted double,
    enum string, etc):
       >>> x = caget('xx.VAL', as_string=True)
    """
    thispv = __createPV(pvname)
    if thispv is not None:
        val = thispv.get()
        thispv.get_ctrlvars()
        ca.poll()
        if as_string:
            return thispv.char_value
        return val

def cainfo(pvname, print_out=True):
    """cainfo(pvname,print_out=True)

    return printable information about pv
       >>>cainfo('xx.VAL')

    will return a status report for the pv.

    If print_out=False, the status report will be printed,
    and not returned.
    """
    thispv = __createPV(pvname)
    if thispv is not None:
        thispv.get()
        thispv.get_ctrlvars()
        if print_out:
            sys.stdout.write("%s\n" % thispv.info)
        else:     
            return thispv.info

_monitor_cache = {}
def camonitor_clear(pvname):
    """clear a monitor on a PV"""
    if pvname in _monitor_cache:
        _monitor_cache[pvname].clear_callbacks()
        
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
        writer = sys.stdout.write
    if callback is None:
        def callback(pvname=None, value=None, char_value=None, **kwd):
            "generic monitor callback"
            if char_value is None:
                char_value = repr(value)
            writer("%.32s %s %s\n" % (pvname, pv.fmt_time(), char_value))
        
    thispv = __createPV(pvname)
    _monitor_cache[pvname] = thispv
    if thispv is not None:
        thispv.get()
        thispv.add_callback(callback)



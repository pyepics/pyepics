"""
   epics python module
   Matthew Newville <newville@cars.uchicago.edu>
   CARS, University of Chicago

   version    :  3.0.1 (beta version of epics Py3)
   last update:  20-Feb-2010
         
== Overview:
   rewrite of EpicsCA v 2.*, with major goals of:
      a) replacing swig interface with ctypes
      b) better support for thread safety
      c) more complete low-level support to epics channel access interface
      
   major classes will be:
      PV -- Process Variable which will work largely as in EpicsCA 2.*
"""


__version__ = '3.0.1'

import time
import sys
import ca
import dbr
import pv
import alarm
import motor
import device
PV    = pv.PV
Alarm = alarm.Alarm
Motor = motor.Motor
Device = device.Device
poll  = ca.poll
sleep = time.sleep

__cache = {}

def __createPV(pvname,timeout=5.0):
    "create PV, wait for connection: "

    t0 = time.time()
    if pvname in __cache: return __cache[pvname]
    thispv = PV(pvname)
    if not thispv.connected:
        thispv.connect()
    while not thispv.connected:
        time.sleep(0.001)
        ca.poll()
        if time.time()-t0 > timeout: break
    if not thispv.connected:
        print 'cannot connect to %s' % pvname
        return None
    __cache[pvname] = thispv
    return thispv

def caput(pvname, value, wait=False, timeout=60):
    """caput(pvname, value, wait=False, timeout=60)
    simple put to a pv's value.
       >>> caput('xx.VAL',3.0)

    to wait for pv to complete processing, use 'wait=True':
       >>> caput('xx.VAL',3.0,wait=True)
    """ 
    pv = __createPV(pvname)
    if pv is not None:
        ret = pv.put(value,wait=wait,timeout=timeout)
        ca.poll()
        return ret

def caget(pvname, as_string=False):
    """caget(pvname, as_string=False)
    simple get of a pv's value..
       >>> x = caget('xx.VAL')

    to get the character string representation (formatted double, enum string, etc):
       >>> x = caget('xx.VAL', as_string=True)
    """
    pv = __createPV(pvname)
    if pv is not None:
        val = pv.get()
        ca.poll()
        if as_string: return pv.char_value
        return val

def cainfo(pvname,print_out=False):
    """cainfo(pvname,print_out=False)

    return printable information about pv
       >>>cainfo('xx.VAL')

    will return a status report for the pv.

    If print_out=True, the status report will be printed,
    and not returned.
    """
    pv = __createPV(pvname)
    if pv is not None:
        pv.get()
        pv.get_ctrlvars()
        if print_out:
            print pv.info
        else:     
            return pv.info

def camonitor_clear(pvname):
    """clear a monitor on a PV"""
    if pvname in __cache:
        __cache[pvname].clear_callbacks()
        
def camonitor(pvname,writer=None, callback=None):
    """ camonitor(pvname, writer=None, callback=None)

    sets a monitor on a PV.  
       >>>camonitor('xx.VAL')

    This will print out a message with the latest value for that PV
    each time the value changes and when ca.poll() is called.

    To write the result to a file, provide the writer option a write
    method to an open file or some other method that accepts a string.

    To completely control where the output goes, provide a callback
    method -- this will be sent the pvname, value, and char_value
    (as keyword arguments!) and you can do whatever you'd like with them.
    """

    if not callable(callback):
        if writer is None:
            writer = sys.stdout.write
        def callback(pvname=pvname, value=value,
                     char_value=char_value):
            writer("%.32s %s %s" % (pvname,pv.fmt_time(),char_value))
        
    def __cb(pvname=pvname,value=value,char_value=char_value,**kw):
        callback(pvname=pvname,value=value,char_value=char_value)
    
    pv = __createPV(pvname)
    if pv is not None:
        pv.get()
        pv.add_callback(__cb)

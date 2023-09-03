import time
from . import ca, dbr, pv, alarm, autosave, device, motor, multiproc
from .version import __version__

__doc__ = f"""
   Epics Channel Access Python module

   version: {__version__}
   Principal Authors:
      Matthew Newville <newville@cars.uchicago.edu> CARS, University of Chicago
      Ken Lauer, David Chabot, Angus Gratton

== License:
   Except where explicitly noted, this file and all files in this distribution
   are licensed under the Epics Open License See LICENSE in the top-level
   directory of this distribution.

== Overview:
   Python Interface to the Epics Channel Access protocol of the Epics control system.
"""

PV = pv.PV
Alarm = alarm.Alarm
Motor = motor.Motor
Device = device.Device
poll = ca.poll

get_pv = pv.get_pv

CAProcess = multiproc.CAProcess
CAPool = multiproc.CAPool

# some constants
NO_ALARM = 0
MINOR_ALARM = 1
MAJOR_ALARM = 2
INVALID_ALARM = 3

_PVmonitors_ = {}

def caput(pvname, value, wait=False, timeout=60.0, connection_timeout=5.0):
    """caput(pvname, value, wait=False, timeout=60, connection_timeout=5.0)

    put a value to an epics Process Variable (PV).

    Arguments
    ---------
     pvname (str):   name of PV
     value (any):    value to put to PV (see notes)
     wait (bool):    whether to wait for processing to complete [False]
     timeout (float):  maximum time to wait for the processing to complete [60]
     connection_timeout (float): maximum time to wait for connection [5]

    Returns
    --------
      1  on succesful completion
      -1 or other negative value on failure of the low-level CA put.
      None  on a failure to connect to the PV.

    Notes
    ------
      1. Epics PVs are typically limited to an appropriate Epics data type,
         int, float, str, and enums or homogeneously typed lists or arrays.
         Numpy arrays or Python strings are generally coeced as appropriate,
         but care may be needed when mapping Python objects to Epics PV values.
      2. If not already connected, the PV will first attempt to connect to
         the networked variable. As the initial connection can take some time
         (typically 30 msec or so), if a successful connection is made, a rich
         PV object with will be stored internally for later use.  Use
         connection_timeout to control how long to wait before declaring that
         the PV cannot be connected (mispelled name, inactive IOC, improper
         network configuration)
      3. Since some PVs can take a long time to process (perhaps physically
         moving a motor or telling a detector to collect and not return until
         done), it is impossible to tell what a "reasonable" timeout for a put
         should be.
      4. All time in seconds.

    Examples
    ---------
       to put a value to a PV and return as soon as possible:
       >>> caput('xx.VAL', 3.0)

      to wait for processing to finish, use 'wait=True':
      >>> caput('xx.VAL', 3.0, wait=True)

    """
    start_time = time.time()
    thispv = get_pv(pvname, timeout=connection_timeout, connect=True)
    out = None
    if thispv.connected:
        timeout -= time.time() - start_time
        out = thispv.put(value, wait=wait, timeout=timeout)
    return out


def caget(pvname, as_string=False, count=None, as_numpy=True,
          use_monitor=True, timeout=5.0, connection_timeout=5.0):
    """caget(pvname, as_string=False, count=None, as_numpy=True,
             use_monitor=True, timeout=5.0, connection_timeout=5.0)

    get the current value to an epics Process Variable (PV).

    Arguments
    ---------
     pvname (str):   name of PV
     as_string (bool): whether to get the string representation [False]
     count (int or None): maximum number of elements of array values [None]
     use_monitor (bool): whether to use the value cached by the monitor [True]
     timeout (float):  maximum time to wait for the processing to complete [60]
     connection_timeout (float): maximum time to wait for connection [5]

    Returns
    --------
      the PV value on success, or `None`on a failure.

    Notes
    ------
      1. If not already connected, the PV will first attempt to connect to
         the networked variable. As the initial connection can take some time
         (typically 30 msec or so), if a successful connection is made, a rich
         PV object with will be stored internally for later use.
      2. as_string=True will return a string: float values will formatted
         according to the PVs precision, enum values will return the approriate
         enum string, etc.
      3. count can be used to limit the number of elements fetched for array PVs.
      4. `use_monitor=False` will return the most recently cached value from the
         internal monitor placed on the PV. This will be the latest value unless
         the value is changing very rapidly. `use_monitor=False` will ignore the
         cached value and ask for an explicit value.  Of course, if a PV is
         changing rapidly enough for that to make a difference, it may also
         change between getting the value and downstream code using it.
      5. All time values are in seconds.


    Examples
    ---------
       get of a PV's value
       >>> x = caget('xx.VAL')

       to get the character string representation (formatted double,
       enum string, etc):
       >>> x = caget('xx.VAL', as_string=True)

       to get a truncated amount of data from an array, you can specify
       the count with
       >>> x = caget('MyArray.VAL', count=1000)
    """
    start_time = time.time()
    thispv = get_pv(pvname, timeout=connection_timeout, connect=True)
    val = None
    if thispv.connected:
        if as_string:
            thispv.get_ctrlvars()
        timeout -= time.time() - start_time
        val = thispv.get(count=count, timeout=timeout,
                         use_monitor=use_monitor,
                         as_string=as_string,
                         as_numpy=as_numpy)
        poll()
    return val

def cainfo(pvname, print_out=True, timeout=5.0, connection_timeout=5.0):
    """cainfo(pvname,print_out=True,timeout=5.0, connection_timeout=5.0)

    return printable information about PV

    Arguments
    ---------
     pvname (str):   name of PV
     print_out (bool): whether to print the info to standard out [True]
     timeout (float):  maximum time to wait for the processing to complete [60]
     connection_timeout (float): maximum time to wait for connection [5]

    Returns
    --------
       if `print_out` is True, returns the printable text
       otherwise return `None`.

    Notes
    ------
      1. If not already connected, the PV will first attempt to connect to
         the networked variable. As the initial connection can take some time
         (typically 30 msec or so), if a successful connection is made, a rich
         PV object with will be stored internally for later use.
      2. All time in seconds.


    Examples
    ---------
       to print a status report for the PV:
       >>>cainfo('xx.VAL')

       to get the multiline text, use
       >>>txt = cainfo('xx.VAL', print_out=False)

    """
    start_time = time.time()
    thispv = get_pv(pvname, timeout=connection_timeout, connect=True)
    out = None
    if thispv.connected:
        conn_time = time.time() - start_time
        thispv.get(timeout=timeout-conn_time)
        get_time = time.time() - start_time
        thispv.get_ctrlvars(timeout=timeout-get_time)
        if print_out:
            ca.write(thispv.info)
        else:
            out = thispv.info
    return out

def camonitor_clear(pvname):
    """clear monitors on a PV"""
    if pvname in _PVmonitors_:
        _PVmonitors_[pvname].remove_callback(index=-999)
        _PVmonitors_.pop(pvname)

def camonitor(pvname, writer=None, callback=None, connection_timeout=5.0):
    """ camonitor(pvname, writer=None, callback=None, connection_timeout=5)

    sets a monitor on a PV.

    Arguments
    ---------
     pvname (str):   name of PV
     writer (callable or None): function used to send monitor messages [None]
     callback (callback or None): custom callback function [None]
     connection_timeout (float): maximum time to wait for connection [5]


    Notes
    ------
     1. To write the result to a file, provide the writer option a
        write method to an open file or some other callable that
        accepts a string.
     2. To completely control where the output goes, provide a callback
         method and you can do whatever you'd like with them.
     3. A custom callback can be provieded.  This will be sent keyword
        arguments for pvname, value, char_value, and more.
        Important: use **kws!!

    Examples
    --------
      to write a message with the latest value for that PV each
      time the value changes and when ca.poll() is called.
      >>>camonitor('xx.VAL')
    """

    if writer is None:
        writer = ca.write
    if callback is None:
        def callback(pvname=None, value=None, char_value=None, **kwds):
            "generic monitor callback"
            if char_value is None:
                char_value = repr(value)
            writer(f"{pvname:.32s} {pv.fmt_time()} {char_value}")

    thispv = get_pv(pvname, timeout=connection_timeout, connect=True)
    if thispv.connected:
        thispv.get()
        thispv.add_callback(callback, index=-999, with_ctrlvars=True)
        _PVmonitors_[pvname] = thispv

def caget_many(pvlist, as_string=False, as_numpy=True, count=None,
               timeout=1.0, connection_timeout=5.0, conn_timeout=None):
    """caget_many(pvlist, as_string=False, as_numpy=True, count=None,
                 timeout=1.0, connection_timeout=5.0, conn_timeout=None)
    get values for a list of PVs, working as fast as possible

    Arguments
    ---------
     pvlist (list):        list of pv names to fetch
     as_string (bool):     whether to get values as strings [False]
     as_numpy (bool):      whether to get values as numpy arrys [True]
     count  (int or None): max number of elements to get [None]
     timeout (float):      timeout on *each* get()  [1.0]
     connection_timeout (float): timeout for *all* pvs to connect [5.0]
     conn_timeout (float):  back-compat alias or connection_timeout

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
    if conn_timeout is not None:
        connection_timeout = conn_timeout
    expire_time = time.time() + connection_timeout
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

def caput_many(pvlist, values, wait=False, connection_timeout=5.0,
               put_timeout=60):
    """caput_many(pvlist, values, wait=False, connection_timeout=5.0,
               put_timeout=60)


    put values to a list of PVs, as quickly as possible

    Arguments
    ----------
     pvlist (iterable):   list of PV names
     values (iterable):   list of values for corresponding PVs
     wait  (bool or string):   whether to wait for puts (see notes) [False]
     put_timeout (float):  maximum time to wait for the put to complete [60]
     connection_timeout (float): maximum time to wait for connection [5]


    Returns
    --------
     a list of ints or `None`, with values of 1 if the put was successful,
     or a negative number if the put failed (say, the timeout was exceeded),
     or `None` if the connection failed.

    Notes
    ------
      1. This does not maintain the PV objects.

      2. If wait is 'each', *each* put operation will block until it is
         complete or until the put_timeout duration expires.
         If wait is 'all', this method will block until *all* put
         operations are complete, or until the put_timeout expires.

         This 'wait' only applies to the put timeout, not the
         connection timeout.

    """
    if len(pvlist) != len(values):
        raise ValueError("List of PV names must be equal to list of values.")
    kwargs = {'auto_monitor': False, 'timeout': connection_timeout}
    pvs = [get_pv(name, **kwargs) for name in pvlist]

    wait_all = wait=='all'
    put_kws = {'wait': (wait=='each'), 'timeout': put_timeout,
               'use_complete': wait_all}
    put_ret = []
    for pvo, val in zip(pvs, values):
        put_ret.append(pvo.put(val, **put_kws))
    out = None
    if wait_all:
        start_time = time.time()
        while not all(((pv.connected and pv.put_complete) for pv in pvs)):
            ca.poll()
            elapsed_time = time.time() - start_time
            if elapsed_time > put_timeout:
                break
        out = [1 if (pv.connected and pv.put_complete) else -1 for pv in pvs]
    else:
        out = [val if val == 1 else -1 for val in put_ret]
    return out

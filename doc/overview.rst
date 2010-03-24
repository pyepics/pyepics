
==============================
EPICS Channel Access in Python 
==============================

Py-Epics3 contains a Python package named `epics` which consists of several
modules to interact with EPICS.  The simplest approach uses the functions
:func:`caget`, :func:`caput`, :func:`camonitor`, :func:`camonitor_clear`,
and :func:`cainfo` within the top-level `epics` module.  These functions
are similar to the Unix command line utilities and to the EZCA library
interface, and described in more detail below.

Most users will probably want to create and use `PV` objects provided by
the `pv` module.  The `PV` class provides a PV object that has both methods
(including :func:`get` and :func:`put`) and attributes that are kept
automatically synchronized with the remote PV.

The lowest-level CA functionality is exposed in the `ca` and `dbr` module.
While  not necessarily intended for general use, this module does provide a
fairly complete wrapping of the basic EPICS CA library, and is quite
useable, if a little more verbose and C-like than using PV objects.

In addition, the `epics` package contains more specialized modules for
Epics motors, alarms, a host of other *devices* (collections of PVs), and a
set of wxPython widget classes for using EPICS PVs with wxPython.


:mod:`epics`: caget(), caput() and related functions
====================================================

.. module:: epics
   :synopsis: top-level epics module, and container for simplest CA functions

The simplest interface to EPICS Channel Access provides functions
:func:`caget`, :func:`caput`, as well as functions :func:`camonitor`,
:func:`camonitor_clear`, and :func:`cainfo`.  These are similar to the
EPICS command line utilities and to the functions in the EZCA library.
These all take the name of an Epics Process Variable (PV) as the first
argument.

:func:`caget`
~~~~~~~~~~~~~

..  function:: caget(pvname[, as_string=False])

  retrieves and returns the value of the named PV.

  :param pvname: name of Epics Process Variable
  :param as_string:  whether to return string representation of the PV value.
  :type as_string: True or False
 
The optional *as_string* argument tells the function to return the **string
representation** of the value.  The details of the string representation
depends on the variable type of the PV.  For integer (short or long) and
string PVs, the string representation is pretty easy: 0 will become '0',
for example..  For float and doubles, the internal precision of the PV is
used to format the string value.  For enum types, the name of the enum
state is returned.

For most array (waveform) records, the string representation will be
something like::

  <array size=128, type=int>

depending on the size and type of the waveform.  As an important special
case, CHAR waveforms will be turned to Python strings when *as_string* is
``True``.  This is to work around a painful limitation on the maximum
length (40 characters!) of EPICS strings which leads CHAR waveforms to be
used as longer strings::

    >>> from epics import caget, caput, cainfo
    >>> print caget('XXX:m1.VAL')
    1.200
   >>> print caget('XXX:dir')                                                                                                          
   array([ 84,  58,  92, 120,  97, 115,  95, 117, 115, 101, 114,  92,  77,
        97, 114,  99, 104,  50,  48,  49,  48,  92,  70,  97, 115, 116,
        77,  97, 112,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0])
   >>> print caget('XXX:dir',as_string=True)
   'T:\\xas_user\\March2010\\FastMap'


:func:`caput`
~~~~~~~~~~~~~

..  function:: caput(pvname,value[, wait=False[, timeout=60]])

  set the value of the named PV.  

  :param pvname: name of Epics Process Variable
  :param value:  value to send to  PV
  :param wait:  whether to wait until the processing has completed.
  :type wait: True or False
  :param timeout:  how long to wait (in seconds) for put to complete before giving up.
  :type timeout: double
  :rtype: integer

The optional *wait* argument tells the function to wait until the
processing completes.  This can be useful for PVs which take significant
time to complete, for example moving a physical motor.  The *timeout*
argument gives the maximum time to wait, in seconds.  The function will
return after this (approximate) time even if the :func:`caput` has not
completed.

This function returns 1 on success, and a negative number if the timeout
has been exceeded.

    >>> from import epics import caget, caput, cainfo
    >>> caput('XXX:m1.VAL',2.30)
    1  
    >>> caput('XXX:m1.VAL',-2.30, wait=True)
    ... waits a few seconds ...
    1  

:func:`cainfo`
~~~~~~~~~~~~~~

..  function:: cainfo(pvname[, print_out=True])

  prints (or returns as a string) an informational paragraph about the PV,
  including Control Settings.

  :param pvname: name of Epics Process Variable
  :param print_out:  whether to write results to standard output (otherwise the string is returned).
  :type print_out: True or False

With *print_out=False*, the paragraph will not
be printed, but returned.

    >>> from epics import caget, caput, cainfo
    >>> cainfo('XXX.m1.VAL')
    == XXX:m1.VAL  (double) ==
       value      = 2.3
       char_value = 2.3000
       count      = 1
       units      = mm
       precision  = 4
       host       = xxx.aps.anl.gov:5064
       access     = read/write
       status     = 1
       severity   = 0
       timestamp  = 1265996455.417 (2010-Feb-12 11:40:55.417)
       upper_ctrl_limit    = 200.0
       lower_ctrl_limit    = -200.0
       upper_disp_limit    = 200.0
       lower_disp_limit    = -200.0
       upper_alarm_limit   = 0.0
       lower_alarm_limit   = 0.0
       upper_warning_limit = 0.0
       lower_warning       = 0.0
       PV is monitored internally
       no user callbacks defined.
    =============================

:func:`camonitor`
~~~~~~~~~~~~~~~~~


..  function:: camonitor(pvname[, writer=None[, callback=None]])

  This `sets a monitor` on the named PV, and will print out (by default)
  the PV name, time, and value each time the value changes.  

  :param pvname: name of Epics Process Variable
  :param writer:  whether to write results to standard output (otherwise the string is returned).
  :type writer: None or a method that can take a string
  :param callback:  user-supplied function to receive result
  :type callback: None or callable


One can any function that can take a string as *writer*, such as the
`write` method of a file open for writing.  If left as ``None``, messages
of changes will be sent to :func:`sys.stdout.write`. For more complete
control, one can specify a *callback* function to be called on each change
event.  This callback should take keyword arguments for *pvname*, *value*,
and *char_value*.  See :ref:`pv-callbacks-label` for information on writing
callback functions.

:func:`camonitor_clear`
~~~~~~~~~~~~~~~~~~~~~~~

..  function:: camonitor_clear(pvname)

  clears a monitor set on the named PV by :func:`camonitor`.

  :param pvname: name of Epics Process Variable

    >>> import epics
    >>> fh = open('PV1.log','w')
    >>> epics.camonitor('XXX:DMM1Ch2_calc.VAL',writer=fh.write)
    >>> .... wait for changes ...
    >>> epics.camonitor_clear('XXX:DMM1Ch2_calc.VAL')
    >>> fh.close()
    >>> fh = open('PV1.log','r')
    >>> for i in fh.readlines(): print i[:-1]
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:40.536946 -183.5035
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:41.536757 -183.6716
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:42.535568 -183.5112
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:43.535379 -183.5466
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:44.535191 -183.4890
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:45.535001 -183.5066
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:46.535813 -183.5085
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:47.536623 -183.5223
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:48.536434 -183.6832

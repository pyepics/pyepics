
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


epics module: caget(), caput() and related functions
====================================================

.. module:: epics
   :synopsis: top-level epics module, and container for simplest CA functions

The simplest interface to EPICS Channel Access provides functions
:func:`caget`, :func:`caput`, as well as functions :func:`camonitor`,
:func:`camonitor_clear`, and :func:`cainfo`.  These are similar to the
EPICS command line utilities and to the functions in the EZCA library.
These all take the name of an Epics Process Variable (PV) as the first
argument.

..  function:: caget(pvname[, as_string=False])
 
This function retrieves and returns the value of the named PV.
The optional argument *as_string* tells the function to return the **string
representation** of the value.  The string representation depends on the
variable type of the PV.  For integer (short or long) and string PVs, the
string representation is pretty easy.  For float and doubles, the
internal precision of the PV is used to format the string value.  For enum
types, the name of the enum state is returned.  

For most array (waveform) records, the string representation will be
something like `<array size=128, type=int>`, depending on the size and type
of the waveform.  As an important special case, CHAR waveforms will be
turned to Python strings when *as_string* is ``True``.  This is to work around
a painful limitation on the maximum length (40 characters!) of EPICS
strings which leads CHAR waveforms to be used as longer strings::

    >>> from import epics import caget, caput, cainfo
    >>> print caget('XXX:m1.VAL')
    1.200

..  function:: caput(pvname,value[, wait=False[, timeout=60]])

This function sets the value of the named PV.  The optional argument *wait*
tells the function to wait until the processing completes.  This can be
useful for PVs which take significant time to complete, for example moving
a physical motor.  The *timeout* argument gives the maximum time to wait,
in seconds.  The function will return after this (approximate) time even if
the :func:`put` has not completed.  

This function returns 1 on success, and a negative number if the timeout
has been exceeded.

    >>> from import epics import caget, caput, cainfo
    >>> caput('XXX:m1.VAL',2.30)
    1  
    >>> caput('XXX:m1.VAL',-2.30, wait=True)
    ... waits a few seconds ...
    1  

..  function:: cainfo(pvname[, print_out=True])

This function prints out (or returns as a string) an informational
paragraph about the PV, including Control Settings.  With *print_out=False*,
the paragraph will not be printed, but returned.

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


..  function:: camonitor(pvname[, writer=None[, callback=None]])

This function `sets a monitor` on the named PV, and will print out (by
default) the PV name, time, and value each time the value changes.  One can
optionally pass any function that can take a string, for example the
`write` method of a file open for writing, to *writer*.  If left as ``None``,
messages of changes will be sent to :func:`sys.stdout.write`. For more complete
control, one can specify a *callback* function to be called on each change
event.  This callback should take keyword arguments for *pvname*, *value*,
and *char_value*.  See :ref:`pv-callbacks` for information on writing
callback functions.

..  function:: camonitor_clear(pvname)

clears a `monitor` set on the named PV by :func:`camonitor`.

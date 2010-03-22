
==============================
EPICS Channel Access in Python 
==============================

Py-Epics3 consists of several modules to interact with EPICS. The simplest
approach uses the functions :func:`caget`, :func:`caput`,
:func:`camonitor`, :func:`camonitor_clear`, and :func:`cainfo` which are
similar to the Unix command line utilities and to the EZCA interface.  Most
users will want to create and use PV objects provided by the pv modules.


The lowest-level CA functionality is exposed in the *ca* and *dbr* module,
while a higher-level, more pythonic object-oriented interface is provided
in the *pv* module.  Py-Epics3 also provides functions caget(), caput(),
and cainfo() for the simplest of interaction with EPICS similar to EZCA and
the Unix command-line tools.  In addition, there are modules for Epics
motors, alarms, and other devices, and special widget classes for using
EPICS PVs with wxPython.


Simple Functional Interface: caget(), caput() and related functions
===================================================================

The simplest interface to EPICS Channel Access provides functions
:func:`caget`, :func:`caput`, as well as functions :func:`camonitor`,
:func:`camonitor_clear`, and :func:`cainfo`.  These are similar to the EZCA
EPICS interface and to the EPICS command line utilities.  These all take
the name of an Epics Process Variable (PV) as the first argument.

..  function:: caget(pvname[, as_string=False])

    .. index:: caget
 
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
turned to Python strings when *as_string* is True.  This is to work around
a painful limitation on the maximum length (40 characters!) of EPICS
strings which leads CHAR waveforms to be used as longer strings::

    >>> from import epics import caget, caput, cainfo
    >>> print caget('XXX:m1.VAL')
    1.200

..  function:: caput(pvname,value[, wait=False[, timeout=60]])

    .. index:: caput

This function sets the value of the named PV.  The optional argument *wait*
tells the function to wait until the processing completes.  This can be
useful for PVs which take significant time to complete, for example moving
a physical motor.  The *timeout* argument gives the maximum time to wait,
in seconds.  The function will return after this (approximate) time even if
the :func:`put` has not completed.  

This function returns 1 on success, and a negative number if the timeout
has been exceeded.::

    >>> from import epics import caget, caput, cainfo
    >>> caput('XXX:m1.VAL',2.30)
    1  
    >>> caput('XXX:m1.VAL',-2.30, wait=True)
    1  

..  function:: cainfo(pvname[, print_out=True])

    .. index:: cainfo

This function prints out (or returns) an informational paragraph about the
PV, includin Control Settings.  With *print_out=False*, the paragraph will
not be printed, but returned.::

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


..  function:: camonitor(pvname[, writer=None])

    .. index:: camonitor


..  function:: camonitor_clear(pvname)

    .. index:: camonitor_clear

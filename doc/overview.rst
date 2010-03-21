
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


caget(), caput() and cainfo()
=============================

The simplest interface to EPICS Channel Access provides functions caget(),
caput(), and cainfo(), similar to the EZCA interface and to the
EPICS-supplied command line utilities.  These all take the name of an Epics
Process Variable as the first argument.

    >>> from import epics import caget, caput, cainfo
    >>> print caget('XXX:m1.VAL')
    1.200
    >>> caput('XXX:m1.VAL',2.30)
    1  
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

the included html documentation see the doc directory.


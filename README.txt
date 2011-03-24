
Py-Epics 3:  Epics Channel Access for Python
============================================

Py-EPICS3 is a Python interface to the EPICS Channel Access (CA) library
for the EPICS control system.

This interface is meant to replace older Epics-Python interfaces, including
EpicsCA.  This interface is under active development. Currently, most
features are working, but more testing, polish, and documentation are
needed. In addition, better compatibility with other existing Epics-Python
interfaces is desired.

The goals of this module include providing both low-level (C-like) and
higher-level access (with Pythonic objects) to the EPICS Channnel Access
(CA) protocol.  Py-Epics3 uses Python's ctypes library to wrap the basic CA
functionality, and builds higher level objects on top of that basic
interface.  Using ctypes has several advantages, including no need for
extension code written in C, better thread-safety, and easier installation
on multiple platforms. 

This package requires python2.5 or higher.  The EPICS (v 3.14.8 or higher,
I think) Channel Access libraries are also required. Specifically, the
shared libraries libCom.so and libca.so (or Com.dll and ca.dll on Windows)
are required to use this module.  For Unix-like systems, these are assumed
to be available (and findable by Python at runtime) on the system. For
Windows, pre-built DLLs are included and installed so that no other Epics
installation is required.

For installation from source, see the INSTALL file. Binary installers for
Windows are available.  

License
========

This code is distributed under the  Epics Open License

Overview
========

Py-Epics3 provides two principle modules: ca, and pv, and functions
caget(), caput(), and cainfo() for the simplest of interaction with EPICS.
In addition, there are modules for Epics Motors and Alarms, autosave support 
via CA, and special widget classes for using EPICS PVs with wxPython.


caget(), caput() and cainfo()
=============================

The simplest interface to EPICS Channel Access provides functions caget(),
caput(), and cainfo(), similar to the EZCA interface and to the
EPICS-supplied command line utilities.  These all take the name of an Epics
Process Variable as the first argument.

    >>> from epics import caget, caput, cainfo
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

ca: Low-level Channel Access interface
======================================

The ca module provides a low-level 

The general concept is that an Epics Process Variable is implemented as a
python PV object, which provides the normal way to interact with Epics.
     pv = EpicsCA.PV('PVName')
     print pv.value
     pv.value = new_value


For convenience, there are also procedural functions caget and caput to
mimic the "Ezca" interface:
   x = caget('PVName')
   caput('PVName', value)

A partial consequence of that design goal is that not every part of the
C-level Channel Access library is implemented.   Channel Access features  
that ARE included here are:
     user callbacks:       user-supplied python function(s) that are run
                           when a PV's value changes.
     control values:       a full Control DBR record can be requested.
     enumeration strings:  enum PV types have integer or string
                           representation, and you get access to both.
 
     put with wait:        The PV.put() method can optionally wait until 
                           the record is done processing (and a timeout 

Features that you won't have to worry about:
     connection management (unless you choose to worry about this)
     PV record types -- this is handled automatically.


Matt Newville <newville@cars.uchicago.edu>
Last Update:  30-Mar-2010


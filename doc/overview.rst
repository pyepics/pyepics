

Overview for Python EPICS
=========================

Py-Epics3 is a Python module for the EPICS Channel Access (CA) library
for the EPICS control system.

Py-Epics3 is intended as an improvement over EpicsCA, and should replace
that older Epics-Python interface. It is under active development.  The
current status is that most features are working well, but more testing,
polish, and documentation are needed.

There are a few other Python modules exposing Epics Channel Access
available.  Being able to combine some of these has influenced the goals
for writing another Python-Epics module.  These goals include:

   a) providing both low-level (C-like) and higher-level access (Pythonic
      objects) to the EPICS Channnel Access protocol.
   b) supporting as many features of Epics 3.14 as possible, including
      preemptive callbacks and thread support.
   c) easy support and distribution for Windows and Unix-like systems.
   d) being ready for porting to Python3.
   e) using Python's ctypes library.

The main implementatio feature here (and difference from EpicsCA) is using
Python's ctypes library to do hanlde the connection between Python and the
CA C library.  Using ctypes has many advantages, including eliminating the
need to write and maintain a separate wrapper code either with SWIG or
directly with Python's C API.  Since the module is pure Python, this makes
installation on multiple platforms much easier as no compilation step is
needed.  It also provides better thread-safety, as each call to the
underlying C library is automatically made thread-aware without explicit
coding.  Migration to Python3 should also be easier, as changes to the C
API are not an issue.  Finally, since ctypes loads a shared object library
at runtime,  the underlying Epics library can be upgraded without having to
re-build the Python wrapper.

This package requires python2.5 or higher.  Version 3.14 of the EPICS
Channel Access library (v 3.14.8 or higher, I believe) is also required.
More specifically, the shared libraries libCom.so and libca.so (or Com.dll
and ca.dll on Windows) from *Epics Base* are required to use this module.
For Unix-like systems, these are assumed to be available (and findable by
Python at runtime) on the system. This may mean setting LD_LIBRARY_PATH or
DYLD_LIBRARY_PATH or configuring ldconfig.   For 32-bit Windows, pre-built
DLLs are included and installed so that no other Epics installation is
required to use the modules.

Installation from source on any platform is simply::

   python setup.py install

A binary installer for Windows is also available. 

For more details, especially about how to set paths on Unix-like systems,
see the INSTALL file.

Overview
========

Py-Epics3 consists of several modules.  The lowest-level CA functionality
is exposed in the *ca* and *dbr* module, while a higher-level, more
pythonic object-oriented interface is provided in the *pv* module.
Py-Epics3 also provides functions caget(), caput(), and cainfo() for the
simplest of interaction with EPICS similar to EZCA and the Unix
command-line tools.  In addition, there are modules for Epics motors,
alarms, and other devices, and special widget classes for using EPICS PVs
with wxPython.


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


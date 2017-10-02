[![Travis CI](https://travis-ci.org/pyepics/pyepics.png)](https://travis-ci.org/pyepics/pyepics)   [![Zenondo](https://zenodo.org/badge/4185/pyepics/pyepics.svg)](https://zenodo.org/badge/latestdoi/4185/pyepics/pyepics)

# PyEpics 3:  Epics Channel Access for Python


PyEpics is a Python interface to the EPICS Channel Access (CA) library
for the EPICS control system.

The PyEpics module includes both low-level (C-like) and higher-level access
(with Python objects) to the EPICS Channnel Access (CA) protocol.  Python's
ctypes library is used to wrap the basic CA functionality, with higher
level objects on top of that basic interface.  This approach has several
advantages including no need for extension code written in C, better
thread-safety, and easier installation on multiple platforms.

## Installation

This package requires python2.6 or higher.  The EPICS Channel Access
library v 3.14.8 or higher is also required, with v 3.14.12 or higher being
recommended. Specifically, the shared libraries libCom.so and libca.so
(or Com.dll and ca.dll on Windows, or libca.dylib and libCom.dylib on macOS)
are required to use this module.

To support this requirement, suitably recent versions of the libraries are
included here (version 3.15.3), and the OS-appropriate library will be
installed alongside the python packages. To install from source:

```
> python setup.py install
```

Or,

```
> pip install .
```

If it is desirable to forgo installation of the pre-packaged EPICS libraries,
(i.e. suitable libraries already exist on the target system), then simply
define the `NOLIBCA` environment variable prior to installation:

```
> NOLIBCA=1 python setup.py install
```

Or,

```
> NOLIBCA=1 pip install .
```

For additional installation details, see the INSTALL file. Binary installers
for Windows are available.

## License

This code is distributed under the  Epics Open License

## Overview

Py-Epics3 provides two principle modules: ca, and pv, and functions
caget(), caput(), and cainfo() for the simplest of interaction with EPICS.
In addition, there are modules for Epics Motors and Alarms, autosave support
via CA, and special widget classes for using EPICS PVs with wxPython.


## caget(), caput() and cainfo()

The simplest interface to EPICS Channel Access provides functions caget(),
caput(), and cainfo(), similar to the EZCA interface and to the
EPICS-supplied command line utilities.  These all take the name of an Epics
Process Variable as the first argument.

```python
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
```

## PV: Object Oriented CA interface

The general concept is that an Epics Process Variable is implemented as a
Python PV object, which provides a natural way to interact with EPICS.

```python
>>> import epics

>>> pv = epics.PV('PVName')
>>> pv.connected
True
>>> pv.get()
3.14
>>> pv.put(2.71)
```

Channel Access features that are included here:

* user callbacks - user-supplied Python function(s) that are run when a PV's
  value, access rights, or connection status changes
* control values - a full Control DBR record can be requested
* enumeration strings - enum PV types have integer or string representation,
  and you get access to both
* put with wait - The PV.put() method can optionally wait until the record is
  done processing (with timeout)

Features that you won't have to worry about:

* connection management (unless you choose to worry about this)
* PV record types - this is handled automatically.


Matt Newville <newville@cars.uchicago.edu>
Last Update:  18-Apr-2016

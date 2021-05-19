PyEpics:  Epics Channel Access for Python
================================

.. image:: https://github.com/pyepics/pyepics/actions/workflows/test-with-conda.yml/badge.svg
   :target: https://github.com/pyepics/pyepics/actions/workflows/test-with-conda.yml/

.. image:: https://img.shields.io/pypi/v/pyepics.svg
   :target: https://pypi.org/project/pyepics

.. image:: https://img.shields.io/badge/docs-read-brightgreen
   :target: https://pyepics.github.io/pyepics/

.. image:: https://zenodo.org/badge/4185/pyepics/pyepics.svg
   :target: https://zenodo.org/badge/latestdoi/4185/pyepics/pyepics



PyEpics is a Python interface to the EPICS Channel Access (CA) library
for the EPICS control system.

The PyEpics module includes both low-level (C-like) and higher-level access
(with Python objects) to the EPICS Channnel Access (CA) protocol.  Python's
ctypes library is used to wrap the basic CA functionality, with higher
level objects on top of that basic interface.  This approach has several
advantages including no need for extension code written in C, better
thread-safety, and easier installation on multiple platforms.

Installation
===========

This package requires python3.6 or higher.  The EPICS Channel Access
library v 3.14.8 or higher is also required. Shared libraries are provided
for Windows, MacOS, and Linux.

To install the package, use `pip install pyepics`.  To install from source, use::

    python setup.py install


For additional installation details, see the INSTALL file. Binary installers
for Windows are available.

License
----------

This code is distributed under the  Epics Open License

Overview
=================

Py-Epics3 provides two principle modules: ca, and pv, and functions
caget(), caput(), and cainfo() for the simplest of interaction with EPICS.
In addition, there are modules for Epics Motors and Alarms, autosave support
via CA, and special widget classes for using EPICS PVs with wxPython.


caget(), caput() and cainfo()
----------------------------

The simplest interface to EPICS Channel Access provides functions caget(),
caput(), and cainfo(), similar to the EZCA interface and to the
EPICS-supplied command line utilities.  These all take the name of an Epics

PV: Object Oriented CA interface
------------------------------

The general concept is that an Epics Process Variable is implemented as a
Python PV object, which provides a natural way to interact with EPICS.

   >>> import epics
   >>> pv = epics.PV('PVName')
   >>> pv.connected
   True
   >>> pv.get()
   3.14
   >>> pv.put(2.71)


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
Last Update:  18-May-2021

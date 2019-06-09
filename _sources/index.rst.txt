.. epics documentation master file

Epics Channel Access for Python
=====================================

PyEpics is an interface for the Channel Access (CA) library of the `Epics
Control System <http://www.aps.anl.gov/epics/>`_ to the Python Programming
language.  The pyepics package provides a base :mod:`epics` module to python,
with methods for reading from and writing to Epics Process Variables (PVs) via
the CA protocol.  The package includes a thin and fairly complete layer over
the low-level Channel Access library in the :mod:`ca` module, and higher level
abstractions built on top of this basic functionality.

The package includes a very simple interface to CA similar to the Unix
command-line tools and EZCA library with functions :meth:`epics.caget`,
:meth:`epics.caput`, :meth:`epics.cainfo`, and :meth:`epics.camonitor`.
For an object-oriented interface, there is also a :class:`pv.PV` class
which represents an Epics Process Variable as a full-featured and
easy-to-use Python object.  Additional modules provide higher-level
programming support to CA, including grouping related PVs into a
:class:`device.Device`, creating alarms in :class:`alarm.Alarm`, and saving
PVs values in the :mod:`autosave` module.  There is also support for
conveniently using epics PVs to wxPython widgets in the :mod:`wx` module,
and some support for using PyQt widgets in the :mod:`qt` module.

-----------

In addition to the Pyepics library described here, several applications
built with pyepics are available at `http://github.com/pyepics/epicsapps/
<http://github.com/pyepics/epicsapps/>`_.  See
`http://pyepics.github.com/epicsapps/
<http://pyepics.github.com/epicsapps/>`_ for further details.

-----------

.. toctree::
   :maxdepth: 2

   installation
   overview
   pv
   ca
   arrays
   devices
   alarm
   autosave
   wx
   advanced

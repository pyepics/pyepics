.. epics documentation master file

Epics Channel Access for Python
=====================================

PyEpics is an interface for the Channel Access (CA) library of the `Epics
Control System <https://epics-controls.org/>`_ to the Python Programming
language.  The pyepics package provides an :mod:`epics` module to python,
with methods for reading from and writing to Epics Process Variables (PVs)
via the CA protocol.  The package includes a thin and fairly complete layer
over the lowest-level Channel Access library in the :mod:`ca` module, and
higher level abstractions built on top of this basic functionality.

The package includes a very simple interface to CA similar to the Unix
command-line tools with functions :meth:`epics.caget`, :meth:`epics.caput`,
:meth:`epics.cainfo`, and :meth:`epics.camonitor`.  For an object-oriented
interface, there is also a :class:`pv.PV` class which represents an Epics
Process Variable as a full-featured and easy-to-use Python object.
Additional modules provide higher-level programming support to CA,
including grouping related PVs into a :class:`device.Device` (with a number
of predefined devices ready to use), for creating alarms in
:class:`alarm.Alarm`, and for saving PVs values in the :mod:`autosave`
module.  There is also support for conveniently using epics PVs to wxPython
widgets in the :mod:`wx` module, and some support for using PyQt widgets in
the :mod:`qt` module.

-----------

See also: Some `applications <https://pyepics.github.io/epicsapps/>`_ built
with pyepics that are available at `https://github.com/pyepics/epicsapps/
<https://github.com/pyepics/epicsapps/>`_.


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

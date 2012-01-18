.. epics documentation master file

Epics Channel Access for Python
=====================================

PyEpics is an interface for the Channel Access (CA) library of the `Epics
Control System <http://www.aps.anl.gov/epics/>`_ to the Python Programming
language.  The pyepics package provides a base :mod:`epics` module to
python, with methods for reading from and writing to Epics Process
Variables (PVs) via the CA protocol.  The package includes a fairly
complete, thin layer over the low-level Channel Access library in the
:mod:`ca` module, and higher-level abstractions built on top of this basic
functionality.

The package includes a simple, functional approach to CA similar to EZCA
and the Unix command-line tools with functions in the main :mod:`epics`
package including :meth:`epics.caget`, :meth:`epics.caput`,
:meth:`epics.cainfo`, and :meth:`epics.camonitor`.  There is also a
:class:`pv.PV` object which represents an Epics Process Variable as an
easy-to-use Python object. Additional modules provide even higher-level
programming support to Epics.  These include groups of related PVs in
:class:`device.Device`, a simple method to create alarms in
:class:`alarm.Alarm`, and support for saving PVs values in the
:mod:`autosave` module.  Finally, there is support for conveniently
tying epics PVs to wxPython widgets in the :mod:`wx` module.

-----------

In addition to the Pyepics library described here, several applications
built with pyepics are available at `http://github.com/pyepics/epicsapps/
<http://github.com/pyepics/epicsapps/>`_.  
See
`http://pyepics.github.com/epicsapps/
<http://pyepics.github.com/epicsapps/>`_ for further details.

-----------
   
.. toctree::
   :maxdepth: 1

   installation
   overview
   pv
   ca
   devices
   alarm
   autosave
   wx
   advanced


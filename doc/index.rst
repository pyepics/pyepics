.. epics documentation master file, 


<<<<<<< HEAD
Epics Channel Access for Python
=====================================

The Epics Python module is an interface for the Channel Access (CA) library
of the EPICS control system to the Python Programming language.  

The python epics package provides methods for reading from and writing to
Epics Process Variables via the CA protocol.  The package includes a
complete, thin layer over the low-level Channel Access library in the
:mod:`ca` module, and a few higher-level abstractions built on top of this
basic functionality.  The :mod:`PV` class provides a `PV` object for an
object-oriented approach, and there is also a simple functional approach to
CA similar to EZCA and the Unix command-line tools `caget`, `caput`,
`cainfo`, and `camonitor`.  In addition, there are classes for an epics
:mod:`Device`, epics :mod:`Motor`, :mod:`Alarm`, and special code for
wxPython widgets.

This documentation is also available in  
`PDF Format <http://cars9.uchicago.edu/software/python/pyepics3/pyepics3.pdf>`_.

=======
Documentation for Python Epics Package version 3
==================================================

Epics is a Python package for the Channel Access (CA) library of the EPICS
control system.  The Epics package provides simple methods for reading and
writing to Epics Process Variables PVs) via the CA protocol. 

The package contains a few modules, to provide low- and high-level
interfaces to the Channel Access library and Process Variables.  At the
lowest level, there is a fairly complete and *thin* interface to the CA
library in the :mod:`ca` module which closely follows the C library to CA.
This :mod:`ca` module is the basis for all other functionality.  The
:class:`PV` class (defined in the :mod:`pv` module) provides a high-level
`PV` object for an object-oriented programming approach.  In addition,
there is a very simple, functional approach to CA similar to EZCA and the
Unix command-line tools which provides functions :func:`caget`,
:func:`caput`, :func:`cainfo`, :func:`camonitor`, and
:func:`camonitor_clear`.


In addition, there are higher level classes for epics :class:`Device`,
:class:`Motor`, and :class:`Alarm`, all built on top of he :class:`PV`
object, and special code for wxPython widgets.

For download, see  `PyEpics3 Home Page
<http://cars9.uchicago.edu/software/python/pyepics3/>`_.

This documentation is also available in  `PDF Format
<http://cars9.uchicago.edu/software/python/pyepics3/pyepics3.pdf>`_.

>>>>>>> ce5dd90d0af58b145f12818eced4857d3f21b908
Contents:

.. toctree::
   :maxdepth: 3

   installation
   overview
   pv
   ca
   advanced
   devices
   wx
   
Indices and tables
~~~~~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



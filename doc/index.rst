.. epics documentation master file, 


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

Contents:

.. toctree::
   :maxdepth: 3

   overview
   pv
   ca
   advanced
   devices
   wx
   installation
   
Indices and tables
~~~~~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



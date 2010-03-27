.. epics documentation master file, 


Documentation for Python Epics module
=====================================

Epics is a Python package for the Channel Access (CA) library of the EPICS
control system.  This module provides simple methods for reading and
writing to Epics Process Variables via the CA protocol. The :mod:`epics`
module provides both a simple, functional approach to CA, and also a higher
level `PV` object.

The Epics package consists of a fairly complete and *thin* interface to the
low-level CA library in the :mod:`ca` module that is base of all other
functionality.  The :mod:`PV` class provides a `PV` object, as well as
classes for an epics :mod:`Device`, epics :mod:`Motor`, :mod:`Alarm`, and
special code for wxPython widgets.

Contents:

.. toctree::
   :maxdepth: 3

   overview
   pv
   ca
   devices
   wx
   installation
   
Indices and tables
~~~~~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



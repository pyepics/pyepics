.. epics documentation master file, 

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



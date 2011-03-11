====================================
Downloading and Installation
====================================

Prerequisites
~~~~~~~~~~~~~~~

This package requires Python version 2.5, 2.6, or 3.1.  I believe that
Python 2.7 will work, but this has yet not tested.  It is possible that
Python 2.4 will work if the ctypes package is installed, but this has not
been tested.

In addtion, version 3.14 of the EPICS Channel Access library (v 3.14.8 or
higher, I believe) is required.  More specifically, the shared libraries
libCom.so and libca.so (or Com.dll and ca.dll on Windows) from *Epics Base*
are required to use this module.  For 32-bit Windows, pre-built DLLs are
included and installed so that no other Epics installation is required to
use the modules.  For Unix-like systems, these are assumed to be available
(and findable by Python at runtime) on the system. This may mean setting
LD_LIBRARY_PATH or DYLD_LIBRARY_PATH or configuring ldconfig.

Downloads
~~~~~~~~~~~~

The latest stable version of the Epics Python Package is 3.0.11.  There are
a few ways to get the Epics Python Package: 

.. _epics-3.0.11.tar.gz:          http://cars9.uchicago.edu/software/python/pyepics3/src/epics-3.0.11.tar.gz
.. _epics-3.0.11.win32-py2.6.exe: http://cars9.uchicago.edu/software/python/pyepics3/src/epics-3.0.11.win32-py2.6.exe
.. _epics-3.0.11.win32-py3.1.exe: http://cars9.uchicago.edu/software/python/pyepics3/src/epics-3.0.11.win32-py3.1.exe
.. _pyepics github repository:    http://github.com/newville/pyepics
.. _PyEpics Source Tree:          http://cars9.uchicago.edu/software/python/pyepics3/src

+---------------------------+------------------------------------------+
|  Download Option          |  Location                                |
+===========================+==========================================+
|  Source Kit               |  `epics-3.0.11.tar.gz`_                  |
+---------------------------+------------------------------------------+
|  Windows Installers       |  `epics-3.0.11.win32-py2.6.exe`_  or     |
|                           |  `epics-3.0.11.win32-py3.1.exe`_         |
+---------------------------+------------------------------------------+
|  Development Version      |  use `pyepics github repository`_        |
+---------------------------+------------------------------------------+



The Epics module is still under active development, and enhancements and
bug-fixes are being added frequently.  All development is done through the
`pyepics github repository`_.  To get a read-only copy of the atest
version, use::

   git clone http://github.com/newville/pyepics.git

or::

   git clone https://github.com/newville/pyepics.git

Current and older source source kits, and Windows Installers can also be found
at the `PyEpics Source Tree`_. 

Installation
~~~~~~~~~~~~~~

Installation from source on any platform is::

   python setup.py install

For more details, especially about how to set paths for LD_LIBRARY_PATH or
DYLD_LIBRARY_PATH on Unix-like systems, see the INSTALL file.

Acknowledgements
~~~~~~~~~~~~~~~~~~~~~~

PyEpics was originally written and is maintained by Matt Newville
<newville@cars.uchicago.ed>.  Several people have provided valuable
additions or bug reports, which has greatly improved the quality of the
library: Michael Abbott, Marco Cammarata, Angus Gratton, Craig Haskins,
Pete Jemian, Andrew Johnson, Janko Kolar, Irina Kosheleva, Tim Mooney, Mark
Rivers, Friedrich Schotte, Steve Wasserman, and Glen Wright.


Epics Open License
~~~~~~~~~~~~~~~~~~~~~~

This code and all material associated with it are distributed under the
Epics Open License:


.. include:: ../license.txt


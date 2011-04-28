====================================
Downloading and Installation
====================================

Prerequisites
~~~~~~~~~~~~~~~

This package requires Python version 2.5, 2.6, 2.7, or 3.1.  I It is
possible that Python 2.4 will work if the ctypes package is installed, but
this has not been tested.  In addition, Python 3.2 should work as well, but
was not tested as of this writing.

In addition, version 3.14 of the EPICS Channel Access library (v 3.14.8 or
higher, I believe) is required.  More specifically, the shared libraries
libCom.so and libca.so (or Com.dll and ca.dll on Windows) from *Epics Base*
are required to use this module.  Using a patched version of 3.14.12 is
recommended -- some of the features for 'subarray records' will only work
with this latest version.  

For 32-bit Windows, pre-built DLLs from 3.14.12 (patched as of March, 2011)
are included and installed so that no other Epics installation is required
to use the modules.  For Unix-like systems, these are assumed to be
available (and findable by Python at runtime) on the system. This may mean
setting LD_LIBRARY_PATH or DYLD_LIBRARY_PATH or configuring ldconfig.

Downloads
~~~~~~~~~~~~~

The latest stable version of the Epics Python Package is 3.1.2.  There are
a few ways to get the Epics Python Package: 

.. _pyepics-3.1.2.tar.gz (CARS):   http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.1.2.tar.gz
.. _pyepics-3.1.2.tar.gz (PyPI):   http://pypi.python.org/packages/source/p/pyepics/pyepics-3.1.2.tar.gz
.. _pyepics-3.1.2.win32-py2.6.exe: http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.1.2.win32-py2.6.exe
.. _pyepics-3.1.2.win32-py2.7.exe: http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.1.2.win32-py2.7.exe
.. _pyepics-3.1.2.win32-py3.1.exe: http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.1.2.win32-py3.1.exe
.. _pyepics github repository:    http://github.com/pyepics/pyepics
.. _PyEpics Source Tree:          http://cars9.uchicago.edu/software/python/pyepics3/src
.. _PyPi Epics Entry:             http://pypi.python.org/pypi/pyepics/
.. _Python Setup Tools:           http://pypi.python.org/pypi/setuptools

+---------------------------+------------------------------------------+
|  Download Option          |  Location                                |
+===========================+==========================================+
|  Source Kit               |  `pyepics-3.1.2.tar.gz (CARS)`_  or      |
|                           |  `pyepics-3.1.2.tar.gz (PyPI)`_          |
+---------------------------+------------------------------------------+
|  Windows Installers       |  `pyepics-3.1.2.win32-py2.6.exe`_  or    |
|                           |  `pyepics-3.1.2.win32-py2.7.exe`_        |
|                           |  `pyepics-3.1.2.win32-py3.1.exe`_        |
+---------------------------+------------------------------------------+
|  Development Version      |  use `pyepics github repository`_        |
+---------------------------+------------------------------------------+

if you have `Python Setup Tools`_  installed, you can download and install
the PyEpics Package simply with::

   easy_install -U pyepics


Testing
~~~~~~~~~~~~~

Some automated unit-testing is done, using the tests folder from the source
distribution kit.  The following systems were tested for 3.1.2, all with
Epics base 3.14.12.1.  Except as noted, all tests pass.  Those tests that
fail are generally well-understood.

+-----------+-----------------+------------+-----------------------------+
|  Host OS  | Epics HOST ARCH |  Python    |   Tests Failed, Notes       |
+===========+=================+============+=============================+
| Linux     |  linux-x86      |  2.5.1     |   autosave not tested       |
+-----------+-----------------+------------+-----------------------------+
| Linux     |  linux-x86      |  2.6       |   all pass                  |
+-----------+-----------------+------------+-----------------------------+
| Linux     |  linux-x86      |  2.6.6     |   all pass                  |
+-----------+-----------------+------------+-----------------------------+
| Linux     |  linux-x86_64   |  2.7       |   all pass                  |
+-----------+-----------------+------------+-----------------------------+
| Linux     |  linux-x86_64   |  3.1       |   all pass                  |
+-----------+-----------------+------------+-----------------------------+
| Windows   |   win32-x86     |  2.6.5     |   all pass                  |
+-----------+-----------------+------------+-----------------------------+
| Windows   |   win32-x86     |  2.7.1     |   all pass                  |
+-----------+-----------------+------------+-----------------------------+
| Windows   |   win32-x86     |  3.1       |   pyparsing/autosave        |
+-----------+-----------------+------------+-----------------------------+
| Mac OSX   |  darwin-x86     |  2.6.5     |   all pass                  |
+-----------+-----------------+------------+-----------------------------+


Note that tests involving subarrays are known to fail with Epics base of
3.14.11 and earlier.  The autosave module relies on the 3rd part extension
pyparsing, which seems to not work correctly for Python3.1 and was not
installed on one tested system.  The wx module is not automatically
tested. 


Development Version
~~~~~~~~~~~~~~~~~~~~~~~~

The PyEpics module is still under active development, and enhancements and
bug-fixes are being added frequently.  All development is done through the
`pyepics github repository`_.  To get a read-only copy of the latest
version, use::

   git clone http://github.com/pyepics/pyepics.git

or::

   git clone git@github.com/pyepics/pyepics.git

Current and older source source kits, and Windows Installers can also be found
at the `PyEpics Source Tree`_.   

Installation
~~~~~~~~~~~~~~~~~

Installation from source on any platform is::

   python setup.py install

For more details, especially about how to set paths for LD_LIBRARY_PATH or
DYLD_LIBRARY_PATH on Unix-like systems, see the INSTALL file.

Again, if you have `Python Setup Tools`_  installed, you can download and 
install the PyEpics Package with::

   easy_install -U pyepics


Acknowledgments
~~~~~~~~~~~~~~~~~~~~~~

PyEpics was originally written and is maintained by Matt Newville
<newville@cars.uchicago.ed>.  Important contributions to the library have
come from Angus Gratton, at the Australian National University.  Several
other people have provided valuable additions, suggestions, or bug reports,
which has greatly improved the quality of the library: Michael Abbott,
Marco Cammarata, Craig Haskins, Pete Jemian, Andrew Johnson, Janko Kolar,
Irina Kosheleva, Tim Mooney, Eric Norum, Mark Rivers, Friedrich Schotte, 
Mark Vigder, Steve Wasserman, and Glen Wright.


Epics Open License
~~~~~~~~~~~~~~~~~~~~~~

The PyEpics source code, this documentation, and all material associated
with it are distributed under the Epics Open License:

.. include:: ../license.txt


In plain words, this means

  a. you can use this software for any purpose.

  b. you can modify and redistribute this software if you keep existing copyright notices intact.

  c. you cannot claim that you wrote this software or remove copyright notices.

  d. you cannot claim the copyright holders endorse your use of this software.
  
  e. you cannot claim the copyright holders owe you anything if the software does not work as you expect it to, and 

  f. if you are the US government, you can probably do whatever you want. ;)


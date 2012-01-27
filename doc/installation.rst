====================================
Downloading and Installation
====================================

Prerequisites
~~~~~~~~~~~~~~~

This package requires Python version 2.5, 2.6, 2.7, or 3.2.  It should work
with Python 3.1, as well, but this is no longer being tested as of this
writing.

In addition, version 3.14 of the EPICS Channel Access library (v 3.14.8 or
higher, I believe) is required.  More specifically, the shared libraries
libCom.so and libca.so (or Com.dll and ca.dll on Windows) from *Epics Base*
are required to use this module.  Using version 3.14.12 or higher is
recommended -- some of the features for 'subarray records' will only work
with this 3.14.12 and higher.

For 32-bit Windows, pre-built DLLs from 3.14.12 (patched as of March, 2011)
are included and installed so that no other Epics installation is required
to use the modules.  For Unix-like systems, these are assumed to be
available (and findable by Python at runtime) on the system. This may mean
setting LD_LIBRARY_PATH or DYLD_LIBRARY_PATH or configuring ldconfig.

The Python `numpy module <http://numpy.scipy.org/>`_ is not strictly
required, but will be used to convert EPICS waveforms values into numerical
array data if available, and its use is strongly encouraged. 

Downloads
~~~~~~~~~~~~~

The latest stable version of the PyEpics Package is 3.2.0.  There are
a few ways to get the PyEpics Package:

.. _pyepics-3.2.0.tar.gz (CARS):   http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.2.0.tar.gz
.. _pyepics-3.2.0.tar.gz (PyPI):   http://pypi.python.org/packages/source/p/pyepics/pyepics-3.2.0.tar.gz
.. _pyepics-3.2.0.win32-py2.6.exe (CARS): http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.2.0.win32-py2.6.exe
.. _pyepics-3.2.0.win32-py2.7.exe (CARS): http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.2.0.win32-py2.7.exe
.. _pyepics-3.2.0.win32-py3.2.exe (CARS): http://cars9.uchicago.edu/software/python/pyepics3/src/pyepics-3.2.0.win32-py3.2.exe
.. _pyepics-3.2.0.win32-py2.6.exe (PyPI): http://pypi.python.org/packages/source/p/pyepics/pyepics-3.2.0.win32-py2.6.exe
.. _pyepics-3.2.0.win32-py2.7.exe (PyPI): http://pypi.python.org/packages/source/p/pyepics/pyepics-3.2.0.win32-py2.7.exe
.. _pyepics-3.2.0.win32-py3.2.exe (PyPI): http://pypi.python.org/packages/source/p/pyepics/pyepics-3.2.0.win32-py3.2.exe
.. _pyepics github repository:    http://github.com/pyepics/pyepics
.. _PyEpics Source Tree:          http://cars9.uchicago.edu/software/python/pyepics3/src
.. _PyPi Epics Entry:             http://pypi.python.org/pypi/pyepics/
.. _Python Setup Tools:           http://pypi.python.org/pypi/setuptools

+-----------------+------------+----------------------------------------------+
|  Download Type  | Py Version |   Location                                   |
+=================+============+==============================================+
| Source tarball  | All        | `pyepics-3.2.0.tar.gz (CARS)`_  or           |
|                 |            | `pyepics-3.2.0.tar.gz (PyPI)`_               |
+-----------------+------------+----------------------------------------------+
| Win32 Installer | 2.6        |  `pyepics-3.2.0.win32-py2.6.exe (CARS)`_  or |
|                 |            |  `pyepics-3.2.0.win32-py2.6.exe (PyPI)`_  or |
+-----------------+------------+----------------------------------------------+
| Win32 Installer | 2.7        |  `pyepics-3.2.0.win32-py2.7.exe (CARS)`_  or |
|                 |            |  `pyepics-3.2.0.win32-py2.7.exe (PyPI)`_  or |
+-----------------+------------+----------------------------------------------+
| Win32 Installer | 3.2        |  `pyepics-3.2.0.win32-py3.2.exe (CARS)`_  or |
|                 |            |  `pyepics-3.2.0.win32-py3.2.exe (PyPI)`_  or |
+-----------------+------------+----------------------------------------------+
|  Development    | All        |  `pyepics github repository`_                |
+-----------------+------------+----------------------------------------------+

If you have `Python Setup Tools`_  installed, you can download and install
the PyEpics Package simply with::

   easy_install -U pyepics


Testing
~~~~~~~~~~~~~

Some automated unit-testing is done, using the tests folder from the source
distribution kit.  The following systems were tested for 3.2.0, all with
Epics base 3.14.12.1 or bas 3.14.12.2.  Except as noted, all tests pass.
Those tests that fail are generally well-understood.

+-----------+-----------------+------------+-----------------------+
|  Host OS  | Epics HOST ARCH |  Python    |  Failures, Notes      |
+===========+=================+============+=======================+
| Linux     |  linux-x86      |  2.5.1     |   all pass            |
+-----------+-----------------+------------+-----------------------+
| Linux     |  linux-x86      |  2.6       |   all pass            |
+-----------+-----------------+------------+-----------------------+
| Linux     |  linux-x86      |  2.7.1     |   all pass            |
+-----------+-----------------+------------+-----------------------+
| Linux     |  linux-x86_64   |  2.7.1     |   all pass            |
+-----------+-----------------+------------+-----------------------+
| Linux     |  linux-x86_64   |  3.2       |   autosave fails      |
+-----------+-----------------+------------+-----------------------+
| Mac OSX   |  darwin-x86     |  2.6.5     |   all pass            |
+-----------+-----------------+------------+-----------------------+
| Windows   |  win32-x86      |  2.6.6     |   all pass            |
+-----------+-----------------+------------+-----------------------+
| Windows   |  win32-x86      |  2.7.2     |   all pass            |
+-----------+-----------------+------------+-----------------------+
| Windows   |  win32-x86      |  3.2.2     |   autosave fails      |
+-----------+-----------------+------------+-----------------------+


Testing Notes:

  1. tests involving subarrays are known to fail with Epics base earlier
     than 3.14.11.

  2. The autosave module relies on the 3rd part extension pyparsing, which
     seems to not work correctly for Python3.

  3. The wx module is not automatically tested.

  4. CA is not yet working with 64-bit Python on 64-bit Windows. It *does*
     work with 32-bit Python on 64-bit Linux, and Channel Access is known
     to work with 64-bit  Windows.  The current status is: I can get the
     64-bit ca.dll to load with 64-bit Python, but there seems to be some
     disagreement about the lengths of basic C data types (for example,
     does a double take 8 or 16 bytes).  This is being investigated....

Development Version
~~~~~~~~~~~~~~~~~~~~~~~~

The PyEpics module is still under active development, with enhancements and
bug-fixes are being added frequently.  All development is done through the
`pyepics github repository`_.  To get a read-only copy of the latest
version, use one of::

   git clone http://github.com/pyepics/pyepics.git
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


Getting Started, Setting up the Epics Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order for PyEpics to work at correctly, it must be able to find and load the
Channel Access dynamic library (*libca.so*, *libca.dylib*, or *ca.dll*
depending on the system).  This dynamic library needs to found at runtime.

There are a few ways to specify how to find this library:

 1. set the environmental variable ``PYEPICS_LIBCA`` to the full path of the dynamic library, for example::

     > export PYEPICS_LIBCA=/usr/local/epics/base-3.14.12.1/lib/linux-x86/libca.so

 2. set the environmental variables ``EPICS_BASE`` and  ``EPICS_HOST_ARCH``
    to point to where the library was built.   For example::

     > export EPICS_BASE=/usr/local/epics/base-3.14.12.1
     > export EPICS_HOST_ARCH=linux-x86

    will find the library at /usr/local/epics/base-3.14.12.1/lib/linux-x86/libca.so.

 3. Put the dynamic library somewhere in the Python path.  A convenient
    place might be the same ``site-packages/pyepics library`` folder as the
    python package is installed.

Note, that For Windows users, the DLLs (ca.dll and Com.dll) are included in the
installation kit, and automatically installed to where they can be found at
runtime (following rule 3 above).

With the Epics library loaded, it will need to be able to connect to Epics
Process Variables. Generally, these variables are provided by Epics I/O
controllers (IOCs) that are processes running on some device on the
network.   If you're connecting to PVs provided by IOCs on your local
subnet, you should have no trouble.  If trying to reach further network,
you may need to set the environmental variable ``EPICS_CA_ADDR_LIST`` to
specify which networks to search for PVs.


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





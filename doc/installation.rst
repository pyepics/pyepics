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

There are a few ways to get the Epics Python Package:


=========================== =====================================
  **Download Option**          Location
--------------------------- -------------------------------------
  **Source Kit**               http://cars9.uchicago.edu/software/python/pyepics3/src/epics-3.0.7.tar.gz
--------------------------- -------------------------------------
  **Windows Installers**       http://cars9.uchicago.edu/software/python/pyepics3/src/epics-3.0.7.win32-py2.6.exe 
                               http://cars9.uchicago.edu/software/python/pyepics3/src/epics-3.0.7.win32-py3.1.exe
--------------------------- -------------------------------------
  **Development Version**      http://github.com/newville/pyepics    use             
                                 `git clone https://newville@github.com/newville/pyepics.git`
=========================== =====================================

All current development is done through the github repository above. For older source kits and Windows Binaries, browse the `Python Epics Source Tree <http://cars9.uchicago.edu/software/python/pyepics3/src/>`_

Installation
~~~~~~~~~~~~~~

Installation from source on any platform is::

   python setup.py install

For more details, especially about how to set paths for LD_LIBRARY_PATH or
DYLD_LIBRARY_PATH on Unix-like systems, see the INSTALL file.

Epics Open License
~~~~~~~~~~~~~~~~~~~~~~

This code and all material associated with it are distributed under the
Epics Open License:


.. literalinclude:: ../license.txt


============
Installation
============

This package requires Python version 2.5, 2.6, or 3.1.  I believe that
Python 2.7 will work, but this has yet not tested.  It is possible that
Python 2.4 will work if the ctypes packa is installed, but this has not
been tested.

Version 3.14 of the EPICS Channel Access library (v 3.14.8 or higher, I
believe) is required.  More specifically, the shared libraries libCom.so
and libca.so (or Com.dll and ca.dll on Windows) from *Epics Base* are
required to use this module.  For Unix-like systems, these are assumed to
be available (and findable by Python at runtime) on the system. This may
mean setting LD_LIBRARY_PATH or DYLD_LIBRARY_PATH or configuring ldconfig.
For 32-bit Windows, pre-built DLLs are included and installed so that no
other Epics installation is required to use the modules.

Installation from source on any platform is::

   python setup.py install

For Windows, binary installers will be available. 

For more details, especially about how to set paths on Unix-like systems,
see the INSTALL file.

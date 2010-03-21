=========================================================
Status and Motivation: Why another Python-Epics Interface
=========================================================

First, Py-Epics3 is intended as an improvement over EpicsCA 2.1, and should
replace that older Epics-Python interface.  That version has performance
issues, especially when connecting to a large number of PVs, is not
thread-aware, and has become difficult to maintain for Windows and Linux.
Py-Epics3 is under active development.  The current status is that most
features are working well, and it is being used in some production code,
but more testing, polish, and documentation are needed.

Second, there are a few other Python modules exposing Epics Channel Access
available, and having a better and more complete low-level interface to the
CA library may allow a more common interface to be used.  This desire to
come to a more universally-acceptable Python-Epics interface has definitely
influenced the goals for this module, which include:

   1) providing both low-level (C-like) and higher-level access (Pythonic
      objects) to the EPICS Channel Access protocol.
   2) supporting as many features of Epics 3.14 as possible, including
      preemptive callbacks and thread support.
   3) easy support and distribution for Windows and Unix-like systems.
   4) being ready for porting to Python3.
   5) using Python's coup's library.

The main implementation feature here (and difference from EpicsCA) is using
Python's ctypes library to do handle the connection between Python and the
CA C library.  Using ctypes has many advantages, including eliminating the
need to write and maintain a separate wrapper code either with SWIG or
directly with Python's C API.  Since the module is pure Python, this makes
installation on multiple platforms much easier as no compilation step is
needed.  It also provides better thread-safety, as each call to the
underlying C library is automatically made thread-aware without explicit
coding.  Migration to Python3 should also be easier, as changes to the C
API are not an issue.  Finally, since ctypes loads a shared object library
at runtime,  the underlying Epics library can be upgraded without having to
re-build the Python wrapper.

Other implementations
=====================





==============================
EPICS Channel Access in Python 
==============================

The epics python package consists of several modules to interact with
EPICS.  The simplest approach uses the functions :func:`caget`,
:func:`caput`, :func:`camonitor`, :func:`camonitor_clear`, and
:func:`cainfo` within the top-level `epics` module.  These functions are
similar to the Unix command line utilities and to the EZCA library
interface, and described in more detail below.


The :mod:`epics` package consists of several functions, modules and classes
that are all imported with::

     import epics
    
These components includes

    * functions :func:`caget`, :func:`caput`, :func:`camonitor`,
      :func:`camonitor_clear`, and :func:`cainfo` as described below.
    * a :mod:`ca` module, providing the low-level Epics Channel Access
      library as a set of functions.
    * a :class:`PV` object, giving a higher-level interface to Epics
      Channel Access.
    * a :class:`Device` object:  a collection of related PVs
    * a :class:`Motor` object: a mapping of an Epics Motor
    * an :class:`Alarm` object, which can be used to set up notifications
      when a PV's values goes outside an acceptable bounds.
    * an :mod:`epics.wx` module that provides wxPython classes designed for
      use with Epics PVs.

Most users will probably want to create and use `PV` objects provided by
the `pv` module.  The `PV` class provides a PV object that has both methods
(including :func:`get` and :func:`put`) and attributes that are kept
automatically synchronized with the remote PV.

The lowest-level CA functionality is exposed in the `ca` and `dbr` module.
While  not necessarily intended for general use, this module does provide a
fairly complete wrapping of the basic EPICS CA library, and is quite
useable, if a little more verbose and C-like than using PV objects.

In addition, the `epics` package contains more specialized modules for
Epics motors, alarms, a host of other *devices* (collections of PVs), and a
set of wxPython widget classes for using EPICS PVs with wxPython.


Functions defined in :mod:`epics`: caget(), caput() and related functions
=========================================================================

.. module:: epics
   :synopsis: top-level epics module, and container for simplest CA functions

The simplest interface to EPICS Channel Access provides functions
:func:`caget`, :func:`caput`, as well as functions :func:`camonitor`,
:func:`camonitor_clear`, and :func:`cainfo`.  These are similar to the
EPICS command line utilities and to the functions in the EZCA library.
These all take the name of an Epics Process Variable (PV) as the first
argument.

:func:`caget`
~~~~~~~~~~~~~

..  function:: caget(pvname[, as_string=False])

  retrieves and returns the value of the named PV.

  :param pvname: name of Epics Process Variable
  :param as_string:  whether to return string representation of the PV value.
  :type as_string: True or False
 
The optional *as_string* argument tells the function to return the **string
representation** of the value.  The details of the string representation
depends on the variable type of the PV.  For integer (short or long) and
string PVs, the string representation is pretty easy: 0 will become '0',
for example..  For float and doubles, the internal precision of the PV is
used to format the string value.  For enum types, the name of the enum
state is returned.

For most array (waveform) records, the string representation will be
something like::

  <array size=128, type=int>

depending on the size and type of the waveform.  As an important special
case, CHAR waveforms will be turned to Python strings when *as_string* is
``True``.  This is to work around a painful limitation on the maximum
length (40 characters!) of EPICS strings which leads CHAR waveforms to be
used as longer strings::

    >>> from epics import caget, caput, cainfo
    >>> print caget('XXX:m1.VAL')
    1.200
   >>> print caget('XXX:dir')                                                                                                          
   array([ 84,  58,  92, 120,  97, 115,  95, 117, 115, 101, 114,  92,  77,
        97, 114,  99, 104,  50,  48,  49,  48,  92,  70,  97, 115, 116,
        77,  97, 112,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
         0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0])
   >>> print caget('XXX:dir',as_string=True)
   'T:\\xas_user\\March2010\\FastMap'


:func:`caput`
~~~~~~~~~~~~~

..  function:: caput(pvname,value[, wait=False[, timeout=60]])

  set the value of the named PV.  

  :param pvname: name of Epics Process Variable
  :param value:  value to send to  PV
  :param wait:  whether to wait until the processing has completed.
  :type wait: True or False
  :param timeout:  how long to wait (in seconds) for put to complete before giving up.
  :type timeout: double
  :rtype: integer

The optional *wait* argument tells the function to wait until the
processing completes.  This can be useful for PVs which take significant
time to complete, for example moving a physical motor.  The *timeout*
argument gives the maximum time to wait, in seconds.  The function will
return after this (approximate) time even if the :func:`caput` has not
completed.

This function returns 1 on success, and a negative number if the timeout
has been exceeded.

    >>> from import epics import caget, caput, cainfo
    >>> caput('XXX:m1.VAL',2.30)
    1  
    >>> caput('XXX:m1.VAL',-2.30, wait=True)
    ... waits a few seconds ...
    1  

:func:`cainfo`
~~~~~~~~~~~~~~

..  function:: cainfo(pvname[, print_out=True])

  prints (or returns as a string) an informational paragraph about the PV,
  including Control Settings.

  :param pvname: name of Epics Process Variable
  :param print_out:  whether to write results to standard output (otherwise the string is returned).
  :type print_out: True or False

With *print_out=False*, the paragraph will not
be printed, but returned.

    >>> from epics import caget, caput, cainfo
    >>> cainfo('XXX.m1.VAL')
    == XXX:m1.VAL  (double) ==
       value      = 2.3
       char_value = 2.3000
       count      = 1
       units      = mm
       precision  = 4
       host       = xxx.aps.anl.gov:5064
       access     = read/write
       status     = 1
       severity   = 0
       timestamp  = 1265996455.417 (2010-Feb-12 11:40:55.417)
       upper_ctrl_limit    = 200.0
       lower_ctrl_limit    = -200.0
       upper_disp_limit    = 200.0
       lower_disp_limit    = -200.0
       upper_alarm_limit   = 0.0
       lower_alarm_limit   = 0.0
       upper_warning_limit = 0.0
       lower_warning       = 0.0
       PV is monitored internally
       no user callbacks defined.
    =============================

:func:`camonitor`
~~~~~~~~~~~~~~~~~


..  function:: camonitor(pvname[, writer=None[, callback=None]])

  This `sets a monitor` on the named PV, and will print out (by default)
  the PV name, time, and value each time the value changes.  

  :param pvname: name of Epics Process Variable
  :param writer:  whether to write results to standard output (otherwise the string is returned).
  :type writer: None or a method that can take a string
  :param callback:  user-supplied function to receive result
  :type callback: None or callable


One can any function that can take a string as *writer*, such as the
`write` method of a file open for writing.  If left as ``None``, messages
of changes will be sent to :func:`sys.stdout.write`. For more complete
control, one can specify a *callback* function to be called on each change
event.  This callback should take keyword arguments for *pvname*, *value*,
and *char_value*.  See :ref:`pv-callbacks-label` for information on writing
callback functions for :func:`camonitor`.

:func:`camonitor_clear`
~~~~~~~~~~~~~~~~~~~~~~~

..  function:: camonitor_clear(pvname)

  clears a monitor set on the named PV by :func:`camonitor`.

  :param pvname: name of Epics Process Variable

   >>> import epics
   >>> fh = open('PV1.log','w')
   >>> epics.camonitor('XXX:DMM1Ch2_calc.VAL',writer=fh.write)
   >>> .... wait for changes ...
   >>> epics.camonitor_clear('XXX:DMM1Ch2_calc.VAL')
   >>> fh.close()
   >>> fh = open('PV1.log','r')
   >>> for i in fh.readlines(): print i[:-1]
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:40.536946 -183.5035
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:41.536757 -183.6716
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:42.535568 -183.5112
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:43.535379 -183.5466
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:44.535191 -183.4890
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:45.535001 -183.5066
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:46.535813 -183.5085
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:47.536623 -183.5223
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:48.536434 -183.6832


Motivation: Why another Python-Epics Interface?
================================================

First, Py-Epics3 is intended as an improvement over EpicsCA 2.1, and should
replace that older Epics-Python interface.  That version has performance
issues, especially when connecting to a large number of PVs, is not
thread-aware, and has become difficult to maintain for Windows and Linux.

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


Status and To-Do List
=====================

The Epics3 package is under active development.  The current status is that
most features are working well, and it is being used in some production
code, but more testing is needed, and this documentation needs improvement.

There are several desired features are left undone or unfinished:
 
 *  port CaChannel interface to use epics.ca

 *  improve documentation, examples, unit testing.

 *  test threading

 *  investigate retrieving array data for CTRL and TIME variants.

 *  are ca_array_expection events needed???

 *  add more "devices", including low-level epics records.

 *  port the Motor class to be a subclass of epics.Device.

 *  improve wx_motor.py to be a stand-alone app with:
     - dialog window to select a set of motors for an "instrument"
     - enable "save/restore" for named positions of all motors
       in an instrument, with options to prompt-for-restore and
       prompt-for-restore-per-motor.
     - config file per instrument to allow loading a saved
       instrument definition, with saved positions
     - tabbed/notebook interface for multiple instruments.




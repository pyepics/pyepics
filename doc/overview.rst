
============================================
Overview of EPICS Channel Access in Python
============================================

The python :mod:`epics` package consists of several function, modules, and
classes to interact with EPICS Channel Access.  The simplest approach uses
the functions :func:`caget`, :func:`caput`, :func:`cainfo`,
:func:`camonitor`, and :func:`camonitor_clear` within the top-level `epics`
module.  These functions are similar to the standard command line utilities
and to the EZCA library interface, and are described in more detail below.

To use the :mod:`epics` package, import it with::

     import epics

The main components of this module include

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

If you're looking to write quick scripts or a simple introduction to using
Channel Access, the :func:`caget` and :func:`caput` functions are probably
where you want to start.

If you're building larger scripts and programs, using :class:`PV` objects
provided by the :mod:`pv` module is recommended.  The :class:`PV` class
provides a Process Variable object that has both methods (including
:meth:`get` and :meth:`put`) to read and change the PV, and attributes that
are kept automatically synchronized with the remote channel.  For larger
applications, you may find the :class:`Device` class helpful.

The lowest-level CA functionality is exposed in the :mod:`ca` module, and
companion :mod:`dbr` module.  While not necessary recommended for most use
cases, this module does provide a fairly complete wrapping of the basic
EPICS CA library.  For people who have used CA from C or other languages,
this module should be familiar and seem quite usable, if a little more
verbose and C-like than using PV objects.

In addition, the `epics` package contains more specialized modules for
alarms, Epics motors, and several other *devices* (collections of PVs), and
a set of wxPython widget classes for using EPICS PVs with wxPython.

The `epics` package is targeted for use on Unix-like systems (including
Linux and Mac OS X) and Windows with Python versions 2.5, 2.6, 2.7, and
3.1, and 3.2.


Quick Start
=================

Whether you're familiar with Epics Channel Access or not, start here.
You'll then be able to use Python's introspection tools and built-in help
system, and the rest of this document as a reference and for detailed
discussions.

Functional Approach: caget(), caput()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get values from PVs, you can use the :func:`caget` function:

   >>> from epics import caget, caput
   >>> m1 = caget('XXX:m1.VAL')
   >>> print m1
   1.2001

To set PV values, you can use the :func:`caput` function:

   >>> caput('XXX:m1.VAL', 1.90)
   >>> print caget('XXX:m1.VAL')
   1.9000

For many cases, this approach is ideal because of its simplicity and
clarity.

Object Oriented Approach: PV
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to repeatedly access the same PV, you may find it more
convenient to ''create a PV object'' and use it in a more object-oriented
manner.

   >>> from epics import PV
   >>> pv1 = PV('XXX:m1.VAL')

PV objects have several methods and attributes.  The most important methods
are  :meth:`get` and :meth:`put` to receive and send the PV's value, and
the :attr:`value` attribute which stores the current value.  In analogy to
the :func:`caget` and :func:`caput` examples above, the value of a PV can
be fetched either with

   >>> print pv1.get()
   1.2001

or

   >>> print pv1.value
   1.2001

To set a PV's value, you can either use

   >>> pv1.put(1.9)

or assign the :attr:`value` attribute

   >>> pv1.value = 1.9

You can see a few of the most important properties of a PV by simply
printing it:

   >>> print pv1
   <PV 'XXX:m1.VAL', count=1, type=double, access=read/write>

Even more complete information can be seen by printing the PVs :attr:`info`
attribute::

   >>> print pv1.info
   == XXX:m1.VAL  (native_double) ==
      value      = 1.9
      char_value = '1.90000'
      count      = 1
      nelm       = 1
      type       = double
      units      = mm
      precision  = 5
      host       = somehost.cars.aps.anl.gov:5064
      access     = read/write
      status     = 0
      severity   = 0
      timestamp  = 1265996457.212 (2010-Feb-12 11:40:57.212)
      upper_ctrl_limit    = 12.5
      lower_ctrl_limit    = -12.3
      upper_disp_limit    = 12.5
      lower_disp_limit    = -12.3
      upper_alarm_limit   = 0.0
      lower_alarm_limit   = 0.0
      upper_warning_limit = 0.0
      lower_warning_limit = 0.0
      PV is internally monitored, with 0 user-defined callbacks:
   =============================

PV objects have several additional methods, especially related to
monitoring changes to the PVs and defining functions to be run when the
value does change.  There are also attributes associated with a PVs
*Control Attributes*, like those shown above in the :attr:`info` attribute.
Further details are at :ref:`pv-label`.


Functions defined in :mod:`epics`: caget(), caput(), etc.
========================================================================

.. module:: epics
   :synopsis: top-level epics module, and container for simplest CA functions

The simplest interface to EPICS Channel Access provides functions
:func:`caget`, :func:`caput`, as well as functions :func:`camonitor`,
:func:`camonitor_clear`, and :func:`cainfo`.  These functions are similar
to the EPICS command line utilities and to the functions in the EZCA
library.  They all take the name of an Epics Process Variable (PV) as the
first argument.  As with the EZCA library, the python implementation keeps
an internal cache of connected PV (in this case, using `PV` objects) so
that repeated use of a PV name will not actually result in a new
connection.  Thus, though the functionality is limited, the performance of
the functional approach can be quite good.

:func:`caget`
~~~~~~~~~~~~~

..  function:: caget(pvname[, as_string=False[, count=None[, as_numpy=True[, timeout=None[, use_monitor=False]]]]])

  retrieves and returns the value of the named PV.

  :param pvname: name of Epics Process Variable
  :param as_string:  whether to return string representation of the PV value.
  :type as_string:  ``True``/``False``
  :param count:  number of elements to return for array data.
  :type count:  integer or ``None``
  :param as_numpy:  whether to return the Numerical Python representation for array data.
  :type as_numpy:  ``True``/``False``
  :param timeout:  maximum time to wait (in seconds) for value before returning None.
  :type timeout:  float or ``None``
  :param use_monitor:  whether to rely on monitor callbacks or explicitly get value now.
  :type use_monitor: ``True``/``False``

The *count* and *as_numpy* options apply only to array or waveform
data. The default behavior is to return the full data array and convert to
a numpy array if available.  The *count* option can be used to explicitly
limit the number of array elements returned, and *as_numpy* can turn on or
off conversion to a numpy array.

The *timeout* argument sets the maximum time to wait for a value to be
fetched over the network.  If the timeout is exceeded, :func:`caget` will
return ``None``.  This might imply that the PV is not actually available,
but it might also mean that the data is large or network slow enough that
the data just hasn't been received yet, but may show up later.

The *use_monitor* argument sets whether to rely on the monitors from the
underlying PV.  The default is ``False``, so that each :func:`caget` will
explicitly ask the value to be sent instead of relying on the automatic
monitoring normally used for persistent PVs.  If this makes no sense,
leaving the default value of ``True`` is fine.  For more details on making
:func:`caget` more efficient, see :ref:`pv-automonitor-label` and
:ref:`advanced-get-timeouts-label`.

The *as_string* argument tells the function to return the **string
representation** of the value.  The details of the string representation
depends on the variable type of the PV.  For integer (short or long) and
string PVs, the string representation is pretty easy: 0 will become '0',
for example.  For float and doubles, the internal precision of the PV is
used to format the string value.  For enum types, the name of the enum
state is returned::

    >>> from epics import caget, caput, cainfo
    >>> print caget('XXX:m1.VAL')     # A double PV
    0.10000000000000001

    >>> print caget('XXX:m1.DESC')    # A string PV
    'Motor 1'
    >>> print caget('XXX:m1.FOFF')    # An Enum PV
    1

Adding the `as_string=True` argument always results in string being
returned, with the conversion method depending on the data type::

    >>> print caget('XXX:m1.VAL', as_string=True)
    '0.10000'

    >>> print caget('XXX:m1.FOFF', as_string=True)
    'Frozen'

For most array data from Epics waveform records, the regular value will be
a numpy array (or a python list if numpy is not installed).  The string
representation will be something like '<array size=128, type=int>'
depending on the size and type of the waveform.  An array of doubles might
be::

    >>> print caget('XXX:scan1.P1PA')  # A Double Waveform
    array([-0.08      , -0.078     , -0.076     , ...,
        1.99599814, 1.99799919,  2.     ])

    >>> print caget('XXX:scan1.P1PA', as_string=True)
    '<array size=2000, type=DOUBLE>'

As an important special case, CHAR waveforms will be turned to Python
strings when *as_string* is ``True``.  This is useful to work around the
low limit of the maximum length (40 characters!) of EPICS strings, and
means that it is fairly common to use CHAR waveforms when long strings are
desired::

    >>> print caget('XXX:dir')      # A CHAR waveform
    array([ 84,  58,  92, 120,  97, 115,  95, 117, 115,
       101, 114,  92,  77,  97, 114,  99, 104,  50,  48,
        49,  48,  92,  70,  97, 115, 116,  77,  97, 112])

    >>> print caget('XXX:dir',as_string=True)
    'T:\\xas_user\\March2010\\Fastmap'

Of course,character waveforms are not always used for long strings,  but
can also hold byte array data, such as comes from some detectors and
devices.

:func:`caput`
~~~~~~~~~~~~~~~~

..  function:: caput(pvname, value[, wait=False[, timeout=60]])

  set the value of the named PV.

  :param pvname: name of Epics Process Variable
  :param value:  value to send.
  :param wait:  whether to wait until the processing has completed.
  :type wait: ``True``/``False``
  :param timeout:  how long to wait (in seconds) for put to complete before giving up.
  :type timeout: double
  :rtype: integer

The optional *wait* argument tells the function to wait until the
processing completes.  This can be useful for PVs which take significant
time to complete, either because it causes a physical device (motor, valve,
etc) to move or because it triggers a complex calculation or data
processing sequence.  The *timeout* argument gives the maximum time to
wait, in seconds.  The function will return after this (approximate) time
even if the :func:`caput` has not completed.

This function returns 1 on success, and a negative number if the timeout
has been exceeded.

    >>> from epics import caget, caput, cainfo
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
  :param print_out:  whether to write results to standard output
                 (otherwise the string is returned).
  :type print_out: ``True``/``False``

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

  This `sets a monitor` on the named PV, which will cause *something* to be
  done each time the value changes.  By default the PV name, time, and
  value will be printed out (to standard output) when the value changes,
  but the action that actually happens can be customized.

  :param pvname: name of Epics Process Variable
  :param writer:  where to write results to standard output .
  :type writer: ``None`` or a callable function that takes a string argument.
  :param callback:  user-supplied function to receive result
  :type callback: ``None`` or callable function

One can specify any function that can take a string as *writer*, such as
the :meth:`write` method of an open file that has been open for writing.
If left as ``None``, messages of changes will be sent to
:func:`sys.stdout.write`. For more complete control, one can specify a
*callback* function to be called on each change event.  This callback
should take keyword arguments for *pvname*, *value*, and *char_value*.  See
:ref:`pv-callbacks-label` for information on writing callback functions for
:func:`camonitor`.

    >>> from epics import camonitor
    >>> camonitor('XXX.m1.VAL')
    XXX.m1.VAL 2010-08-01 10:34:15.822452 1.3
    XXX.m1.VAL 2010-08-01 10:34:16.823233 1.2
    XXX.m1.VAL 2010-08-01 10:34:17.823233 1.1
    XXX.m1.VAL 2010-08-01 10:34:18.823233 1.0


:func:`camonitor_clear`
~~~~~~~~~~~~~~~~~~~~~~~

..  function:: camonitor_clear(pvname)

  clears a monitor set on the named PV by :func:`camonitor`.

  :param pvname: name of Epics Process Variable

This simple example monitors a PV with :func:`camonitor` for while, with
changes being saved to a log file.   After a while, the monitor is cleared
and the log file is inspected::

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

PyEpics version 3 is intended as an improvement over EpicsCA 2.1, and
should replace that older Epics-Python interface.  That version had
performance issues, especially when connecting to a large number of PVs, is
not thread-aware, and has become difficult to maintain for Windows and
Linux.

There are a few other Python modules exposing Epics Channel Access
available.  Most of these have a interface to the CA library that was both
closer to the C library and lower-level than EpicsCA.  Most of these
interfaces use specialized C-Python 'wrapper' code to provide the
interface.

Because of this, an additional motivation for this package was to allow a
more common interface to be used that built higher-level objects (as
EpicsCA had) on top of a complete lower-level interface.  The desire to
come to a more universally-acceptable Python-Epics interface has definitely
influenced the goals for this module, which include:

   1) providing both low-level (C-like) and higher-level access (Pythonic
      objects) to the EPICS Channel Access protocol.
   2) supporting as many features of Epics 3.14 as possible, including
      preemptive callbacks and thread support.
   3) easy support and distribution for Windows and Unix-like systems.
   4) being ready for porting to Python3.
   5) using Python's ctypes library.

The main implementation feature used here (and difference from EpicsCA) is
using Python's ctypes library to handle the connection between Python and
the CA C library.  Using ctypes has many advantages.  Principally, it fully
eliminates the need to write (and maintain) wrapper code either with SWIG
or directly with Python's C API.  Since the ctypes module allows access to
C data and objects in pure Python, no compilation step is needed to build
the module, making installation and support on multiple platforms much
easier.  Since ctypes loads a shared object library at runtime, the
underlying Epics Channel Access library can be upgraded without having to
re-build the Python wrapper.  In addition, using ctypes provides the most
reliable thread-safety available, as each call to the underlying C library
is automatically made thread-aware without explicit code.  Finally, by
avoiding the C API altogether, migration to Python3 is greatly simplified.
PyEpics3 does work with both Python 2.* and 3.*.


Status and To-Do List
=======================

The PyEpics package is under active development.  The current status is
that most features are working well, and it is starting to be used in
production code, but more testing and better tests are needed.

The package is targeted and tested to work with Python 2.5, 2.6, 2.7, and
3.1 simultaneously (that is, the same code is meant to support all
versions).  Currently, the package works with Python 3.1, but is not
extremely well-tested.

There are several desired features are left undone or unfinished:

 * port CaChannel interface, ca_util, epicsPV (and other interfaces??) to use epics.ca

 * add more "devices", including low-level epics records.

 * incorporate some or all of the Channel Access Server from `pcaspy <http://code.google.com/p/pcaspy/>`_

 * build and improve applications.

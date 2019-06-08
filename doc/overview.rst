
============================================
PyEpics Overview
============================================

The python :mod:`epics` package provides several function, modules, and
classes to interact with EPICS Channel Access.  The simplest approach uses
the functions :func:`caget`, :func:`caput`, and :func:`cainfo` within the
top-level `epics` module to get and put values of Epics Process Variables.
These functions are similar to the standard command line utilities and the
EZCA library interface, and are described in more detail below.

To use the :mod:`epics` package, import it with::

     import epics

The main components of this module include

    * functions :func:`caget`, :func:`caput`, :func:`cainfo` and others
      described in more detail below.
    * a :mod:`ca` module, providing the low-level library as a set of
      functions, meant to be very close to the C library for Channel Access.
    * a :class:`PV` object, representing a Process Variable (PV) and giving
      a higher-level interface to Epics Channel Access.
    * a :class:`Device` object: a collection of related PVs, similar to an
      Epics Record.
    * a :class:`Motor` object: a Device that represents an Epics Motor.
    * an :class:`Alarm` object, which can be used to set up notifications
      when a PV's values goes outside an acceptable bounds.
    * an :mod:`epics.wx` module that provides wxPython classes designed for
      use with Epics PVs.

If you're looking to write quick scripts or a simple introduction to using
Channel Access, the :func:`caget` and :func:`caput` functions are probably
where you want to start.

If you're building larger scripts and programs, using :class:`PV` objects
is recommended.  The :class:`PV` class provides a Process Variable (PV)
object that has methods (including :meth:`get` and :meth:`put`) to read and
change the PV, and attributes that are kept automatically synchronized with
the remote channel.  For larger applications where you find yourself
working with sets of related PVs, you may find the :class:`Device` class
helpful.

The lowest-level CA functionality is exposed in the :mod:`ca` module, and
companion :mod:`dbr` module.  While not necessary recommended for most use
cases, this module does provide a fairly complete wrapping of the basic
EPICS CA library.  For people who have used CA from C or other languages,
this module should be familiar and seem quite usable, if a little more
verbose and C-like than using PV objects.

In addition, the `epics` package contains more specialized modules for
alarms, Epics motors, and several other *devices* (collections of PVs), and
a set of wxPython widget classes for using EPICS PVs with wxPython.

The `epics` package is supported and well-tested on Linux, Mac OS X, and
Windows with Python versions 2.7, and 3.5 and above.


Quick Start
=================

Whether you're familiar with Epics Channel Access or not, start here.
You'll then be able to use Python's introspection tools and built-in help
system, and the rest of this document as a reference and for detailed
discussions.

Procedural Approach: caget(), caput()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get values from PVs, you can use the :func:`caget` function:

    >>> from epics import caget, caput, cainfo
    >>> m1 = caget('XXX:m1.VAL')
    >>> print(m1)
    1.2001

To set PV values, you can use the :func:`caput` function:

    >>> caput('XXX:m1.VAL', 1.90)
    >>> print(caget('XXX:m1.VAL'))
    1.9000

To see more detailed information about a PV, use the :func:`cainfo`
function:

    >>> cainfo('XXX:m1.VAL')
    == XXX:m1.VAL  (time_double) ==
       value      = 1.9
       char_value = '1.9000'
       count      = 1
       nelm       = 1
       type       = time_double
       units      = mm
       precision  = 4
       host       = somehost.aps.anl.gov:5064
       access     = read/write
       status     = 0
       severity   = 0
       timestamp  = 1513352940.872 (2017-12-15 09:49:00.87179)
       posixseconds        = 1513352940.0
       nanoseconds= 871788105
       upper_ctrl_limit    = 50.0
       lower_ctrl_limit    = -48.0
       upper_disp_limit    = 50.0
       lower_disp_limit    = -48.0
       upper_alarm_limit   = 0.0
       lower_alarm_limit   = 0.0
       upper_warning_limit = 0.0
       lower_warning_limit = 0.0
       PV is internally monitored, with 0 user-defined callbacks:
    =============================

The simplicity and clarity of these functions make them ideal for many
uses.

Creating and Using PV Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are repeatedly referencing the same PV, you may find it more
convenient to create a PV object and use it in a more object-oriented
manner.

    >>> from epics import PV
    >>> pv1 = PV('XXX:m1.VAL')

PV objects have several methods and attributes.  The most important methods
are  :meth:`get` and :meth:`put` to receive and send the PV's value, and
the :attr:`value` attribute which stores the current value.  In analogy to
the :func:`caget` and :func:`caput` examples above, the value of a PV can
be fetched either with

    >>> print(pv1.get())
    1.90

or

    >>> print(pv1.value)
    1.90

To set a PV's value, you can either use

    >>> pv1.put(1.9)

or assign the :attr:`value` attribute

    >>> pv1.value = 1.9

You can see a few of the most important properties of a PV by simply
printing it:

    >>> print(pv1)
    <PV 'XXX:m1.VAL', count=1, type=time_double, access=read/write>

More complete information can be seen by printing the PVs :attr:`info`
attribute::

    >>> print(pv1.info)
    == XXX:m1.VAL  (time_double) ==
       value      = 1.9
       char_value = '1.9000'
       count      = 1
       nelm       = 1
       type       = time_double
       units      = mm
       precision  = 4
       host       = somehost.aps.anl.gov:5064
       access     = read/write
       status     = 0
       severity   = 0
       timestamp  = 1513352940.872 (2017-12-15 09:49:00.87179)
       posixseconds        = 1513352940.0
       nanoseconds= 871788105
       upper_ctrl_limit    = 50.0
       lower_ctrl_limit    = -48.0
       upper_disp_limit    = 50.0
       lower_disp_limit    = -48.0
       upper_alarm_limit   = 0.0
       lower_alarm_limit   = 0.0
       upper_warning_limit = 0.0
       lower_warning_limit = 0.0
       PV is internally monitored, with 0 user-defined callbacks:
    =============================

PV objects have several additional methods related to monitoring changes to
the PV values or connection state including user-defined functions to be
run when the value changes.  There are also attributes associated with a
PVs *Control Attributes*, like those shown above in the :attr:`info`
attribute.  Further details are at :ref:`pv-label`.


Functions defined in :mod:`epics`: caget(), caput(), etc.
========================================================================

.. module:: epics
   :synopsis: top-level epics module, and container for simplest CA functions

As shown above, the simplest interface to EPICS Channel Access is found
with the functions :func:`caget`, :func:`caput`, and :func:`cainfo`.  There
are also functions :func:`camonitor` and :func:`camonitor_clear` to setup
and clear a simple monitoring of changes to a PV.  These functions all take
the name of an Epics Process Variable (PV) as the first argument and are
similar to the EPICS command line utilities of the same names.

Internally, these functions keeps a cache of connected PV (in this case,
using `PV` objects) so that repeated use of a PV name will not actually
result in a new connection to the PV -- see :ref:`pv-cache-label` for more
details.  Thus, though the functionality is simple and straightforward, the
performance of using thes simple function can be quite good.  In addition,
there are also functions :func:`caget_many` and :func:`caput_many` for
getting and putting values for multiple PVs at a time.


:func:`caget`
~~~~~~~~~~~~~

..  function:: caget(pvname[, as_string=False[, count=None[, as_numpy=True[, timeout=None[, use_monitor=False]]]]])

  retrieves and returns the value of the named PV.

  :param pvname: name of Epics Process Variable.
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
monitoring normally used for persistent PVs.  This makes :func:`caget` act
more like command-line tools, and slightly less efficient than creating a
PV and getting values with it.  If performance is a concern, using monitors
is recommended.  For more details on making :func:`caget` more efficient,
see :ref:`pv-automonitor-label` and :ref:`advanced-get-timeouts-label`.

The *as_string* argument tells the function to return the **string
representation** of the value.  The details of the string representation
depends on the variable type of the PV.  For integer (short or long) and
string PVs, the string representation is pretty easy: 0 will become '0',
for example.  For float and doubles, the internal precision of the PV is
used to format the string value.  For enum types, the name of the enum
state is returned::

    >>> from epics import caget, caput, cainfo
    >>> print(caget('XXX:m1.VAL'))     # A double PV
    0.10000000000000001

    >>> print(caget('XXX:m1.DESC'))    # A string PV
    'Motor 1'
    >>> print(caget('XXX:m1.FOFF'))    # An Enum PV
    1

Adding the `as_string=True` argument always results in string being
returned, with the conversion method depending on the data type, for
example using the precision field of a double PV to determine how to format
the string, or using the names of the enumeration states for an enum PV::

    >>> print(caget('XXX:m1.VAL', as_string=True))
    '0.10000'

    >>> print(caget('XXX:m1.FOFF', as_string=True))
    'Frozen'

For integer or double array data from Epics waveform records, the regular
value will be a numpy array (or a python list if numpy is not installed).
The string representation will be something like '<array size=128,
type=int>' depending on the size and type of the waveform.  An array of
doubles might be::

    >>> print(caget('XXX:scan1.P1PA'))  # A Double Waveform
    array([-0.08      , -0.078     , -0.076     , ...,
        1.99599814, 1.99799919,  2.     ])

    >>> print(caget('XXX:scan1.P1PA', as_string=True))
    '<array size=2000, type=time_double>'

As an important special case CHAR waveform records will be turned to Python
strings when *as_string* is ``True``.  This is useful to work around the
low limit of the maximum length (40 characters!) of EPICS strings which has
inspired the fairly common usage of CHAR waveforms to represent longer
strings::

    >>> epics.caget('MyAD:TIFF1:FilePath')
    array([ 47, 104, 111, 109, 101,  47, 101, 112, 105,  99, 115,  47, 115,
            99, 114,  97, 116,  99, 104,  47,   0], dtype=uint8)
    >>> epics.caget('MyAD:TIFF1:FilePath', as_string=True)
    '/home/epics/scratch/'

Of course,character waveforms are not always used for long strings, but can
also hold byte array data, such as comes from some detectors and devices.

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
   >>> for i in fh.readlines(): print(i[:-1])
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:40.536946 -183.5035
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:41.536757 -183.6716
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:42.535568 -183.5112
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:43.535379 -183.5466
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:44.535191 -183.4890
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:45.535001 -183.5066
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:46.535813 -183.5085
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:47.536623 -183.5223
    XXX:DMM1Ch2_calc.VAL 2010-03-24 11:56:48.536434 -183.6832

:func:`caget_many`
~~~~~~~~~~~~~~~~~~

..  function:: caget_many(pvlist[, as_string=False[, count=None[, as_numpy=True[, timeout=None]]]])

  get a list of PVs as quickly as possible.  Returns a list of values for
  each PV in the list.  Unlike :func:`caget`, this method does not use
  automatic monitoring (see :ref:`pv-automonitor-label`).

  :param pvlist: A list of process variable names.
  :type pvlist:  ``list`` or ``tuple`` of ``str``
  :param as_string:  whether to return string representation of the PV values.
  :type as_string:  ``True``/``False``
  :param count:  number of elements to return for array data.
  :type count:  integer or ``None``
  :param as_numpy:  whether to return the Numerical Python representation for array data.
  :type as_numpy:  ``True``/``False``
  :param timeout:  maximum time to wait (in seconds) for value before returning None.
  :type timeout:  float or ``None``

For detailed information about the arguments, see the documentation for
:func:`caget`. Also see :ref:`advanced-connecting-many-label` for more
discussion.

:func:`caput_many`
~~~~~~~~~~~~~~~~~~

..  function:: caput_many(pvlist, values[, wait=False[, connection_timeout=None[, put_timeout=60]]])

  put values to a list of PVs as quickly as possible.  Returns a list of ints
  for each PV in the list: 1 if the put was successful, -1 if it timed out.
  Unlike :func:`caput`, this method does not use automatic monitoring (see
  :ref:`pv-automonitor-label`).

  :param pvlist: A list of process variable names.
  :type pvlist:  ``list`` or ``tuple`` of ``str``
  :param values: values to put to each PV.
  :type values: ``list`` or ``tuple``
  :param wait:  if ``'each'``, :func:`caput_many` will wait for each
    PV to process before starting the next.  If ``'all'``,
    :func:`caput_many` will issue puts for all PVs immediately, then
    wait for all of them to complete.  If any other value,
    :func:`caput_many` will not wait for put processing to complete.
  :param connection_timeout:  maximum time to wait (in seconds) for
    a connection to be established to each PV.
  :type connection_timeout:  float or ``None``
  :param put_timeout: maximum time to wait (in seconds) for processing
   to complete for each PV (if ``wait`` is ``'each'``), or for processing
   to complete for all PVs (if ``wait`` is ``'all'``).
  :type put_timeout: float or ``None``

Because connections to channels normally connect very quickly (less than a
second), but processing a put may take a significant amount of time (due to
a physical device moving, or due to complex calculations or data processing
sequences), a separate timeout duration can be specified for connections and
processing puts.


Motivation and design concepts
================================================

There are other Python wrappings for Epics Channel Access, so it it useful
to outline the design goals for PyEpics. The motivations for PyEpics3
included:

   1) providing both low-level (C-like) and higher-level access (Python
      objects) to the EPICS Channel Access protocol.
   2) supporting as many features of Epics 3.14 as possible, including
      preemptive callbacks and thread support.
   3) easy support and distribution for Windows and Unix-like systems.
   4) support for both Python 2 and Python 3.
   5) using Python's ctypes library.

The idea is to provide both a low-level interface to Epics Channel Access
(CA) that closely resembled the C interface to CA, and to build higher
level functionality and complex objects on top of that foundation.  The
Python ctypes library conveniently allows such direct wrapping of a shared
libraries, and requires no compiled code for the bridge between Python and
the CA library.  This makes it very easy to wrap essentially all of CA from
Python code, and support multiple platforms.  Since ctypes loads a shared
object library at runtime, the underlying CA library can be upgraded
without having to re-build the Python wrapper. The ctypes interface
provides the most reliable thread-safety available, as each call to the
underlying C library is automatically made thread-aware without explicit
code.  Finally, by avoiding the C API altogether, supporting both Python2
and Python3 is greatly simplified.

Status and to-do list
=======================

The PyEpics package is actively maintained, but the core library is
reasonably stable and ready to use in production code.  Features are being
added slowly, and testing is integrated into development so that the chance
of introducing bugs into existing codes is minimized.  The package is
targeted and tested to work with Python 2.7 and Python 3 simultaneously.

There are several desired features are left unfinished or could use
improvement:

 * add more Epics Devices, including low-level epics records and more
   suport for Area Detectors.

 * build and improve applications using PyEpics, especially for common data
   acquisition needs.

 * improve and extend the use of PyQt widgets with PyEpics.

If you are interested in working on any of these or other topics, please
contact the authors.

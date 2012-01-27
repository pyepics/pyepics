..  _pv-label:

==============================
PV: Epics Process Variables
==============================


.. module:: pv
   :synopsis: PV objects for Epics Channel Access

The :mod:`pv` module provides a higher-level class :class:`pv.PV`, which
creates a `PV` object for an EPICS Process Variable.  A `PV` object has
both methods and attributes for accessing it's properties.


The :class:`PV` class
=======================

.. class:: PV(pvname[, callback=None[, form='native'[, auto_monitor=None[, connection_callback=None[,  connection_timeout=None[, verbose=False]]]]]] )
   create a PV object for a named Epics Process Variable.

   :param pvname: name of Epics Process Variable
   :param callback:  user-defined callback function on changes to PV value or state.
   :type callback: callable, tuple, list or None
   :param form:  which epics *data type* to use:  the 'native' , or the 'ctrl' (Control) or 'time' variant.
   :type form: string, one of ('native','ctrl', or 'time')
   :param auto_monitor:  whether to automatically monitor the PV for changes.
   :type auto_monitor: ``None``, ``True``, ``False``, or bitmask (see :ref:`pv-automonitor-label`)
   :param connection_callback: user-defined function called on changes to PV connection status.
   :type connection_callback:  callable or ``None``
   :param connection_timeout:  time (in seconds) to wait for connection before giving up
   :type connection_timeout:  float or ``None``
   :param verbose:  whether to print out debugging messages
   :type verbose: ``True``/``False``

Once created, a PV should (barring any network issues) automatically
connect and be ready to use.

      >>> from epics import PV
      >>> p = PV('XX:m1.VAL')
      >>> print p.get()
      >>> print p.count, p.type


The *pvname* is required, and is the name of an existing Process Variable.

The *callback* parameter specifies one or more python methods to be called
on changes, as discussed in more detail at :ref:`pv-callbacks-label`

The *connection_callback* parameter specifies a python method to be called
on changes to the connection status of the PV (that is, when it connects or
disconnects).  This is discussed in more detail at :ref:`pv-connection_callbacks-label`

The *form* parameter specifies which of the three variants 'native' (the
default), 'ctrl' (Control) or 'time' to use for the PV.  The control and
time variants add additional fields to the PV, which can be useful in some
cases.  Also note that the additional 'ctrl' value fields (see the
:ref:`Table of Control Attributes <ctrlvars_table>`) can be obtained with
:meth:`get_ctrlvars` even for PVs of 'native' form.

The *auto_monitor* parameter specifies whether the PV should be
automatically monitored.  See :ref:`pv-automonitor-label` for a detailed
description of this.

The *verbose* parameter specifies more verbose output on changes, and is
intended for debugging purposes.



methods
~~~~~~~~

A `PV` has several methods for getting and setting its value and defining
callbacks to be executed when the PV changes.

.. method:: get([, count=None[, as_string=False[, as_numpy=True[, timeout=None[, use_monitor=True]]]]])

   get and return the current value of the PV

   :param count:  maximum number of array elements to return
   :type count:  integer or ``None``
   :param as_string:  whether to return the string representation of the  value.
   :type as_string: ``True``/``False``
   :param as_numpy:  whether to try to return a numpy array where appropriate.
   :type as_string: ``True``/``False``
   :param timeout:  maximum time to wait for data before returning ``None``.
   :type  timeout:  float or ``None``
   :param use_monitor:  whether to rely on monitor callbacks or explicitly get value now.
   :type use_monitor: ``True``/``False``

   see :ref:`pv-as-string-label` for details on how the string
   representation is determined.

   With the *as_numpy* option, an array PV (that is, a PV whose value has
   more than one element) will be returned as a numpy array, provided the
   numpy module is available.  See :ref:`advanced-large-arrays-label` for a
   discussion of strategies for how to best deal with very large arrays.

   The *use_monitor* option controls whether the most recent value from the automatic
   monitoring will be used or whether the value will be explicitly asked
   for right now.  Usually, you can rely on a PVs value being kept up to
   date, and so the default here is ``True``.  But, since network traffic
   is not instantaneous and hard to predict, the value returned with
   `use_monitor=True` may be out-of-date.

   The *timeout* sets how long (in seconds) to wait for the value to be
   sent.  This only applies with `use_monitor=False`, or if the PV is not
   automatically monitored.   Otherwise, the most recently received value
   will be sent immediately.

   See :ref:`pv-automonitor-label` for more on monitoring PVs and
   :ref:`advanced-get-timeouts-label` for more details on what happens when
   a :func:`pv.get` times out.


.. method:: put(value[, wait=False[, timeout=30.0[, use_complete=False[, callback=None[, callback_data=None]]]]])

   set the PV value, optionally waiting to return until processing has
   completed, or setting the :attr:`put_complete` to indicate complete-ness.

   :param value:  value to set PV
   :param wait:  whether to wait for processing to complete (or time-out) before returning.
   :type  wait:  ``True``/``False``
   :param timeout:  maximum time to wait for processing to complete before returning anyway.
   :type  timeout:  float
   :param use_complete:  whether to use a built-in callback to set :attr:`put_complete`.
   :type  use_complete:  ``True``/``False``
   :param callback: user-supplied function to run when processing has completed.
   :type callback: ``None`` or a valid python function
   :param callback_data: extra data to pass on to a user-supplied callback function.

The `wait` and `callback` arguments, as well as the 'use_complete' / :attr:`put_complete`
attribute give a few options for knowing that a :meth:`put` has
completed.   See :ref:`pv-putwait-label` for more details.

..  _pv-get-ctrlvars-label:

.. method:: get_ctrlvars()

   returns a dictionary of the **control values** for the PV.  This
   dictionary may have many members, depending on the data type of PV.  See
   the :ref:`Table of Control Attributes <ctrlvars_table>`  for details.

.. method:: poll([evt=1.e-4, [iot=1.0]])

   poll for changes.  This simply calls :meth:`ca.poll`

   :param evt:  time to pass to :meth:`ca.pend_event`
   :type  evt:  float
   :param iot:  time to pass to :meth:`ca.pend_io`
   :type  iot:  float

.. method:: connect([timeout=None])

   this explicitly connects a PV, and returns whether or not it has
   successfully connected.  It is probably not that useful, as connection
   should happen automatically. See :meth:`wait_for_connection`.

   :param timeout:  maximum connection time, passed to :meth:`ca.connect_channel`
   :type  timeout:  float
   :rtype:    ``True``/``False``

   if timeout is ``None``, the PVs connection_timeout parameter will be used. If that is also ``None``,
   :data:`ca.DEFAULT_CONNECTION_TIMEOUT`  will be used.

.. method:: wait_for_connection([timeout=None])

   this waits until a PV is connected, or has timed-out waiting for a
   connection.  Returns  whether the connection has occurred.

   :param timeout:  maximum connection time.
   :type  timeout:  float
   :rtype:    ``True``/``False``

   if timeout is ``None``, the PVs connection_timeout parameter will be used. If that is also ``None``,
   :data:`ca.DEFAULT_CONNECTION_TIMEOUT`  will be used.


.. method:: disconnect()

   disconnect a PV, clearing all callbacks.

.. method:: add_callback(callback=None[, index=None [, with_ctrlvars=True[, **kw]])

   adds a user-defined callback routine to be run on each change event for
   this PV.  Returns the integer *index*  for the callback.

   :param callback: user-supplied function to run when PV changes.
   :type callback: ``None`` or callable
   :param index: identifying key for this callback
   :param with_ctrlvars:  whether to (try to) make sure that accurate  ``control values`` will be sent to the callback.
   :type index: ``None`` (integer will be produced) or immutable
   :param kw: additional keyword/value arguments to pass to each execution of the callback.
   :rtype:  integer

   Note that multiple callbacks can be defined, each having its own index
   (a dictionary key, typically an integer).   When a PV changes, all the
   defined callbacks will be executed.  They will be called in order (by
   sorting  the keys of the :attr:`callbacks` dictionary)

   See also: :attr:`callbacks`  attribute, :ref:`pv-callbacks-label`

.. method:: remove_callback(index=None)

   remove a user-defined callback routine using supplied

   :param index: index of user-supplied function, as returned by :meth:`add_callback`,
        and also to key for  this callback in the  :attr:`callbacks` dictionary.
   :type index: ``None`` or integer
   :rtype:  integer

   If only one callback is defined an index=``None``, this will clear the
   only defined callback.

   See also: :attr:`callbacks`  attribute, :ref:`pv-callbacks-label`

.. method:: clear_callbacks()

   remove all user-defined callback routine.

.. method:: run_callbacks()

   execute all user-defined callbacks right now, even if the PV has not
   changed.  Useful for debugging!

   See also: :attr:`callbacks`  attribute, :ref:`pv-callbacks-label`

.. method:: run_callback(index)

   execute a particular user-defined callback right now, even if the PV
   has not changed.  Useful for debugging!

   See also: :attr:`callbacks`  attribute, :ref:`pv-callbacks-label`


attributes
~~~~~~~~~~

A PV object has many attributes, each associated with some property of the
underlying PV: its *value*, *host*, *count*, and so on.  For properties
that can change, the PV attribute will hold the latest value for the
corresponding property,  Most attributes are **read-only**, and cannot be
assigned to.  The exception to this rule is the :attr:`value` attribute.

.. attribute:: value

   The current value of the PV.

   **Note**: The :attr:`value` attribute can be assigned to.
   When read, the latest value will be returned, even if that means a
   :meth:`get` needs to be called.

   Assigning to :attr:`value` is equivalent to setting the value with the
   :meth:`put` method.

   >>> from epics import PV
   >>> p1 = PV('xxx.VAL')
   >>> print p1.value
   1.00
   >>> p1.value = 2.00

.. attribute:: char_value

   The string representation of the string, as described in :meth:`get`.

.. attribute:: status

   The PV status, which will be 1 for a Normal, connected PV.

.. attribute:: type

   string describing data type of PV, such as `double`, `float`, `enum`, `string`,
   `int`,  `long`, `char`, or one of the `ctrl` or `time` variants of these, which
   will be named `ctrl_double`, `time_enum`, and so on.  See the
   :ref:`Table of DBR Types <dbrtype_table>`


.. attribute:: ftype

  The integer value (from the underlying C library) indicating the PV data
  type according to :ref:`Table of DBR Types <dbrtype_table>`

.. attribute:: host

    string of host machine provide this PV.

.. attribute:: count

   number of data elements in a PV.  1 except for waveform PVs, where it
   gives the number of elements in the waveform. For recent versions of
   Epics Base (3.14.11 and later?), this gives the `.NORD` field, which
   gives the number of elements last put into the PV and which may be less
   than the maximum number allowed (see `nelm` below).

.. attribute:: nelm

   number of data elements in a PV.  1 except for waveform PVs where it
   gives the maximum number of elements in the waveform. For recent
   versions of Epics Base (3.14.11 and later?), this gives the `.NELM`
   parameter.  See also the `count` attribute above.

.. attribute:: read_access

   Boolean (``True``/``False``) for whether PV is readable

.. attribute:: write_access

   Boolean (``True``/``False``) for whether PV is writable

.. attribute:: access

   string describing read/write access.  One of
   'read/write','read-only','write-only', 'no access'.

.. attribute:: severity

   severity value of PV. Usually 0 for PVs that are not in an alarm
   condition.

.. attribute:: timestamp

   Unix (not Epics!!) timestamp of the last seen event for this PV.

.. attribute:: precision

   number of decimal places of precision to use for float and double PVs

.. attribute:: units

   string of engineering units for PV

.. attribute:: enum_strs

   a list of strings for the enumeration states  of this PV (for enum PVs)

.. attribute:: info

   a string paragraph (ie, including newlines) showing much of the
   information about the PV.

.. attribute:: upper_disp_limit

.. attribute:: lower_disp_limit

.. attribute:: upper_alarm_limit

.. attribute:: lower_alarm_limit

.. attribute:: lower_warning_limit

.. attribute:: upper_warning_limit

.. attribute:: upper_ctrl_limit

.. attribute:: lower_ctrl_limit

   These are all the various kinds of limits for a PV.

.. attribute:: put_complete

   a Boolean (``True``/``False``) value for whether the most recent
   :meth:`put`  has completed.

.. attribute:: callbacks

   a dictionary of currently defined callbacks, to be run on changes to the
   PV.  This dictionary has integer keys (generally in increasing order of
   when they were defined) which sets which order for executing the
   callbacks.  The values of this dictionary are tuples of `(callback,
   keyword_arguments)`.

   **Note**: The :attr:`callbacks` attribute can be assigned to or
    	  manipulated directly.  This is not recommended. Use the
          methods :meth:`add_callback`, :meth:`remove_callback`, and
          :meth:`clear_callbacks` instead of altering this dictionary directly.

.. attribute:: connection_callbacks

   a simple list of connection callbacks: functions to be run when the
   connection status of the PV changes. See
   :ref:`pv-connection_callbacks-label` for more details.

..  _pv-as-string-label:

String representation for a PV
================================

The string representation for a `PV`, as returned either with the
*as_string* argument to :meth:`ca.get` or from the :attr:`char_value`
attribute (they are equivalent) needs some further explanation.

The value of the string representation (hereafter, the :attr:`char_value`),
will depend on the native type and count of a `PV`.
:ref:`Table of String Representations <charvalue_table>`

.. _charvalue_table:

   Table of String Representations:  How raw data :attr:`value` is mapped
   to :attr:`char_value` for different native data types.

    =============== ========== ==============================
     *data types*    *count*     *char_value*
    =============== ========== ==============================
     string               1       = value
     char                 1      = value
     short                1      = str(value)
     long                 1      = str(value)
     enum                 1      = enum_str[value]
     double               1      = ("%%.%if" % (precision)) % value
     float                1      = ("%%.%if" % (precision)) % value
     char               > 1      = long string from bytes in array
     all others         > 1      = <array size=*count*, type=*type*>
    =============== ========== ==============================

For double/float values with large exponents, the formatting will be
`("%%.%ig" % (precision)) % value`.  For character waveforms (*char* data
with *count* > 1), the :attr:`char_value` will be set according to::

   >>> firstnull  = val.index(0)
   >>> if firstnull == -1: firstnull= len(val)
   >>> char_value = ''.join([chr(i) for i in val[:firstnull]).rstrip()

.. _pv-automonitor-label:

Automatic Monitoring of a PV
================================

When creating a PV, the *auto_monitor* parameter specifies whether the PV
should be automatically monitored or not.  Automatic monitoring means that
an internal callback will be registered for changes.  Any callbacks defined
by the user will be called by this internal callback when changes occur.

For most scalar-value PVs, this automatic monitoring is desirable, as the
PV will see all changes (and run callbacks) without any additional
interaction from the user. The PV's value will always be up-to-date and no
unnecessary network traffic is needed.

Possible values for :attr:`auto_monitor` are:

``False``
   For some PVs, especially those that change much more rapidly than you care
   about or those that contain large arrays as values, auto_monitoring can add
   network traffic that you don't need.  For these, you may wish to create
   your PVs with *auto_monitor=False*.  When you do this, you will need to
   make calls to :meth:`get` to explicitly get the latest value.

``None``
  The default value for *auto_monitor* is ``None``, and is set to
  ``True`` if the element count for the PV is smaller than 
  :data:`ca.AUTOMONITOR_MAXLENGTH` (default of 65536).  To suppress
  monitoring of PVs with fewer array values, you will have to explicitly
  turn *auto_monitor* to ``False``. For waveform arrays with more elements,
  automatic monitoring will not be done unless you explicitly set
  *auto_monitor=True*, or to an explicit mask.  See 
  :ref:`advanced-large-arrays-label` for more details.

``True``
  When *auto_monitor* is set to ``True``, the value will be monitored using
  the default subscription mask set at :data:`ca.DEFAULT_SUBSCRIPTION_MASK`.

  This mask determines which kinds of changes cause the PV to update. By
  default, the subscription updates when the PV value changes by more
  than the monitor deadband, or when the PV alarm status changes. This
  behavior is the same as the default in EPICS' *camonitor* tool.

*Mask*
  It is also possible to request an explicit type of CA subscription by
  setting *auto_monitor* to a numeric subscription mask made up of
  dbr.DBE_ALARM, dbr.DBE_LOG and/or dbr.DBE_VALUE. This mask will be
  passed directly to :meth:`ca.create_subscription` An example would be::

    pv1 = PV('AAA', auto_monitor=dbr.DBE_VALUE)
    pv2 = PV('BBB', auto_monitor=dbr.DBE_VALUE|dbr.DBE_ALARM)
    pv3 = PV('CCC', auto_monitor=dbr.DBE_VALUE|dbr.DBE_ALARM|dbr.DBE_LOG)

  which will generate callbacks for pv1 only when the value of 'AAA'
  changes, while pv2 will receive callbacks if the value or alarm state of
  'BBB' changes, and pv3 will receive callbacks for all changes to 'CCC'.
  Note that these dbr.DBE_**** constants are ORed together as a bitmask.

..  _pv-callbacks-label:

User-supplied Callback functions
================================

This section describes user-defined functions that are called when the
value of a PV changes.  These callback functions are useful as they allow
you to be notified of changes without having to continually ask for a PVs
current value.  Much of this information is similar to that in
:ref:`ca-callbacks-label` for the :mod:`ca` module, though there are some
important enhancements to callbacks on `PV` objects.

You can define more than one callback function per PV to be run on value
changes.  These functions can be specified when creating a PV, with the
*callback* argument which can take either a single callback function or a
list or tuple of callback functions.  After a PV has been created, you can
add callback functions with :meth:`add_callback`, remove them with
:meth:`remove_callback`, and explicitly run them with :meth:`run_callback`.
Each callback has an internal unique *index* (a small integer number) that
can be used for specifying which one to add, remove, and run.

When defining a callback function to be run on changes to a PV, it is
important to know two things:

    1)  how your function will be called.
    2)  what is permissible to do inside your callback function.

Callback functions will be called with several keyword arguments.  You
should be prepared to have them passed to your function, and should always
include `**kw` to catch all arguments.  Your callback will be sent the
following keyword parameters:

    * `pvname`: the name of the pv
    * `value`: the latest value
    * `char_value`: string representation of value
    * `count`: the number of data elements
    * `ftype`: the numerical CA type indicating the data type
    * `type`: the python type for the data
    * `status`: the status of the PV (1 for OK)
    * `precision`: number of decimal places of precision for floating point values
    * `units`:  string for PV units
    * `severity`: PV severity
    * `timestamp`: timestamp from CA server.
    * `read_access`: read access (``True``/``False``)
    * `write_access`: write access (``True``/``False``)
    * `access`: string description of  read- and write-access
    * `host`: host machine and CA port serving PV
    * `enum_strs`: the list of enumeration strings
    * `upper_disp_limit`: upper display limit
    * `lower_disp_limit`:  lower display limit
    * `upper_alarm_limit`:  upper alarm limit
    * `lower_alarm_limit`:  lower alarm limit
    * `upper_warning_limit`:  upper warning limit
    * `lower_warning_limit`:  lower warning limit
    * `upper_ctrl_limit`:  upper control limit
    * `lower_ctrl_limit`:  lower control limit
    * `chid`:  integer channel ID
    * `cb_info`:  (index, self) tuple containing callback ID
                  and the PV object

Some of these may not be directly applicable to all PV data types, and some
values may be ``None`` if the control parameters have not yet been fetched with
:meth:`get_ctrlvars`.

It is important to keep in mind that the callback function will be run
*inside* a CA function, and cannot reliably make any other CA calls.  It is
helpful to think "this all happens inside of a :func:`pend_event` call",
and in an epics thread that may or may not be the main thread of your
program.  It is advisable to keep the callback functions short and not
resource-intensive.  Consider strategies which use the callback only to
record that a change has occurred and then act on that change later --
perhaps in a separate thread, perhaps after :func:`pend_event` has
completed.

The `cb_info` parameter supplied to the callback needs special attention,
as it is the only non-Epics information passed.   The `cb_info` parameter
will be a tuple containing (:attr:`index`, :attr:`self`) where
:attr:`index` is the key for the :attr:`callbacks` dictionary for the PV
and :attr:`self` *is* PV object.  A principle use of this tuple is to
**remove the current callback**  if an error happens, as for example in GUI
code if the widget that the callback is meant to update disappears.

..  _pv-connection_callbacks-label:

User-supplied Connection Callback functions
=============================================

A *connection* callback is a user-defined function that is called when the
connection status of a PV changes -- that is, when a PV initially
connects, disconnects or reconnects due to the process serving the PV going
away, or loss of network connection.  A connection callback can be
specified when a PV is created, or can be added by appending to the
:attr:`connection_callbacks` list.  If there is more than one connection
callback defined, they will all be run when the connection state changes.

A connection callback should be prepared to receive the following keyword arguments:

    * `pvname`: the name of the pv
    * `conn`: the connection status

where *conn* will be either ``True` or ``False``, specifying whether the PV is
now connected.   A simple example is given below.


..  _pv-putwait-label:

Put with wait, put callbacks, and  put_complete
========================================================

Some EPICS records take a significant amount of time to fully process, and
sometimes you want to wait until the processing completes before going on.
There are a few ways to accomplish this.  First, one can simply wait until
the processing is done::

    import epics
    p = epics.PV('XXX')
    p.put(1.0, wait=True)
    print 'Done'

This will hang until the processing of the PV completes (motor moving, etc)
before printing 'Done'.   You can also specify a maximum time to wait -- a
*timeout* (in seconds)::

    p.put(1.0, wait=True, timeout=30)

which will wait up to 30 seconds.  For the pedantic, this timeout should
not be used as an accurate clock -- the actual wait time may be slightly
longer.

A second method is to use the 'use_complete' option and watch for the
:attr:`put_complete` attribute to become ``True`` after a :meth:`put`.  This is
somewhat more flexible than using `wait=True` as above, because you can more
carefully control how often you look for a :meth:`put` to complete, and
what to do in the interim.  A simple example would be::

    p.put(1.0, use_complete=True)
    waiting = True
    while waiting:
        time.sleep(0.001)
        waiting = not p.put_complete

An additional advantage of this approach is that you can easily wait for
multiple PVs to complete with python's built-in *all* function, as with::

    pvgroup = (epics.PV('XXX'), epics.PV('YYY'), epics.PV('ZZZ'))
    newvals = (1.0, 2.0,  3.0)
    for pv, val in zip(pvgroup, newvals):
        pv.put(val, use_complete=True)

    waiting = True
    while waiting:
        time.sleep(0.001)
        waiting = all(pv.put_complete for pv in pvgroup)
    print 'All puts are done!'

For maximum flexibility, one can all define a *put callback*, a function to
be run when the :meth:`put` has completed.   This function requires a
*pvname* keyword argument, but will receive no others, unless you pass in
data with the *callback_data* argument (which should be dict-like) to
:meth:`put`.   A simple example would be::

    pv = epics.PV('XXX')
    def onPutComplete(pvname=None, **kws):
        print 'Put done for %s' % pvname

    pv.put(1.0, callback=onPutComplete)


..  _pv-examples-label:

Examples
============

Some simple examples using PVs follow.

Basic Use
~~~~~~~~~~~~

The simplest approach is to simply create a PV and use its :attr:`value`
attribute:

   >>> from epics import PV
   >>> p1 = PV('xxx.VAL')
   >>> print p1.value
   1.00
   >>> p1.value = 2.00

The *print p1.value* line automatically fetches the current PV value.  The
*p1.value = 2.00* line does a :func:`put` to set the value, causing any
necessary processing over the network.

The above example is equivalent to

   >>> from epics import PV
   >>> p1 = PV('xxx.VAL')
   >>> print p1.get()
   1.00
   >>> p1.put(value = 2.00)

To get a string representation of the value, you can use either

   >>> print p1.get(as_string=True)
   '1.000'

or, equivalently

   >>> print p1.char_value
   '1.000'


Example of using info and more properties examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A PV has many attributes.  This can be seen from its *info* paragraph:

>>> import epics
>>> p = epics.PV('13IDA:m3')
>>> print p.info
== 13IDA:m3  (native_double) ==
   value      = 0.2
   char_value = '0.200'
   count      = 1
   type       = double
   units      = mm
   precision  = 3
   host       = ioc13ida.cars.aps.anl.gov:5064
   access     = read/write
   status     = 0
   severity   = 0
   timestamp  = 1274809682.967 (2010-05-25 12:48:02.967364)
   upper_ctrl_limit    = 5.49393415451
   lower_ctrl_limit    = -14.5060658455
   upper_disp_limit    = 5.49393415451
   lower_disp_limit    = -14.5060658455
   upper_alarm_limit   = 0.0
   lower_alarm_limit   = 0.0
   upper_warning_limit = 0.0
   lower_warning_limit = 0.0
   PV is internally monitored, with 0 user-defined callbacks:
=============================

The individual attributes can also be accessed as below.  Many of these
(the *control attributes*, see :ref:`Table of Control Attributes
<ctrlvars_table>`) will not be filled in until either the :attr:`info`
attribute is accessed or until :meth:`get_ctrlvars` is called.

>>>  print p.type
double
>>> print p.units, p.precision, p.lower_disp_limit
mm 3 -14.5060658455


Getting a string value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is not uncommon to want a string representation of a PVs value, for
example to show in a display window or to write to some report.  For string
PVs and integer PVs, this is a simple task.  For floating point values,
there is ambiguity how many significant digits to show. EPICS PVs all have
a :attr:`precision` field. which sets how many digits after the decimal
place should be described.  In addition, for ENUM PVs, it would be
desire able to get at the name of the ENUM state, not just its integer
value.

To get the string representation of a PVs value, use either the
:attr:`char_value` attribute or the `as_string=True` argument to :meth:`get`


Example of :meth:`put`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To put a new value to a variable, either of these two approaches can be
used:

>>> import epics
>>> p = epics.PV('XXX')
>>> p.put(1.0)

Or (equivalently):

>>> import epics
>>> p = epics.PV('XXX')
>>> p.value = 1.0

The :attr:`value` attribute is the only attribute that can be set.


Example of simple callback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is often useful to get a notification of when a PV changes.  In general,
it would be inconvenient (and possibly inefficient) to have to continually
ask if a PVs value has changed.  Instead, it is better to set a *callback*
function: a function to be run when the value has changed.

A simple example of this would be::

    import epics
    import time
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        print 'PV Changed! ', pvname, char_value, time.ctime()


    mypv = epics.PV(pvname)
    mypv.add_callback(onChanges)

    print 'Now wait for changes'

    t0 = time.time()
    while time.time() - t0 < 60.0:
        time.sleep(1.e-3)
    print 'Done.'

This first defines a *callback function* called `onChanges()` and then
simply waits for changes to happen.  Note that the callback function should
take keyword arguments, and generally use `**kw` to catch all arguments.
See :ref:`pv-callbacks-label` for more details.

Example of connection callback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A connection callback:

.. literalinclude:: ../tests/pv_connection_callback.py


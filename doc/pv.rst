..  _pv-label:

==============================
:mod:`epics.pv`  the PV object
==============================

Overview
========

.. module:: pv
   :synopsis: PV objects for Epics Channel Access

This module provides a higher-level class :class:`PV`, which creates a `PV`
object for an EPICS Process Variable.  A `PV` object has both methods and
attributes for accessing it's properties.


The :class:`PV` class
=======================

.. class:: PV(pvname[, callback=None[, connection_callback=None, [form='native'[, auto_monitor=None[, verbose=False]]]]])

   create a PV object for a named Epics Process Variable.  

   :param pvname: name of Epics Process Variable
   :param callback:  user-defined callback function on changes to PV value or state.
   :type callback: callable or None
   :param connection_callback:  user-defined function called on changes to PV connection status.
   :type connection_callback: callable or None
   :param form:  which epics *data type* to use:  the 'native' , or the 'ctrl' (Control) or 'time' variant.  
   :type form: string, one of ('native','ctrl', or 'time')
   :param auto_monitor:  whether to automatically monitor the PV for changes.
   :type auto_monitor: ``None``, ``True``, or ``False``
   :param verbose:  whether to print out debugging messages
   :type verbose: ``True``/``False``
   
Once created, a PV should (barring any network issues) automatically
connect and be ready to use. 

      >>> from epics import PV
      >>> p = PV('XX:m1.VAL')      
      >>> print p.get()   
      >>> print p.count, p.type


The *pvname* is required, and is the name of an existing Process Variable.

The *callback* parameter  specifies a python method to be called on changes,
as discussed in more detail at :ref:`pv-callbacks-label`

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

.. method:: get([, as_string=False[, as_numpy=True]])

   get and return the current value of the PV

   :param as_string:  whether to return the string representation of the  value.  
   :type as_string: ``True``/``False``
   :param as_numpy:  whether to try to return a numpy array where appropriate.
   :type as_string: ``True``/``False``

   see :ref:`pv-as-string-label` for details on how the string
   representation is determined.

   With the *as_numpy* option, an array PV (that is, a PV whose value has
   more than one element) will be returned as a numpy array, provided the
   numpy module is available.  See :ref:`advanced-large-arrays-label` for a
   discussion of strategies for how to best deal with very large arrays.

.. method:: put(value[, wait=False[, timeout=30.0[, callback=None[, callback_data=None]]]])

   set the PV value, optionally waiting to return until processing has
   completed. 

   :param value:  value to set PV 
   :param wait:  whether to wait for processing to complete (or time-out) before returning.
   :type  wait:  ``True``/``False``
   :param timeout:  maximum time to wait for processing to complete before returning anyway. 
   :type  timeout:  double
   :param callback: user-supplied function to run when processing has completed. 
   :type callback: ``None`` or a valid python function
   :param callback_data: extra data to pass on to a user-supplied callback function. 


..  _pv-get-ctrlvars-label:  

.. method:: get_ctrlvars()

   returns a dictionary of the **control values** for the PV.  This 
   dictionary may have many members, depending on the data type of PV.  See
   the :ref:`Table of Control Attributes <ctrlvars_table>`  for details.

.. method:: poll(evt=1.e-3, iot=1.0)

   this simply calls `ca.poll(evt=evt,iot=iot)` 

   :param evt:  time to pass to :meth:`ca.pend_event`
   :type  evt:  double
   :param iot:  time to pass to :meth:`ca.pend_io`
   :type  iot:  double

.. method:: connect(timeout=5.0, force=True)
 
   this explicitly connects a PV, and returns whether or not it has
   successfully connected.

   :param timeout:  maximum connection time, passed to :meth:`ca.connect_channel`
   :type  timeout:  double
   :param force:  whether to (try to) force a connect, passed to :meth:`ca.connect_channel`
   :type  force:  ``True``/``False``
   :rtype:    ``True``/``False``
   
.. method:: add_callback(callback=None[, index=None , [**kw]])
 
   adds a user-defined callback routine to be run on each change event for
   this PV.  Returns the integer *index*  for the callback.

   :param callback: user-supplied function to run when PV changes.
   :type callback: None or callable
   :param index: identifying key for this callback 
   :type index:: None (integer will be produced) or immutable
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
   :type index: None or integer
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

   number of data elements in a PV.  1 except for waveform PVs

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
     string                1         = value   
     char                  1         = value   
     short                 1         = str(value) 
     long                  1         = str(value)
     enum                1         = enum_str[value]
     double              1         = ("%%.%if" % (precision)) % value
     float                  1         = ("%%.%if" % (precision)) % value 
     char                > 1       = long string from bytes in array
     all others        > 1       = <array size=*count*, type=*type*>
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

For some PVs, especially those that change much more rapidly than you care
about or those that contain large arrays as values, auto_monitoring can add
network traffic that you don't need.  For these, you may wish to create
*your PVs with *auto_monitor=False*.  When you do this, you will need to
make calls to :meth:`get` to explicitly get the latest value.

The default value for *auto_monitor* is ``None``, and is set to ``True`` if
the element count for the PV is smaller than 16384 (The value is set as
:data:`ca.AUTOMONITOR_MAXLENGTH`).  To suppress monitoring of PVs with
fewer array values, you will have to explicitly turn *auto_monitor* to
``False``. For waveform arrays larger than 16384 items, automatic
monitoring will be ``False`` unless you explicitly set it to ``True``.  See
:ref:`advanced-large-arrays-label` for more details.

..  _pv-callbacks-label:

User-supplied Callback functions
================================

This section describes user-defined functions that are called when the
value of a PV changes.  These callback functions are useful as they allow
you to be notified of changes without having to continually ask for a PVs
current value.  Much of this information is similar to that in
:ref:`ca-callbacks-label` for the :mod:`ca` module, though there are some
important enhancements to callbacks on `PV` objects.

When defining a callback function to be run on changes to a PV, as set from
:meth:`add_callback`, it is important to know two things:

    1)  how your function will be called.
    2)  what is permissible to do inside your callback function.

Callback functions will be called with several keyword arguments.  You should be
prepared to have them passed to your function, and should always include
`**kw`  to catch all arguments.  Your callback will be sent the following 
keyword parameters:

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
    * `read_access`: read access (`True` or `False`)
    * `write_access`: write access (`True` or `False`)
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
values may be None if the control parameters have not yet been fetched with 
:meth:`get_ctrlvars`.  

Note that a the user-supplied callback will be run *inside* a CA function,
and cannot reliably make any other CA calls.  It is helpful to think "this
all happens inside of a :func:`pend_event` call", and in an epics thread
that may or may not be the main thread of your program.  It is advisable to
keep the callback functions short and not resource-intensive.  Consider
strategies which use the callback only to record that a change has occurred
and then act on that change later -- perhaps in a separate thread, perhaps
after :func:`pend_event` has completed.

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
away, or loss of network connection.  Currently, a connection callback must
be specified when a PV is created.

Such a connection callback should be prepared to receive the following
keyword arguments:

    * `pvname`: the name of the pv 
    * `conn`: the connection status

where *conn* will be either `True` or `False`, specifying whether the PV is
now connected.   A simple example is given below.


..  _pv-examples-label:

Examples
=========

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

or, equivilently 

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
desireable to get at the name of the ENUM state, not just its integer
value.

To get the string representation of a PVs value, use either the
:attr:`char_value` attribute or the *as_string=True* argument to :meth:`get`

 
Example of put
~~~~~~~~~~~~~~~~

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

Example of put with wait
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some EPICS records take a significant amount of time to fully process.  And
sometimes you want to wait until the processing completes before going on::

    import epics
    p = epics.PV('XXX')
    p.put(1.0, wait=True)
    print 'Done'

This will wait until the processing completes (motor moving, etc) before
printing 'Done'.   You can also specfy a maximum time to wait -- a
*timeout* (in seconds)::

    p.put(1.0, wait=True, timeout=30)

which will wait up to 30 seconds.  For the pedantic, this timeout should
not be used as an accurate clock -- the actual wait time may be slightly
longer.


Example of simple callback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is ofen useful to get a notification of when a PV changes.  In general,
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



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


The PV class
============

.. class:: PV(pvname[, callback=None[, form='native'[, auto_monitor=True[, verbose=False]]]])

   :param pvname: name of Epics Process Variable
   :param callback:  user-defined callback function on changes to PV value or state.
   :type callback: callable or None
   :param form:  which epics *data type* to use:  the 'native' , or the 'ctrl' (Control) or 'time' variant.  
   :type form: string, one of ('native','ctrl', or 'time')
   :param verbose:  whether to print out debugging messages
   :type auto_monitor: True or False
   
create a PV object for a named Epics Process Variable.  Once created, a PV
will (eventually) automatically connect and be ready to use.

      >>> from epics import PV
      >>>p = PV(pv_name)      
      >>>print p.get()   
      >>>print p.count, p.type

methods
~~~~~~~~

A `PV` has several methods for getting and setting its value and defining
callbacks to be executed when the PV changes.

.. method:: get([, as_string=False])

   get and return the current value of the PV

   :param as_string:  whether to return the string representation of the  value.  
   :type as_string:  True/False

   see :ref:`pv-as-string-label` for details on how the string representation
   is determined.

.. method:: put(value[, wait=False[, timeout=30.0[, callback=None[, callback_data=None]]]])

   set the PV value, optionally waiting to return until processing has
   completed. 

   :param value:  value to set PV 
   :param wait:  whether to wait for processing to complete (or time-out) before returning.
   :type  wait:  True/False
   :param timeout:  maximum time to wait for processing to complete before returning anyway. 
   :type  timeout:  double
   :param callback: user-supplied function to run when processing has completed. 
   :type callback: None or callable
   :param callback_data: extra data to pass on to a user-supplied callback function. 

.. method:: get_ctrlvars()

   returns a dictionary of the **control values** for the PV.  This 
   dictionary may have many members, depending on the data type of PV.  See
   the :ref:`Table of Control Attributes <ctrlvars_table>`  for details.


.. method:: poll(ev=1.e-4, io=1.0)

   this simply calls `ca.poll(ev=ev,io=io)` 

   :param ev:  time to pass to :meth:`ca.pend_event`
   :type  ev:  double
   :param io:  time to pass to :meth:`ca.pend_io`
   :type  io:  double

.. method:: connect(timeout=5.0, force=True)
 
   this explicitly connects a PV, and returns whether or not it has
   successfully connected.

   :param timeout:  maximum connection time, passed to :meth:`ca.connect_channel`
   :type  timeout:  double
   :param force:  whether to (try to) force a connect, passed to :meth:`ca.connect_channel`
   :type  force:  True/False
   :rtype:    True/False
   
.. method:: add_callback(callback=None[. **kw])
 
   adds a user-defined callback routine to be run on each change event for
   this PV.  Returns the integer *index*  for the callback.

   :param callback: user-supplied function to run when PV changes.
   :type callback: None or callable
   :param kw: additonal keyword/value arguments to pass to each execution of the callback.
   :rtype:  integer

   Note that multiple callbacks can be defined.  When a PV changes, all callbacks will be
   executed in the order of their indices.  

   See also: :attr:`callbacks`  attribute, :ref:`pv-callbacks-label`

.. method:: remove_callback(index=None)

   remove a user-defined callback routine.

   :param index: index of user-supplied function, as returned by  :meth:`add_callback`, and also to key value for this callback in the  :attr:`callbacks` dictionary.
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

   boolean (True/False) for whether PV is readable

.. attribute:: write_access

   boolean (True/False) for whether PV is writeable

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

   **Note**: The :attr:`callbacks` attribute can be assigned to.  It is
   recommended to use the methods :meth:`add_callback`,
   :meth:`remove_callback`, and :meth:`clear_callbacks` instead of altering
   this dictionary directly.

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
     string           1         = value   
     char             1         = value   
     short            1         = str(value) 
     long             1         = str(value)
     enum             1         = enum_str[value]
     double           1         = ("%%.%if" % (precision)) % value
     float            1         = ("%%.%if" % (precision)) % value 
     char             > 1       = long string from bytes in array
     all others       > 1       = <array size=*count*, type=*type*>
    =============== ========== ==============================

For double/float values with large exponents, the formatting will be 
`("%%.%ig" % (precision)) % value`.    

For character waveforms (*char* data with *count* > 1), the
:attr:char_value will be set from

   >>> firstnull  = val.index(0)
   >>> if firstnull == -1: firstnull= len(val)
   >>> char_value = ''.join([chr(i) for i in val[:firstnull]).rstrip()

..  _pv-callbacks-label:

User-supplied Callback functions
================================

Much of this information is similar to that in :ref:`ca-callbacks-label`
for the :mod:`ca` module, though there are some important enhancements to
callbacks on `PV` objects.

When defining a callback function to be run on changes to a PV, as set from
:meth:`add_callback`, it is important to know two things:

    1)  how your function will be called.
    2)  what is permissable to do inside your callback function.

Callback functions will be called with several keyword arguments.  You should be
prepared to have them passed to your function, and should always include
`**kw`  to catch all arguments.  Your callback will be sent the following 
keyword parameters:

    * `pvname`: the name of the pv 
    * `value`: the latest value
    * `char_value`: string representation of value
    * `count`: the number of data elements
    * `ftype`: the numerical CA type indicating the data type
    * `status`: the status of the PV (1 for OK)
    * `precision`: number of decimal places of precision.
    * `units`:  string for PV units
    * `severity`: PV severity
    * `timestamp`: timestamp from CA server.
    * `enum_strs`: the list of enumeration strings
    * `upper_disp_limit`: 
    * `lower_disp_limit`: 
    * `upper_alarm_limit`: 
    * `lower_alarm_limit`: 
    * `upper_warning_limit`: 
    * `lower_warning_limit`: 
    * `upper_ctrl_limit`: 
    * `lower_ctrl_limit`: 

Some of these may not be directly applicable to all PV data types.

Note that a user-supplied callback will be run 'inside' a CA function, and
cannot reliably make any other CA calls.  It is helpful to think 'this all
happens inside of a pend_event call', and in an epics thread that may or
may not be the main thread of your program.  It is advisable to keep the
callback functions short, not resource-intensive, and to consider
strategies which use the callback to record that a change has occurred and
then act on that change outside of the callback (perhaps in a separate
thread, perhaps after pend_event() has completed, etc).

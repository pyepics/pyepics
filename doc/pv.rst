==============================
:mod:`epics.pv`  the PV object
==============================

Overview
========

.. module:: pv
   :synopsis: PV objects for Epics Channel Access

This module provides a higher-level class :class:`PV`, which creates a `PV`
object for an EPICS Process Variable.



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
~~~~~~~

.. method:: get([, as_string=False])

.. method:: put(value[, wait=False[, timeout=30.0[, callback=None[, callback_data=None]]]])

.. method:: get_ctrlvars()

.. method:: poll()

.. method:: connect()

.. method:: add_callback(callback=None[. **kw])

.. method:: remove_callback(index=None)

.. method:: clear_callbacks()

.. method:: run_callbacks()

attributes
~~~~~~~~~~

A PV object has many attributes.  Most of these are actually implemented as
Python properties, and so except as explicitly noted, these attributes
cannot be assigned to.

.. attribute:: value 

   The current value of the PV.

   **Important Note**: The :attr:`value` attribute can be assigned to.
   When read, the latest value will be returned, even if that means a
   :meth:`get` needs to be called.

   Assigning to :attr:`value` is equivalent to setting the value with the
   :meth:`put` method.

.. attribute:: char_value

   The string representation of the string, as described in :meth:`get`.

.. attribute:: status

   The PV status, which will be 1 for a Normal, connected PV.

.. attribute:: type
  
   string describing data type of PV, such as 'double', 'enum', 'string',
   'long', 'char', 'ctrl_short', and so on.

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


.. attribute:: timestamp

.. attribute:: precision

.. attribute:: units

.. attribute:: enum_strs

.. attribute:: no_str

.. attribute:: upper_disp_limit

.. attribute:: lower_disp_limit

.. attribute:: upper_alarm_limit

.. attribute:: lower_alarm_limit

.. attribute:: lower_warning_limit

.. attribute:: upper_warning_limit

.. attribute:: upper_ctrl_limit

.. attribute:: lower_ctrl_limit

.. attribute:: info
        
..  _pv-callbacks-label:

User-supplied Callback functions
================================

Much of this information is similar to that in ref:`ca-callbacks-label`.  

User-supplied callback functions can be provided for both :meth:`put` and
:meth:create_subscription()

For both cases, it is important to keep two things in mind:
   how your function will be called
   what is permissable to do inside your callback function.


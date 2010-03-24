===========================
pv module and the PV object
===========================

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




        
..  _pv-callbacks-label:

User-supplied Callback functions
================================

Much of this information is similar to that in ref:`ca-callbacks-label`.  

User-supplied callback functions can be provided for both :meth:`put` and
:meth:create_subscription()

For both cases, it is important to keep two things in mind:
   how your function will be called
   what is permissable to do inside your callback function.


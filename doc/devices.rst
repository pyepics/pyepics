====================================
:mod:`epics.devices`   Epics Devices
====================================

Overview
========

.. module:: device
   :synopsis: collections of related PVs

This module provides a simple interface to a collection of PVs.  Here a
*device* holds a set of PVs, all sharing a prefix, but having many
*attributes*.  Many PVs will have names made up of *prefix+attribute*, with
a common prefix for several related PVs.  This almost describes an Epics
Record, but as it is concerned only with PV names, the mapping to an Epics
Record is not exact.  On the other hand, the concept of a *device* is more
flexible than a predefined Epics Record as it can actually hold PVs from
several different records.::

      mymotor1 = epics.Device('XXX:motor1.',
                              attr=('VAL','RBV','DESC',
                                    'RVAL','LVIO', 'HLS','LLS'))
      mymotor1.put('VAL',1)
      print ' %s at %f' % ( mymotor1.put('DESC'),  mymotor1.get('RBV'))

While useful on its own like this, the real point of a *device* is as a
base class, to be inherited and extended.

The attribute PVs are built as needed and held in an internal
buffer (self._pvs).  This class is kept intentionally simple
so that it may be subclassed.

To pre-load attribute names on initialization, provide a list or tuple of attributes.

The prefix is actually optional.  Wwhen left off, this class can be used as
an arbitrary container of PVs, or to turn any subclass into an epics
Device:

      >>> class MyDEV(epics.Device):
      ...     def __init__(self,**kw):
      ...         epics.Device.__init__() # no Prefix!!
      ...
      >>> x = MyDEV()
      >>> p1 = x.PV('13IDC:m1.VAL')
      >>> x.put('13IDC:m1.VAL', 2)
      >>> print x.PV('13IDC:m3.DIR').get(as_string=True)

.. class:: Device(prefix=None[, attrs=None])

.. method:: PV(attr):

   returns a `PV` object for a device attribute


.. method::  put(attr,value[,wait=False[,timeout=10.0]])

   put an attribute value, optionally wait for completion or up to a
   supplied timeout value

.. method::  get(attr[,as_string=False])

   get an attribute value, option as_string returns a string
   representation

.. method:: add_callback(attr,callback)

   add a callback function to an attribute PV, so that the callback
   function will be run when the attribute's value changes
        
.. function:: pv_property(attr[, as_string=False[,wait=False[,timeout=10.0]]])

   function to turn a device attribute PV into a Python **property**
   use in your subclass as:
        
   >>> class MyDevice(epics.device):
   >>>     def __init__(self,prefix):
   >>>         epics.Device.__init__(self)
   >>>         self.PV('something')
   >>>     field = pv_property('something', as_string=True)

   then use in code as

   >>> m = MyDevice()
   >>> print m.field
   >>> m.field = new_value

Examples
==========

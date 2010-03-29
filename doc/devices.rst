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

    motor1 = epics.Device('XXX:motor1.', attr=('VAL', 'RBV', 'DESC', 'RVAL',
                                               'LVIO', 'HLS', 'LLS'))
    motor1.put('VAL',1)
    print 'Motor %s = %f' % ( mymotor1.get('DESC'),  mymotor1.get('RBV'))

While useful on its own like this, the real point of a *device* is as a
base class, to be inherited and extended.

.. class:: Device(prefix=None[, attrs=None])

The attribute PVs are built as needed and held in an internal
buffer (self._pvs).  This class is kept intentionally simple
so that it may be subclassed.

To pre-load attribute names on initialization, provide a list or tuple of attributes.

Note that *prefix* is actually optional.  When left off, this class can be
used as an arbitrary container of PVs, or to turn any subclass into an
epics Device.


.. method:: PV(attr)

   returns the `PV` object for a device attribute

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
   use in your subclass as::
        
       class MyDevice(epics.device):
           def __init__(self,prefix):
               epics.Device.__init__(self)
               self.PV('something')
           field = pv_property('something', as_string=True)

   then use in code as::

       m = MyDevice()
       print m.field
       m.field = new_value

.. data:: _pvs
  
   a dictionary of PVs making up the device.

Examples
==========

Device without a prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a simple device without a prefix, containing aribitrary PVs::

    from epics import Device
    dev = Device()
    p1 = dev.PV('13IDC:m1.VAL')
    dev.put('13IDC:m1.VAL', 2)
    print dev.PV('13IDC:m3.DIR').get(as_string=True)

Epics ai record as Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a slightly more useful example: An Epics ai (analog input record)
implemented as a Device. 

.. literalinclude:: ../lib/devices/ai.py

which can be used as::

    
    This_ai = ai('XXX.PRES')
    print This_ai.get('VAL')


Epics Scaler Record as Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

And now a more complicated example: an incomplete (but useful) mapping of
the Scaler Record from synApps, including methods for changing modes,
and reading and writing data. 

.. literalinclude:: ../lib/devices/scaler.py



====================================
:mod:`epics.devices`   Epics Devices
====================================

Overview
===========

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
base class, to be inherited and extended.  In fact, there is a more
sophisticated   Motor device described below at :ref:`device-motor-label`

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
   function will be run when the at tribute's value changes
        
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

.. _device-motor-label:

Epics Motor Device
===========================


.. module:: motor

The Epics Motor record has over 100 fields associated with it.  Of course,
it is often preferrable to think of 1 Motor with many attributes than 100
or so separate PVs.  In addition, while there are many interrelated fields
of the Motor record, the user typically just wants to move the motor by
setting its drive position.  Of course, there are limits on the range of
motion that need to be respected and notifications sent when they are
violated.  Thus, there is a fair amount of functionality for a Motor.

The class:`Motor` class helps you create and use Epics motors.
A simple example use would be::

    import epics
    m1 = epics.Motor('XXX:m1')

    print 'Motor:  ', m1.description , ' Currently at ', m1.readback
   
    m1.tweak_val = 0.10
    m1.move(0.0, dial=True, wait=True)

    for i in range(10):
        m1.tweak(dir='forward', wait=True)
	time.sleep(1.0)
        print 'Motor:  ', m1.description , ' Currently at ', m1.readback

Which will step the motor through a set of positions.    You'll notice a
few features for Motor:

1.  Motors use english-name attributes for fields of the motor record.  Thus '.VAL' becomes 'drive' and '.DESC' becomes  description. 

2.  The methods for setting positions can use the User, Dial, or Step coordinate system, and can wait for completion.



The `epics.Motor` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. class:: Motor(pvname[, timeout=30.])

   create a Motor object for a named Epics Process Variable.  

   :param pvname: prefix name (no '.VAL' needed!) of Epics Process Variable  for a Motor
   :type pvname: string
   :param timeout:  time (in seconds) to wait befoe giving up trying to connect.
   :type timeout: float
   
Once created, a Motor should be ready to use.  

      >>> from epics import Motor
      >>> m = Motor('XX:m1')
      >>> print m.drive, m.description, m.slew_speed
      1.030 Fine X 5.0
      >>> print m.get_field('device_type', as_string=True)
      'asynMotor'


A Motor has very many fields.  Only a few of them are created on
initialization -- the rest are retrieved as needed.  The motor fields can
be retrieved either with an attribute or with the :meth:`get_field` method.
A full list of Motor attributes and their mapping to fields from the motor
record is given in :ref:`Table of Motorl Attributes <motorattr_table>`.

.. _motorattr_table: 

   Table of Attributes for the epics class:`Motor` class, and the
   corresponding field to the Epics Motor Record.

    ==================== ==============================
     *attribute*           *Epics Motor Record field*
    ==================== ==============================
     enabled                 _able.VAL               
     acceleration            .ACCL
     back_accel              .BACC
     backlash                .BDST
     back_speed              .BVEL
     card                    .CARD
     dial_high_limit         .DHLM
     direction               .DIR            
     dial_low_limit          .DLLM
     settle_time             .DLY
     done_moving             .DMOV
     dial_readback           .DRBV
     description             .DESC
     dial_drive              .DVAL
     units                   .EGU
     encoder_step            .ERES
     freeze_offset           .FOFF
     move_fraction           .FRAC
     hi_severity             .HHSV
     hi_alarm                .HIGH
     hihi_alarm              .HIHI
     high_limit              .HLM
     high_limit_set          .HLS
     hw_limit                .HLSV
     home_forward            .HOMF
     home_reverse            .HOMR
     high_op_range           .HOPR
     high_severity           .HSV
     integral_gain           .ICOF
     jog_accel               .JAR
     jog_forward             .JOGF
     jog_reverse             .JOGR
     jog_speed               .JVEL
     last_dial_val           .LDVL
     low_limit               .LLM
     low_limit_set           .LLS
     lo_severity             .LLSV
     lolo_alarm              .LOLO
     low_op_range            .LOPR
     low_alarm               .LOW
     last_rel_val            .LRLV
     last_dial_drive         .LRVL
     last_SPMG               .LSPG
     low_severity            .LSV
     last_drive              .LVAL
     soft_limit              .LVIO
     in_progress             .MIP
     missed                  .MISS
     moving                  .MOVN
     resolution              .MRES
     motor_status            .MSTA
     offset                  .OFF
     output_mode             .OMSL
     output                  .OUT
     prop_gain               .PCOF
     precision               .PREC
     readback                .RBV
     retry_max               .RTRY
     retry_count             .RCNT
     retry_deadband          .RDBD
     dial_difference         .RDIF
     raw_encoder_pos         .REP
     raw_high_limit          .RHLS
     raw_low_limit           .RLLS
     relative_value          .RLV
     raw_motor_pos           .RMP
     raw_readback            .RRBV
     readback_res            .RRES
     raw_drive               .RVAL
     dial_speed              .RVEL
     s_speed                 .S
     s_back_speed            .SBAK
     s_base_speed            .SBAS
     s_max_speed             .SMAX
     set                     .SET
     stop_go                 .SPMG
     s_revolutions           .SREV
     stop                    .STOP
     t_direction             .TDIR
     tweak_forward           .TWF
     tweak_reverse           .TWR
     tweak_val               .TWV
     use_encoder             .UEIP
     u_revolutions           .UREV
     use_rdbl                .URIP
     drive                   .VAL   
     base_speed              .VBAS
     slew_speed              .VELO
     version                 .VERS
     max_speed               .VMAX
     use_home                .ATHM
     deriv_gain              .DCOF
     use_torque              .CNEN
     device_type             .DTYP
     record_type             .RTYP
     status                  .STAT
    ==================== ==============================



methods for  `epics.Motor`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: get_field(attr[, as_string=False])

   sets a field attribute for the motor.

   :param attr: attribute name 
   :type attr: string (from table above)
   :param as_string:  whether to return string value.
   :type as_string: ``True`` or ``False``

Note that :meth:`get_field` can return the string value, while fetching the
attribute cannot do so::

    >>> m = epics.Motor('XXX:m1')
    >>> print m.device_type
    0
    >>> print m.get_field('device_type', as_string=True)
    'asynMotor'

.. method:: put_field(attr, value[, wait=False[, timeout=30]])

   sets a field attribute for the motor.

   :param attr: attribute name 
   :type attr: string (from table above)
   :param value: value for attribute
   :param wait:  whether to wait for completion.
   :type wait: ``True`` or ``False``
   :param timeout:  time (in seconds) to wait befoe giving up trying to connect.
   :type timeout: float


.. method:: check_limits()

   checks whether the current motor position is causing a motor limit
   violation, and raises a MotorLimitException if it is.
   
   returns ``None`` if there is no limit violation.

.. method:: within_limits(value[, limits='user'])

   checks whether a target value **would be** a limit violation.
 
   :param value: target valu
   :param limits: one of 'user', 'dial', or 'raw' for which limits to consider
   :type limits: string
   :rtype:    ``True``/``False``


.. method:: move(val=None[, relative=None[, wait=False[, timeout=300.0[, dial=False[, raw=False[, ignore_limits=False]]]]]])

   moves motor drive to position

   :param val:    value to move to (float) [Must be provided]
   :param relative:   move relative to current position    (T/F) [F]
   :param wait:           whether to wait for move to complete (T/F) [F]
   :param dial:           use dial coordinates                 (T/F) [F]
   :param raw:            use raw coordinates                  (T/F) [F]
   :param ignore_limits:  try move without regard to limits    (T/F) [F]
   :param timeout:        max time for move to complete (in seconds) [300]
   :rtype:  see below


   Return codes:

          None : unable to move, invalid value given
          -1   : target value outside limits -- no move attempted
          -2   : with wait=True, wait time exceeded timeout
          0    : move executed successfully
	  
          will raise an exception if a motor limit is met.
          
.. method:: tweak(dir='forward'[, wait=False[, timeout=300.]])

   move the motor by the current *tweak value*

   :param dir: direction of motion 
   :type dir: string: 'forward' (default) or 'reverse'
   :param wait: whether to wait for completion
   :type wait:  ``True`` or ``False``
   :param timeout:  max time for move to complete (in seconds) [default=300]    
   :type timeout: float
  

.. method:: get_position(readback=False[, dial=False[, raw=False]])

   Returns the motor position in user, dial or raw coordinates.
      
   :param readback:   whether to return the readback position in the
            desired coordinate system.  The default is to return the
            drive position of the motor.
   :param dial: whether to return the position in dial coordinates.
            The default is user coordinates.
   :param raw: whether to return the raw position.
            The default is user coordinates.

   The "raw" and "dial" keywords are mutually exclusive.
   The "readback" keyword can be used in user, dial or raw coordinates.
            

.. method:: set_position(position[ dial=False[, raw=False]])

   set (that is, redefine) the current position to supplied value.

   :param position:   The new motor position
   :param dial: whether to set in dial coordinates. The default is user coordinates.
   :param raw:  whether to set in raw coordinates. The default is user  coordinates.
            
    The 'raw' and 'dial' keywords are mutually exclusive.
         
.. method:: get_pv(attr)
   
   returns the `PV` for the corresponding attribute.

.. method:: set_callback(attr='drive'[, callback=None[, kw=None]])

.. method:: clear_callback(attr='drive')

.. method:: show_info()




Other Device Examples
===========================

Device without a prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a simple device without a prefix, containing arbitrary PVs::

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



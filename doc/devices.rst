================================
Devices: collections of PVs
================================

Overview
===========

.. module:: device
   :synopsis: collections of related PVs

The :mod:`device` module provides a simple interface to a collection of
PVs.  Here an epics :class:`device.Device` is an object holding a set of
PVs, all sharing a prefix, but having many *attributes*.  Many PVs will
have names made up of *prefix+attribute*, with a common prefix for several
related PVs.  This almost describes an Epics Record, but as it is concerned
only with PV names, the mapping to an Epics Record is not exact.  On the
other hand, the concept of a *device* is more flexible than a predefined
Epics Record as it can actually hold PVs from several different records.::

    motor1 = epics.Device('XXX:motor1.', attrs=('VAL', 'RBV', 'DESC', 'RVAL',
                                               'LVIO', 'HLS', 'LLS'))
    motor1.put('VAL', 1)
    print 'Motor %s = %f' % ( motor1.get('DESC'), motor1.get('RBV'))

    motor1.VAL = 0
    print 'Motor %s = %f' % ( motor1.DESC, motor1.RBV )

While useful on its own like this, the real point of a *device* is as a
base class, to be inherited and extended.  In fact, there is a more
sophisticated   Motor device described below at :ref:`device-motor-label`

.. class:: Device(prefix=None[, delim=''[, attrs=None]])

The attribute PVs are built as needed and held in an internal buffer
:data:`self._pvs`.  This class is kept intentionally simple so that it may
be subclassed.

To pre-load attribute names on initialization, provide a list or tuple of
attributes with the `attr` option.

Note that *prefix* is actually optional.  When left off, this class can be
used as an arbitrary container of PVs, or to turn any subclass into an
epics Device.

In general, PV names will be mapped as prefix+delim+attr.  See
:meth:`add_pv` for details of how to override this.

.. method:: PV(attr[, connect=True[, **kw]]])

   returns the `PV` object for a device attribute.  The connect argument
   and any other keyword arguments are passed to :meth:`epics.PV`.

.. method::  put(attr, value[, wait=False[, timeout=10.0]])

   put an attribute value, optionally wait for completion or up to a
   supplied timeout value

.. method::  get(attr[, as_string=False])

   get an attribute value, option as_string returns a string
   representation

.. method:: add_callback(attr, callback)

   add a callback function to an attribute PV, so that the callback
   function will be run when the at tribute's value changes

.. method:: add_pv(pvname[, attr=None,[ **kw]])

   adds an explicitly names :meth:`epics.PV` to the device even though it
   may violate the normal naming rules (in which `attr` is mapped to
   `epics.PV(prefix+delim+attr)`.   That is, one can say::

    import epics
    m1 = epics.Device('XXX:m1', delim='.')
    m1.add_pv('XXX:m2.VAL', attr='other')
    print m1.VAL     # print value of XXX:m1.VAL
    print m1.other   # prints value of XXX:m2.VAL


.. method:: save_state()

   return a dictionary of all current values -- the ''current state''.


.. method:: restore_state(state)

   restores a saved state, as saved with :meth:`save_state`

.. method:: write_state(fname[, state=None])

   write a saved state to a file.   If no state is provide, the current state is written.

.. method:: read_state(fname[, restore=False])

   reads a state from a file, as written with :meth:`write_state`, and returns it.
   If ''restore'' is ``True``, the read state will be restored.

.. data:: _pvs

   a dictionary of PVs making up the device.


.. _device-motor-label:

Epics Motor Device
===========================

.. module:: motor

The Epics Motor record has over 100 fields associated with it.  Of course,
it is often preferable to think of 1 Motor with many attributes than 100
or so separate PVs.  Many of the fields of the Motor record are
interrelated and influence other settings, including limits on the range of
motion which need to be respected, and which may send notifications when
they are violated.  Thus, there is a fair amount of functionality for a
Motor.  Typically, the user just wants to move the motor by setting its
drive position, but a fully enabled Motor should allow the use to change
and read many of the Motor parameters.

The  :class:`Motor` class helps the user create and use Epics motors.
A simple example use would be::

    import epics
    m1 = epics.Motor('XXX:m1')

    print 'Motor:  ', m1.DESC , ' Currently at ', m1.RBV

    m1.tweak_val = 0.10
    m1.move(0.0, dial=True, wait=True)

    for i in range(10):
        m1.tweak(direction='forward', wait=True)
	time.sleep(1.0)
        print 'Motor:  ', m1.DESC , ' Currently at ', m1.RBV

Which will step the motor through a set of positions.    You'll notice a
few features for Motor:

 1.  Motors can use English-name aliases for attributes for fields of the
 motor record.  Thus 'VAL' can be spelled 'drive' and 'DESC' can be
 'description'.   The :ref:`Table of Motor Attributes <motorattr_table>`
 give the list of names that can be used.

 2.  The methods for setting positions can use the User, Dial, or Step
 coordinate system, and can wait for completion.


The :class:`epics.Motor` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. class:: Motor(pvname[, timeout=30.])

   create a Motor object for a named Epics Process Variable.

   :param pvname: prefix name (no '.VAL' needed!) of Epics Process Variable  for a Motor
   :type pvname: string
   :param timeout:  time (in seconds) to wait before giving up trying to connect.
   :type timeout: float

Once created, a Motor should be ready to use.

      >>> from epics import Motor
      >>> m = Motor('XX:m1')
      >>> print m.drive, m.description, m.slew_speed
      1.030 Fine X 5.0
      >>> print m.get('device_type', as_string=True)
      'asynMotor'


A Motor has very many fields.  Only a few of them are created on
initialization -- the rest are retrieved as needed.  The motor fields can
be retrieved either with an attribute or with the :meth:`get` method.
A full list of Motor attributes and their aliases for the motor
record is given in :ref:`Table of Motor Attributes <motorattr_table>`.

.. _motorattr_table:

   Table of Aliases for attributes for the epics :class:`Motor` class, and the
   corresponding attribute name of the Motor Record field.


+--------------------+--------------------------+---+--------------------+--------------------------+
|   **alias**        |  *Motor Record field*    |   |    **alias**       | *Motor Record field*     |
+====================+==========================+===+====================+==========================+
| disabled           |     _able.VAL            |   |   moving           |       MOVN               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| acceleration       |      ACCL                |   |   resolution       |       MRES               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| back_accel         |      BACC                |   |   motor_status     |       MSTA               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| backlash           |      BDST                |   |   offset           |       OFF                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| back_speed         |      BVEL                |   |   output_mode      |       OMSL               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| card               |      CARD                |   |   output           |       OUT                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| dial_high_limit    |      DHLM                |   |   prop_gain        |       PCOF               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| direction          |      DIR                 |   |   precision        |       PREC               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| dial_low_limit     |      DLLM                |   |   readback         |       RBV                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| settle_time        |      DLY                 |   |   retry_max        |       RTRY               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| done_moving        |      DMOV                |   |   retry_count      |       RCNT               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| dial_readback      |      DRBV                |   |   retry_deadband   |       RDBD               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| description        |      DESC                |   |   dial_difference  |       RDIF               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| dial_drive         |      DVAL                |   |   raw_encoder_pos  |       REP                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| units              |      EGU                 |   |   raw_high_limit   |       RHLS               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| encoder_step       |      ERES                |   |   raw_low_limit    |       RLLS               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| freeze_offset      |      FOFF                |   |   relative_value   |       RLV                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| move_fraction      |      FRAC                |   |   raw_motor_pos    |       RMP                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| hi_severity        |      HHSV                |   |   raw_readback     |       RRBV               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| hi_alarm           |      HIGH                |   |   readback_res     |       RRES               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| hihi_alarm         |      HIHI                |   |   raw_drive        |       RVAL               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| high_limit         |      HLM                 |   |   dial_speed       |       RVEL               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| high_limit_set     |      HLS                 |   |   s_speed          |       S                  |
+--------------------+--------------------------+---+--------------------+--------------------------+
| hw_limit           |      HLSV                |   |   s_back_speed     |       SBAK               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| home_forward       |      HOMF                |   |   s_base_speed     |       SBAS               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| home_reverse       |      HOMR                |   |   s_max_speed      |       SMAX               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| high_op_range      |      HOPR                |   |   set              |       SET                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| high_severity      |      HSV                 |   |   stop_go          |       SPMG               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| integral_gain      |      ICOF                |   |   s_revolutions    |       SREV               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| jog_accel          |      JAR                 |   |   stop             |       STOP               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| jog_forward        |      JOGF                |   |   t_direction      |       TDIR               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| jog_reverse        |      JOGR                |   |   tweak_forward    |       TWF                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| jog_speed          |      JVEL                |   |   tweak_reverse    |       TWR                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| last_dial_val      |      LDVL                |   |   tweak_val        |       TWV                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| low_limit          |      LLM                 |   |   use_encoder      |       UEIP               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| low_limit_set      |      LLS                 |   |   u_revolutions    |       UREV               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| lo_severity        |      LLSV                |   |   use_rdbl         |       URIP               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| lolo_alarm         |      LOLO                |   |   drive            |       VAL                |
+--------------------+--------------------------+---+--------------------+--------------------------+
| low_op_range       |      LOPR                |   |   base_speed       |       VBAS               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| low_alarm          |      LOW                 |   |   slew_speed       |       VELO               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| last_rel_val       |      LRLV                |   |   version          |       VERS               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| last_dial_drive    |      LRVL                |   |   max_speed        |       VMAX               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| last_SPMG          |      LSPG                |   |   use_home         |       ATHM               |
+--------------------+--------------------------+---+--------------------+--------------------------+
| low_severity       |      LSV                 |   |   deriv_gain       |       DCOF               |
+--------------------+--------------------------+---+--------------------+--------------------------+


methods for :class:`epics.Motor`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. method:: get(attr[, as_string=False])

   sets a field attribute for the motor.

   :param attr: attribute name
   :type attr: string (from table above)
   :param as_string:  whether to return string value.
   :type as_string: ``True``/ ``False``

Note that :meth:`get` can return the string value, while fetching the
attribute cannot do so::

    >>> m = epics.Motor('XXX:m1')
    >>> print m.device_type
    0
    >>> print m.get('device_type', as_string=True)
    'asynMotor'

.. method:: put(attr, value[, wait=False[, timeout=30]])

   sets a field attribute for the motor.

   :param attr: attribute name
   :type attr: string (from table above)
   :param value: value for attribute
   :param wait:  whether to wait for completion.
   :type wait: ``True``/``False``
   :param timeout:  time (in seconds) to wait before giving up trying to connect.
   :type timeout: float


.. method:: check_limits()

   checks whether the current motor position is causing a motor limit
   violation, and raises a MotorLimitException if it is.

   returns ``None`` if there is no limit violation.

.. method:: within_limits(value[, limits='user'])

   checks whether a target value **would be** a limit violation.

   :param value: target value
   :param limits: one of 'user', 'dial', or 'raw' for which limits to consider
   :type limits: string
   :rtype:    ``True``/``False``


.. method:: move(val=None[, relative=None[, wait=False[, timeout=300.0[, dial=False[, raw=False[, ignore_limits=False, [confirm_move=False]]]]]]])

   moves motor to specified drive position.

   :param val:           value to move to (float) [Must be provided]
   :param relative:      move relative to current position    (T/F) [F]
   :param wait:          whether to wait for move to complete (T/F) [F]
   :param timeout:       max time for move to complete (in seconds) [300]
   :param dial:          use dial coordinates                 (T/F) [F]
   :param raw:           use raw coordinates                  (T/F) [F]
   :param ignore_limits: try move without regard to limits    (T/F) [F]
   :param confirm_move:  try to confirm that move has begun (when wait=False) (T/F) [F]
   :rtype:  integer

   Returns an integer value, according the table below.  Note that a return
   value of 0 with `wait=False` does not really guarantee a successful
   move, just that a move request was issued.  If you're interested in
   checking that a requested move really did start without waiting for the
   move to complete, you may want to use the `confirm_move=True` option.


.. _motor_move_return_vals_table:

   Table of return values from :func:`move`.

   +---------------+----------------------------------------------------------------+
   | return value  |  meaning                                                       |
   +===============+================================================================+
   |      -13      | invalid value (cannot convert to float).  Move not attempted.  |
   +---------------+----------------------------------------------------------------+
   |      -12      | target value outside soft limits.         Move not attempted.  |
   +---------------+----------------------------------------------------------------+
   |      -11      | drive PV is not connected:                Move not attempted.  |
   +---------------+----------------------------------------------------------------+
   |       -8      | move started, but timed-out.                                   |
   +---------------+----------------------------------------------------------------+
   |       -7      | move started, timed-out, but appears done.                     |
   +---------------+----------------------------------------------------------------+
   |       -5      | move started, unexpected return value from :func:`put`         |
   +---------------+----------------------------------------------------------------+
   |       -4      | move-with-wait finished, soft limit violation seen.            |
   +---------------+----------------------------------------------------------------+
   |       -3      | move-with-wait finished, hard limit violation seen.            |
   +---------------+----------------------------------------------------------------+
   |        0      | move-with-wait finish OK.                                      |
   +---------------+----------------------------------------------------------------+
   |        0      | move-without-wait executed, not cpmfirmed.                     |
   +---------------+----------------------------------------------------------------+
   |        1      | move-without-wait executed, move confirmed.                    |
   +---------------+----------------------------------------------------------------+
   |        3      | move-without-wait finished, hard limit violation seen.         |
   +---------------+----------------------------------------------------------------+
   |        4      | move-without-wait finished, soft limit violation seen.         |
   +---------------+----------------------------------------------------------------+


.. method:: tweak(direction='forward'[, wait=False[, timeout=300.]])

   move the motor by the current *tweak value*

   :param direction: direction of motion
   :type direction: string: 'forward' (default) or 'reverse'
   :param wait: whether to wait for completion
   :type wait:  ``True``/``False``
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

   sets a callback on the `PV` for a particular attribute.

.. method:: clear_callback(attr='drive')

   clears a callback on the `PV` for a particular attribute.

.. method:: show_info()

   prints out a table of attributes and their current values.



Other Device Examples
===========================

An epics Device provides a general way to group together a set of PVs.  The
examples below show how to build on this generality, and may inspire you to
build your own device classes.

A basic Device without a prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here, we define a very simple device that does not even define a prefix.
This is not much more than a collection of PVs.  Since there is no prefix
given, all PVs in the device must be *fully qualified*.  Note that there is
no requirement to share a common prefix in such a collection of PVs::

    from epics import Device
    dev = Device()
    p1 = dev.PV('13IDC:m1.VAL')
    p2 = dev.PV('13IDC:m2.VAL')
    dev.put('13IDC:m1.VAL', 2.8)
    dev.put('13IDC:m2.VAL', 3.0)
    print dev.PV('13IDC:m3.DIR').get(as_string=True)

Note that this device cannot use the attributes based on field names.

This may not look very interesting -- why not just use a bunch of PVs?  If
ou consider `Device` to be a starting point for building more complicated
objects by subclassing `Device` and adding specialized methods, then it can
start to get interesting.


Epics ai record as Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a slightly more useful and typical example, the pyepics distribution
includes a Device for an Epics ai (analog input record).  The full
implementation of this device is:


.. literalinclude:: ../epics/devices/ai.py

The code simply pre-defines the fields that are the *suffixes* of an Epics ai
input record, and subclasses :class:`Device` with these fields to create the
corresponding PVs.  For most record suffixes, these will be available as
attributes of the Device object.  For example, the :class:`ai` class above can
be used simply and cleanly as::

    from epics.devices import ai
    This_ai = ai('XXX.PRES')
    print 'Value: ', This_ai.VAL
    print 'Units: ', This_ai.EGU

Of course, you can also use the :meth:`get`, :meth:`put` methods above for a
basic :class:`Device`::

    This_ai.put('DESC', 'My Pump')


Several of the other standard Epics records can easily be exposed as Devices in
this way, and the pyepics distribution includes such simple wrappings for the
Epics ao, bi, and bo records, as well as several more complex records from
synApps.

Epics Scaler Record as Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a slightly more complicated example: an incomplete, but very useful mapping
of the Scaler Record from synApps, including methods for changing modes, and
reading and writing data.

.. literalinclude:: ../epics/devices/scaler.py

Note that we can then create a :class:`scaler` object from its base PV
prefix, and use methods like :meth:`Count` and :meth:`Read` without
directly invoking epics calls::

   s1 = Scaler('XXX:scaler1')
   s1.setCalc(2, '(B-2000*A/10000000.)')
   s1.enableCalcs()
   s1.OneShotMode()
   s1.Count(t=5.0, wait=True)
   print 'Names:       ', s1.getNames()
   print 'Raw  values: ', s1.Read(use_calc=False)
   print 'Calc values: ', s1.Read(use_calc=True)


Other Devices included in PyEpics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Several other Epics Records have been exposed as Devices, and included in
PyEpics distribution.  These vary some in how complete and feature-rich they
are, and are definitely skewed toward data collection at synchrotron beamlines.
A table of current Devices are listed in the :ref:`Table of Included Epics
Devices <devices_table>` table below.  For further details, consult the source
code for these modules.

.. _devices_table:

   Table of Epics Devices Included in the PyEpics distribtion.  For those
   described as "pretty basic", there are generally only PV suffixes to
   attributes mapped.  Many of the others include one or more methods for
   specific use of that Device.


+----------------+-----------------+------------------------------------------------+
|   **module**   |  **class**      |    description                                 |
+================+=================+================================================+
| ad_base        |  AD_Camera      | areaDetector Camera, pretty basic              |
+----------------+-----------------+------------------------------------------------+
| ad_fileplugin  | AD_FilePlugin   | areaDetector File Plugin, many methods         |
+----------------+-----------------+------------------------------------------------+
| ad_image       | AD_ImagePlugin  | areaDetector Image, with ArrayData attribute   |
+----------------+-----------------+------------------------------------------------+
| ad_overlay     | AD_OverlayPlugin| areaDetector Overlay, pretty basic             |
+----------------+-----------------+------------------------------------------------+
| ad_perkinelmer | AD_PerkinElmer  | PerkinElmer(xrd1600) detector, several methods |
+----------------+-----------------+------------------------------------------------+
| ai             | ai              | analog input, pretty basic (as above)          |
+----------------+-----------------+------------------------------------------------+
| ao             | ao              | analog output, pretty basic                    |
+----------------+-----------------+------------------------------------------------+
| bi             | bi              | binary input, pretty basic                     |
+----------------+-----------------+------------------------------------------------+
| bo             | bo              | binary output, pretty basic                    |
+----------------+-----------------+------------------------------------------------+
| mca            | MCA             | epics DXP record, pretty basic                 |
+----------------+-----------------+------------------------------------------------+
| mca            | DXP             | epics MCA record, get_rois()/get_calib()       |
+----------------+-----------------+------------------------------------------------+
| mca            | MultiXMAP       | Multiple XIA XMaps, several methods            |
+----------------+-----------------+------------------------------------------------+
| scaler         | Scaler          | epics Scaler record, many methods              |
+----------------+-----------------+------------------------------------------------+
| scan           | Scan            | epics SScan record, some methods               |
+----------------+-----------------+------------------------------------------------+
| srs570         | SRS570          | SRS570 Amplifier                               |
+----------------+-----------------+------------------------------------------------+
| struck         | Struck          | SIS Multichannel Scaler, many methods          |
+----------------+-----------------+------------------------------------------------+
| transform      | Transform       | epics userTransform record                     |
+----------------+-----------------+------------------------------------------------+

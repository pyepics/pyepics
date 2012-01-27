================================================
Alarms: respond when a PV goes out of range
================================================

Overview
===========

.. module:: alarm
   :synopsis: respond when a PV goes out of range by running user-supplied code

The :mod:`alarm` module provides an Alarm object to specify an alarm
condition and what to do when that condition is met.

.. class:: Alarm(pvname[, comparison=None[, trip_point=None[, callback=None[, alert_delay=10]]]])

creates an alarm object.

   :param pvname:     name of Epics PV (string)
   :param comparison:  operation used to compare PV value to trip_point.
   :type  comparison:  string or callable.  Built in comparisons are listed in :ref:`Table of Alarm Operators<alarmops_table>`.
   :param trip_point: value that will trigger the alarm

   :param callback:   user-defined callback function to be run when the PVs value meets the alarm condition
   :type callback: callable or None
   :param alert_delay:  time (in seconds) to wait before executing another alarm callback.

The alarm works by checking the value of the PV each time it changes.  If
the new value is outside the acceptable range (violates the trip point),
then the user-supplied callback function is run.  This callback could be
set do send a message or to take some other course of action.

The comparison supplied can either be a string as listed in :ref:`Table of
Alarm Operators<alarmops_table>` or a custom callable function which takes
the two values (PV.value, trip_point) and returns ``True`` or ``False``
based on those values.

.. _alarmops_table:

   Table of built-in Operators for Alarms:

    =============== ==============================
     *operator*       Python operator
    =============== ==============================
      'eq', '=='        __eq__
      'ne', '!='        __ne__
      'le', '<='        __le__
      'lt', '<'         __lt__
      'ge', '>='        __ge__
      'gt', '>'         __gt__
    =============== ==============================


The :attr:`alert_delay` prevents the alarm callback from being called too
many times. For PVs with floating point values, the value may
fluctuate around the trip_point for a while.  If the value violates the
trip_point, then momentarily goes back to an acceptable value, and back
again to a violating value, it may not be desirable to send repeated,
identical messages.   To prevent this situation, the alarm callback will be
called when the alarm condition is met **and** the callback was not called
within the time specified by  :attr:`alert_delay`.


Alarm Example
===============

An epics Alarm is very easy to use.  Here is an alarm set to print a
message when a PV's value reaches a certain value::

    from epics import Alarm, poll

    def alertMe(pvname=None, char_value=None, **kw):
        print "Soup's on!   %s = %s" % (pvname, char_value)

    my_alarm = Alarm(pvname = 'WaterTemperature.VAL',
                     comparison = '>',
                     callback = alertMe,
                     trip_point = 100.0,
                     alert_delay = 600)
    while True:
        poll()





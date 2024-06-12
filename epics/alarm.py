 #!/usr/bin/env python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License
"""
alarm module -- Alarm class
"""
import sys
import time
import operator
from . import pv

class Alarm:
    """ alarm class for a PV:
    run a user-supplied callback when a PV's value goes out of range

    quick synopsis:
       The supplied callback will be run when a comparison of the PV's
       value and a trip point is True.  An optional alert delay can be
       set to limit how frequently the callback is run

    arguments:
       pvname         name of PV for which to set alarm
       trip_point     value of trip point
       comparison     a string for the comparison operation: one of
                          'eq', 'ne', 'le', 'lt', 'ge', 'gt'
                          '==', '!=', '<=', '<' , '>=', '>'
       callback       function to run when comparison(value,trip_point) is True
       alert_delay    time (in seconds) to stay quiet after executing a callback.
                      this is a minimum time, as it is checked only when a PVs
                      value actually changes.  See note below.

    example:
       >>> from epics import alarm, poll
       >>> def alarmHandler(pvname=None, value=None, **kw):
       >>>     print 'Alarm!! ', pvname, value
       >>> alarm(pvname = 'XX.VAL',
       >>>       comparison='gt',
       >>>       callback = alarmHandler,
       >>>       trip_point=2.0,
       >>>       alert_delay=600)
       >>> while True:
       >>>     poll()

    when 'XX.VAL' exceeds (is 'gt') 2.0, the alarmHandler will be called.

    notes:
      alarm_delay:  The alarm delay avoids over-notification by specifying a

                    time period to NOT send messages after a message has been
                    sent, even if a value is changing and out-of-range.  Since
                    Epics callback are used to process events, the alarm state
                    will only be checked when a PV's value changes.

      callback function:  the user-supplied callback function should be prepared
                    for a large number of keyword arguments: use **kw!!!
                    For further explanation, see notes in pv.py.

                    These keyword arguments will always be included:

                    pvname      name of PV
                    value       current value of PV
                    char_value  text string for PV
                    trip_point  will hold the trip point used to define 'out of range'
                    comparison  string
                    self.user_callback(pvname=pvname, value=value,
                                   char_value=char_value,
                                   trip_point=self.trip_point,
                                   comparison=self.cmp.__name__, **kw)

    """
    ops = {'eq': operator.__eq__,
           '==': operator.__eq__,
           'ne': operator.__ne__,
           '!=': operator.__ne__,
           'le': operator.__le__,
           '<=': operator.__le__,
           'lt': operator.__lt__,
           '<' : operator.__lt__,
           'ge': operator.__ge__,
           '>=': operator.__ge__,
           'gt': operator.__gt__,
           '>' : operator.__gt__ }

    def __init__(self, pvname, comparison=None, trip_point=None,
                 callback=None, alert_delay=10):

        if isinstance(pvname, pv.PV):
            self.pv = pvname
        elif isinstance(pvname, str):
            self.pv = pv.get_pv(pvname)
            self.pv.connect()

        if self.pv is None or comparison is None or trip_point is None:
            msg = 'alarm requires valid PV, comparison, and trip_point'
            raise UserWarning(msg)


        self.trip_point = trip_point

        self.last_alert  = 0
        self.alert_delay = alert_delay
        self.user_callback = callback

        self.cmp = None
        self.comp_name = 'Not Defined'
        if callable(comparison):
            self.comp_name  = comparison.__name__
            self.cmp = comparison
        elif comparison is not None:
            self.cmp   = self.ops.get(comparison.replace('_', ''), None)
            if self.cmp is not None:
                self.comp_name  = comparison

        self.alarm_state = False
        self.pv.add_callback(self.check_alarm)
        self.check_alarm()

    def __repr__(self):
        parts = [f"pvname='{self.pv.pvname}'",
                 f"comp='{self.comp_name}'",
                 f"'trip_point={self.trip_point}"]
        return f"<Alarm {','.join(parts)}>"

    def reset(self):
        "resets the alarm state"
        self.last_alert = 0
        self.alarm_state = False

    def check_alarm(self, pvname=None, value=None, char_value=None, **kw):
        """checks alarm status, act if needed.
        """
        if (pvname is None or value is None or
            self.cmp is None or self.trip_point is None): return

        val = value
        if char_value is None:
            char_value = value
        old_alarm_state  = self.alarm_state
        self.alarm_state =  self.cmp(val, self.trip_point)

        now = time.time()

        if (self.alarm_state and not old_alarm_state and
            ((now - self.last_alert) > self.alert_delay)) :
            self.last_alert = now
            if callable(self.user_callback):
                self.user_callback(pvname=pvname, value=value,
                                   char_value=char_value,
                                   trip_point=self.trip_point,
                                   comparison=self.comp_name, **kw)

            else:
                sys.stdout.write('Alarm: %s=%s (%s)\n' % (pvname, char_value,
                                                          time.ctime()))

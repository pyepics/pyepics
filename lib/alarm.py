#!/usr/bin/env python
import ca
import pv
import time
import operator
   
class Alarm(object):
    """ alarm class for a PV:
    run a user-supplied callback when a PV's value goes out of an acceptable range

    quick synopsis:
       The supplied _callback_ will be run when a _comparison_ of the pv's value
       and a _trip point_ is True.  An optional _alert delay_ can be set to limit
       how frequently the callback is run

    arguments:
       pvname             name of PV for which to set alarm
       trip_point         value of trip point
       comparison         a string for the comparison operation: one of
                              'eq', 'ne', 'le', 'lt', 'ge', 'gt'
                              '==', '!=', '<=', '<' , '>=', '>'
       callback           function to run when the comparison(value,trip_point) is True
       alert_delay        time (in seconds) to stay quiet after executing a callback.
                          this is a _minimum_ time, as it is checked only when a PVs value
                          actually changes.  See note below.
       notify_all_alarms  whether to call alarm callback even for "Alarm to Alarm"
                          transitions: where the pv was in an alarm state and changed value
                          to another alarm state.
                          This is normally False, so that the alarm callback is called only
                          when going from "No Alarm" to "Alarm" status.

       
    example:
       >>> from epics import alarm, poll
       >>> def alarmHandler(pv=None,**kw):
       >>>     print 'Alarm!! ', pv.pvname, pv.value
       >>> alarm(pvname = 'XX.VAL',
       >>>       comparison='gt',
       >>>       callback = alarmHandler,
       >>>       trip_point=2.0,
       >>>       alert_delay=600)
       >>> while True:
       >>>     pend_event()

    when 'XX.VAL' exceeds (is 'gt') 2.0, the alarmHandler will be called.
   
    
    notes:
      alarm_delay:  The alarm delay avoids annoying over-notification by specifying a
                    time to NOT send messages, even when a PV value is changing and
                    out-of-range.  Since Epics callback are used to process events,
                    the alarm state will only be checked when a PV's value changes.
      notify_all_alarms  This sets whether to notify on "Alarm to Alarm" transitions
                    this is normally false, so that notifications only happen on
                    transitions from No Alarm to Alarm.
                    
                    With "notify_all_alarms" True, the user callback is run when:
                       The PV value has changed.
                       The PV value is 'out-of-range' [ comparison(value,trip_point) is True]
                       It has been at least alarm_delay seconds since the callback was run.

                    With "notify_all_alarms" False (the default), the user callback is run when:
                       The PV value has changed.
                       The PV value was 'in-range' [ comparison(value,trip_point) is False]
                       The PV value is 'out-of-range' [ comparison(value,trip_point) is True]
                       It has been at least alarm_delay seconds since the callback was run.                    


      callback function:  the user-supplied callback function should have the following
                    keyword argument (using **kw is always recommended!):

                    pv          will hold the EpicsCA pv object for the pv
                    comparison  will hold the comparison used to define 'out of range'
                    trip_point  will hold the trip point used to define 'out of range'
    
    """
    ops= {'eq': operator.__eq__,
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
    
    def __init__(self, pvname, trip_point=None, comparison=None,
                 callback=None,  alert_delay=10, **kw):

        if isinstance(pvname, pv.PV):
            self.pv = pvname
        elif isinstance(pvname, (str,unicode)):
            self.pv = pv.PV(pvname)
            self.pv.connect()
        
        if self.pv is None: return

        self.trip_point  = trip_point
        self.last_alert  = 0
        self.alert_delay = alert_delay

        self.cmp   = self.ops.get(comparison.replace('_',''),None)
        self.alarm_state = False
        self.pv.add_callback(self.check_alarm)
        self.check_alarm()
        
    def check_alarm(self,pvname=None,value=None, char_value=None, **kw):
        if (pvname is None or value is None or
            self.cmp is None or self.trip_point is None):
            return

        val = value
        old_alarm_state  = self.alarm_state
        self.alarm_state =  self.cmp(val,self.trip_point)

        now = time.time()
        notify = self.alarm_state and ((now - self.last_alert) > self.alert_delay) 

        if notify:
            self.last_alert = now
            if char_value is None: char_value = value
            print 'Alarm: ', pvname, char_value, time.ctime()            
            # self.callback(pv=self.pv, comparison=self.cmp, trip_point=self.trip_point)
          


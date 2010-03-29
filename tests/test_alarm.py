import EpicsCA

import time

def alarmHandler(pv=None,**kw):
    if pv is not None:
        print 'Alarm!! ', pv.pvname, pv.value, time.ctime()

EpicsCA.alarm(pvname = '13IDC:m13.VAL',   comparison='gt',
      callback = alarmHandler,
      trip_point=-14.0,
      alert_delay=10)

while True: EpicsCA.pend_event(0.01)
    
